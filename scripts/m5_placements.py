#!/usr/bin/env python
"""Amendment B6 item 2: the reported lever cells re-scored on every eligible placement day.

Cells: every row of the cross-account table (round-robin 10/100/1000 rate-capped; heterogeneous
100 and 1000 at stagger 0/6/24/72 h) and every clearing cell of the wider search, each placed
on every day of the absolute timeline on which its schedule ends before the timeline does, one
seeded re-scheduling per day. Per placement: flagged fraction by D10, D11, D1, D2, D3, D9; joint
max; whether any unit is flagged; whether the joint max exceeds 0.10. Summaries with and
without the five original placement days. Also the price table's cells re-scheduled 50 times.

The same-day density is computed by a restricted routine (only the campaign's days) that is
checked against the registered routine on the first placements of the first cell.

Writes results/aggregates/m5/<out-label>/{placements.json,table.md}.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from collections import defaultdict
from pathlib import Path

import numpy as np

from dev_harness.detectors import stats as D
from dev_harness.detectors.analysis import timeline_stats
from dev_harness.detectors.coordination import (
    Standardiser,
    birth_burst,
    births,
    features,
    identity_days,
    nearest_neighbour_radius,
    same_day_density,
    score_births,
    score_campaign,
)
from dev_harness.levers import price, shape_rate, split_heterogeneous, split_identities
from dev_harness.paths import host_repo
from dev_harness.writer import calibration_records, read_records

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m4_coordination import timeline_abs  # noqa: E402

NS = 1_000_000_000
G: dict = {}  # read-only state, sent to spawned workers by the pool initialiser


def _init(state: dict) -> None:
    G.update(state)


def restricted_density(zc: np.ndarray, dc: np.ndarray) -> np.ndarray:
    """D10 for campaign rows placed among the benign rows of the same days; identical to
    score_campaign restricted to the days the campaign touches."""
    zb, by_day, r = G["zb"], G["by_day"], G["r"]
    out = np.zeros(len(zc), dtype=int)
    for d in np.unique(dc):
        mc = dc == d
        c = zc[mc]
        idx = by_day.get(int(d))
        a = np.concatenate([zb[idx], c]) if idx is not None else c
        d2 = np.maximum(
            np.sum(c * c, axis=1)[:, None] + np.sum(a * a, axis=1)[None, :] - 2.0 * (c @ a.T), 0.0
        )
        within = d2 <= r * r
        nb = len(a) - len(c)
        # exclude each campaign row's own entry (it sits at column nb + its position)
        own = np.arange(len(c))
        within[own, nb + own] = False
        out[mc] = within.sum(axis=1)
    return out


def build(cell: dict, seed: int) -> list:
    camp = G["camp"]
    if cell["kind"] == "roundrobin":
        recs = split_identities(camp, cell["n"], seed)
        return shape_rate(recs, G["cap"], seed)
    return split_heterogeneous(
        camp,
        cell["n"],
        seed,
        G["benign_counts"],
        G["benign_sess"],
        cell["stagger_h"] * 3600.0,
        G["interval"],
        count_cap=cell.get("count_cap", 0),
        session_mult=cell.get("session_mult", 1.0),
    )


def place(recs: list, day: int) -> list:
    base = min(x.t_sched_ns for x in recs)
    t0 = day * 86400 * NS
    return [x.model_copy(update={"t_sched_ns": x.t_sched_ns - base + t0}) for x in recs]


def score(recs: list) -> dict:
    rows_c = identity_days(recs)
    zc = G["std"](np.stack([features(x) for x in rows_c]))
    dc = np.array([x["day"] for x in rows_c])
    dens = restricted_density(zc, dc)
    fl = {"D10": float(np.mean([D.fires(float(v), G["cal10"]) for v in dens]))}
    v11 = score_births(G["bb"], np.array(list(births(recs).values())), 600.0)
    fl["D11"] = float(np.mean([D.fires(float(v), G["cal11"]) for v in v11]))
    cv: dict[str, list[float]] = defaultdict(list)
    for st in timeline_stats(recs):
        cv[st.detector_id].append(st.value)
    for det, vals in cv.items():
        sc = [v for v in vals if not math.isnan(v)]
        if sc:
            fl[det] = float(np.mean([D.fires(v, G["cal_t"][det]) for v in sc]))
    return fl


def run_cell(cell: dict) -> dict:
    day_min, day_max, t_max = G["day_min"], G["day_max"], G["t_max_s"]
    per = []
    skipped = 0
    for day in range(day_min, day_max + 1):
        seed = day - day_min
        recs = place(build(cell, seed), day)
        if max(x.t_sched_ns for x in recs) / NS > t_max:
            skipped += 1
            continue
        fl = score(recs)
        jm = max(fl.values())
        per.append(
            {
                "day": day,
                "flagged": fl,
                "joint_max": jm,
                "any": jm > 0.0,
                "over_0.10": jm > 0.10,
                "wall_clock_h": price(recs)["wall_clock_s"] / 3600,
            }
        )
    res = {**cell, "n_placements": len(per), "n_skipped_end_of_timeline": skipped, "per": per}
    s = summarise(per)
    print(
        f"{cell['source']} {cell['kind']} n={cell['n']} S={cell['stagger_h']} cap={cell.get('count_cap')} "
        f"mult={cell.get('session_mult')}: {len(per)} placements, joint median {s['joint_max']['median']:.2f} "
        f"p95 {s['joint_max']['p95']:.2f}, P(any) {s['p_any_unit_flagged']:.2f}, P(>0.10) {s['p_over_0.10']:.2f}",
        flush=True,
    )
    return res


def summarise(per: list[dict]) -> dict:
    dets = sorted({d for p in per for d in p["flagged"]})
    out = {"n": len(per)}
    for det in dets:
        v = np.array([p["flagged"][det] for p in per if det in p["flagged"]])
        out[det] = {
            "median": float(np.median(v)),
            "p5": float(np.percentile(v, 5)),
            "p95": float(np.percentile(v, 95)),
            "min": float(v.min()),
            "max": float(v.max()),
        }
    jm = np.array([p["joint_max"] for p in per])
    out["joint_max"] = {
        "median": float(np.median(jm)),
        "p5": float(np.percentile(jm, 5)),
        "p95": float(np.percentile(jm, 95)),
        "max": float(jm.max()),
    }
    out["p_any_unit_flagged"] = float(np.mean([p["any"] for p in per]))
    out["p_over_0.10"] = float(np.mean([p["over_0.10"] for p in per]))
    out["clears"] = out["joint_max"]["median"] <= 0.10
    out["wall_clock_h_median"] = float(np.median([p["wall_clock_h"] for p in per]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--campaign-label", required=True)
    ap.add_argument("--max-sessions", type=int, default=20)
    ap.add_argument("--search-label", default="v2_l9_search")
    ap.add_argument("--out-label", required=True)
    ap.add_argument("--cap", type=int, default=26)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--table4-seeds", type=int, default=50)
    ap.add_argument(
        "--shard", default="", help="k/N: run cells k::N sequentially, write a shard file"
    )
    ap.add_argument(
        "--merge", type=int, default=0, help="N: merge N shard files instead of running"
    )
    a = ap.parse_args()
    root = host_repo()
    bdir = root / "benign" / a.benign_label
    man = json.loads((bdir / "manifest_abs.json").read_text())
    benign = timeline_abs(bdir / "timeline_abs.jsonl")
    rows_b = identity_days(benign)
    feat_b = np.stack([features(r) for r in rows_b])
    std = Standardiser(feat_b)
    zb = std(feat_b)
    days_b = np.array([r["day"] for r in rows_b])
    r = nearest_neighbour_radius(zb, days_b)
    dens_b = same_day_density(zb, days_b, r)
    cal10 = D.calibrate(dens_b.astype(float).tolist(), "high", 0.01)
    bb = np.array(sorted(births(benign).values()))
    cal11 = D.calibrate(birth_burst(bb, 600.0).astype(float).tolist(), "high", 0.01)
    bvals: dict[str, list[float]] = defaultdict(list)
    for st in timeline_stats(benign):
        bvals[st.detector_id].append(st.value)
    cal_t = {det: D.calibrate(v, D.DIRECTION[det], 0.01) for det, v in bvals.items()}
    if cal_t["D1"]["threshold"] != 26 or cal10["threshold"] != 35 or cal11["threshold"] != 15:
        raise RuntimeError(
            f"registered thresholds not reproduced: D1 {cal_t['D1']['threshold']}, D10 {cal10['threshold']}, D11 {cal11['threshold']}"
        )
    by_day: dict[int, np.ndarray] = {}
    for i, d in enumerate(days_b):
        by_day.setdefault(int(d), []).append(i)
    by_day = {d: np.array(v) for d, v in by_day.items()}
    cdir = root / "results" / "raw" / "campaign" / a.campaign_label
    camp, _ = calibration_records(read_records(cdir / "records.jsonl"))
    if a.max_sessions:
        camp = [c for c in camp if int(c.session_id.rsplit(":s", 1)[1]) < a.max_sessions]
    day_min, day_max = int(man["t_min_s"] // 86400), int(man["t_max_s"] // 86400)
    state = dict(
        zb=zb,
        by_day=by_day,
        r=r,
        std=std,
        days_b=days_b,
        cal10=cal10,
        cal11=cal11,
        cal_t=cal_t,
        bb=bb,
        camp=camp,
        cap=a.cap,
        interval=3600.0 / (a.cap - 1),
        benign_counts=[row["requests"] for row in rows_b],
        benign_sess=[int(x) for row in rows_b for x in [row["session_len_median"]] if x >= 1],
        day_min=day_min,
        day_max=day_max,
        t_max_s=man["t_max_s"],
    )
    G.update(state)
    # original five placement days, as m4_coordination.place / m4_attacker_search drew them
    original_days = [
        int(np.random.default_rng(1000 + s).integers(day_min, day_max)) for s in range(5)
    ]

    cells = [
        {"source": "table5", "kind": "roundrobin", "n": n, "stagger_h": None}
        for n in (10, 100, 1000)
    ]
    cells += [
        {"source": "table5", "kind": "heterogeneous", "n": n, "stagger_h": S}
        for n in (100, 1000)
        for S in (0, 6, 24, 72)
    ]
    search = json.loads(
        (root / "results" / "aggregates" / "m4" / a.search_label / "search.json").read_text()
    )
    for c in search["cells"]:
        if c["clears"]:
            cells.append(
                {
                    "source": "search",
                    "kind": "heterogeneous",
                    "n": c["n"],
                    "count_cap": c["count_cap"],
                    "session_mult": c["session_mult"],
                    "stagger_h": c["stagger_h"],
                    "five_placement_joint_max": c["joint_max"],
                    "five_placement_wall_clock_h": c["wall_clock_h"],
                }
            )

    # verification of the restricted density against the registered routine (rule 3)
    for seed in range(3):
        recs = place(build(cells[0], seed), day_min + 10 + seed)
        rows_c = identity_days(recs)
        zc = std(np.stack([features(x) for x in rows_c]))
        dc = np.array([x["day"] for x in rows_c])
        full = score_campaign(zb, days_b, zc, dc, r)
        fast = restricted_density(zc, dc)
        if not np.array_equal(full, fast):
            raise RuntimeError(f"restricted density differs from score_campaign at seed {seed}")
    print(f"density check passed; {len(cells)} cells; days {day_min}..{day_max}", flush=True)

    out_dir = root / "results" / "aggregates" / "m5" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    if a.merge:
        done = []
        for k in range(a.merge):
            sh = json.loads((out_dir / f"shard_{k}_of_{a.merge}.json").read_text())
            done += sh["cells"]
        if len(done) != len(cells):
            raise RuntimeError(f"merged {len(done)} cells, expected {len(cells)}")
        order = {
            json.dumps(
                {
                    k: c.get(k)
                    for k in ("source", "kind", "n", "count_cap", "session_mult", "stagger_h")
                },
                sort_keys=True,
            ): i
            for i, c in enumerate(cells)
        }
        done.sort(
            key=lambda c: order[
                json.dumps(
                    {
                        k: c.get(k)
                        for k in ("source", "kind", "n", "count_cap", "session_mult", "stagger_h")
                    },
                    sort_keys=True,
                )
            ]
        )
    else:
        if a.shard:
            k, n = (int(x) for x in a.shard.split("/"))
            mine = cells[k::n]
        else:
            k, n, mine = 0, 1, cells
        if a.shard or a.workers <= 1:
            done = [run_cell(c) for c in mine]
        else:
            with ProcessPoolExecutor(
                max_workers=a.workers,
                mp_context=get_context("spawn"),
                initializer=_init,
                initargs=(state,),
            ) as ex:
                done = list(ex.map(run_cell, mine))
        if a.shard:
            (out_dir / f"shard_{k}_of_{n}.json").write_text(
                json.dumps({"cells": done}, default=float)
            )
            print(f"shard {k}/{n} written ({len(done)} cells)")
            return 0
    for c in done:
        c["summary_all"] = summarise(c["per"])
        rest = [p for p in c["per"] if p["day"] not in original_days]
        c["summary_excluding_original_days"] = summarise(rest) if rest else None

    # price-table cells under 50 re-schedulings (jitter only; placement-free detectors)
    table4 = []
    for n in (1, 10, 100, 1000):
        for cap in (0, 26, 8, 2):
            per = []
            for seed in range(a.table4_seeds):
                recs = split_identities(camp, n, seed)
                if cap:
                    recs = shape_rate(recs, cap, seed)
                cv: dict[str, list[float]] = defaultdict(list)
                for st in timeline_stats(recs):
                    cv[st.detector_id].append(st.value)
                fl = {}
                for det in ("D1", "D2", "D3", "D9"):
                    sc = [v for v in cv[det] if not math.isnan(v)]
                    fl[det] = float(np.mean([D.fires(v, cal_t[det]) for v in sc])) if sc else None
                per.append(
                    {
                        "seed": seed,
                        "flagged": fl,
                        "wall_clock_h": price(recs)["wall_clock_s"] / 3600,
                    }
                )
            wc = [p["wall_clock_h"] for p in per]
            table4.append(
                {
                    "n": n,
                    "cap": cap,
                    "wall_clock_h": {
                        "median": float(np.median(wc)),
                        "min": float(min(wc)),
                        "max": float(max(wc)),
                    },
                    "flagged": {
                        det: {
                            "median": float(
                                np.median(
                                    [
                                        p["flagged"][det]
                                        for p in per
                                        if p["flagged"][det] is not None
                                    ]
                                )
                            ),
                            "min": float(
                                min(p["flagged"][det] for p in per if p["flagged"][det] is not None)
                            ),
                            "max": float(
                                max(p["flagged"][det] for p in per if p["flagged"][det] is not None)
                            ),
                        }
                        for det in ("D1", "D2", "D3", "D9")
                        if any(p["flagged"][det] is not None for p in per)
                    },
                }
            )

    clearing = [c for c in done if c["source"] == "search"]
    still = [c for c in clearing if c["summary_all"]["clears"]]
    p = {
        "P28_ten_account_d11_any": next(
            c["summary_all"]["D11"]
            for c in done
            if c["source"] == "table5" and c["kind"] == "roundrobin" and c["n"] == 10
        ),
        "P29_frac_clearing_still_clear": len(still) / len(clearing) if clearing else None,
        "P30_cell50": next(
            (
                c["summary_all"]["p_over_0.10"]
                for c in clearing
                if c["n"] == 50
                and c["count_cap"] == 26
                and c["session_mult"] == 10
                and c["stagger_h"] == 6
            ),
            None,
        ),
        "P31_cell100_shortest": next(
            (
                c["summary_all"]["p_over_0.10"]
                for c in clearing
                if c["n"] == 100
                and c["count_cap"] == 26
                and c["session_mult"] == 10
                and c["stagger_h"] == 6
            ),
            None,
        ),
    }
    ten = next(
        c for c in done if c["source"] == "table5" and c["kind"] == "roundrobin" and c["n"] == 10
    )
    p["P28_ten_account_p_any_d11"] = float(np.mean([x["flagged"]["D11"] > 0 for x in ten["per"]]))
    result = {
        "benign_label": a.benign_label,
        "campaign": f"{a.campaign_label}:{a.max_sessions}",
        "cap": a.cap,
        "thresholds": {
            "D10": cal10["threshold"],
            "D11": cal11["threshold"],
            **{d: c["threshold"] for d, c in cal_t.items()},
        },
        "days": [day_min, day_max],
        "original_days": original_days,
        "predictions": p,
        "cells": done,
        "table4": table4,
    }
    (out_dir / "placements.json").write_text(json.dumps(result, indent=1, default=float))
    md = [
        f"All-day placements (campaign {a.campaign_label}:{a.max_sessions}, cap {a.cap}; days {day_min}..{day_max}; one re-scheduling per eligible day). "
        "Median [p5, p95] of flagged fractions; P(any) = share of placements with at least one unit flagged by any content-blind detector; P(>0.10) = share with joint max above 0.10.\n",
        "| Source | Kind | n | Draw cap | Sess mult | Stagger h | Placements | D10 | D11 | D2 | Joint max | P(any) | P(>0.10) | Clears | Excl. original: joint med, P(>0.10) | Hours |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for c in done:
        s = c["summary_all"]
        e = c["summary_excluding_original_days"]

        def f(d: str) -> str:
            if d not in s:
                return "n/a"
            return f"{s[d]['median']:.2f} [{s[d]['p5']:.2f}, {s[d]['p95']:.2f}]"

        md.append(
            f"| {c['source']} | {c['kind']} | {c['n']} | {c.get('count_cap', '')} | {c.get('session_mult', '')} | {'' if c['stagger_h'] is None else c['stagger_h']} | {c['n_placements']} | "
            f"{f('D10')} | {f('D11')} | {f('D2')} | {s['joint_max']['median']:.2f} [{s['joint_max']['p5']:.2f}, {s['joint_max']['p95']:.2f}] | "
            f"{s['p_any_unit_flagged']:.2f} | {s['p_over_0.10']:.2f} | {'yes' if s['clears'] else 'no'} | "
            f"{e['joint_max']['median']:.2f}, {e['p_over_0.10']:.2f} | {s['wall_clock_h_median']:.1f} |"
        )
    md += [
        "",
        f"Predictions: {json.dumps(p)}",
        "",
        "Price-table cells, 50 re-schedulings: hours median [min, max]; D1, D2 flagged median [min, max].",
        "| n | cap | hours | D1 | D2 |",
        "|---|---|---|---|---|",
    ]
    for t in table4:
        w = t["wall_clock_h"]
        md.append(
            f"| {t['n']} | {t['cap'] or 'none'} | {w['median']:.1f} [{w['min']:.1f}, {w['max']:.1f}] | "
            + " | ".join(
                f"{t['flagged'][d]['median']:.2f} [{t['flagged'][d]['min']:.2f}, {t['flagged'][d]['max']:.2f}]"
                for d in ("D1", "D2")
            )
            + " |"
        )
    (out_dir / "table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    sys.exit(main())
