#!/usr/bin/env python
"""Amendment B7 items 3 and 6: the D10 scalings applied to every reported cell, and the
constructed populations on every placement day.

Item 3: each cross-account-table cell and each clearing cell of the search is re-scored under
the four D10 scalings (registered, constant features dropped, floor one, IQR) on the five
registered placements; the ten-account and 50-account cells, and the 100-account round-robin
cell, on every placement day under each scaling.
Item 6: the three B4 populations re-scored on every placement day under the registered scaling.

Writes results/aggregates/m6/<out-label>/{scale_cells.json,table.md}.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path

import numpy as np

from dev_harness.detectors import stats as D
from dev_harness.detectors.analysis import timeline_stats
from dev_harness.detectors.coordination import (
    birth_burst,
    births,
    features,
    identity_days,
    nearest_neighbour_radius,
    same_day_density,
    score_births,
)
from dev_harness.levers import shape_rate, split_heterogeneous, split_identities
from dev_harness.paths import host_repo
from dev_harness.writer import calibration_records, read_records

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m4_coord_controls import batch_job, eval_fleet, organisation  # noqa: E402
from m4_coordination import timeline_abs  # noqa: E402
from m5_coord_sensitivity import Scaler  # noqa: E402

NS = 1_000_000_000
VARIANTS = ("registered", "drop_constant", "floor_1", "iqr")
G: dict = {}


def _init(state: dict) -> None:
    G.update(state)


def density(zc: np.ndarray, dc: np.ndarray, v: dict) -> np.ndarray:
    zb, by_day, r = v["zb"], G["by_day"], v["r"]
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
        own = np.arange(len(c))
        within[own, nb + own] = False
        out[mc] = within.sum(axis=1)
    return out


def build(cell: dict, seed: int) -> list:
    camp = G["camp"]
    if cell["kind"] == "roundrobin":
        return shape_rate(split_identities(camp, cell["n"], seed), G["cap"], seed)
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
    return [
        x.model_copy(update={"t_sched_ns": x.t_sched_ns - base + day * 86400 * NS}) for x in recs
    ]


def score(recs: list, variant: str) -> dict:
    v = G["variants"][variant]
    rows_c = identity_days(recs)
    zc = v["std"](np.stack([features(x) for x in rows_c]))
    dc = np.array([x["day"] for x in rows_c])
    dens = density(zc, dc, v)
    fl = {"D10": float(np.mean([D.fires(float(x), v["cal10"]) for x in dens]))}
    v11 = score_births(G["bb"], np.array(list(births(recs).values())), 600.0)
    fl["D11"] = float(np.mean([D.fires(float(x), G["cal11"]) for x in v11]))
    cv: dict[str, list[float]] = defaultdict(list)
    for st in timeline_stats(recs):
        cv[st.detector_id].append(st.value)
    for det, vals in cv.items():
        sc = [x for x in vals if not math.isnan(x)]
        if sc:
            fl[det] = float(np.mean([D.fires(x, G["cal_t"][det]) for x in sc]))
    return fl


def five_placements(cell: dict) -> dict:
    """One cell under all four scalings on the five registered placements."""
    out = {}
    for variant in VARIANTS:
        per = []
        for seed in range(5):
            day = int(np.random.default_rng(1000 + seed).integers(G["day_min"], G["day_max"]))
            fl = score(place(build(cell, seed), day), variant)
            per.append({"seed": seed, "flagged": fl, "joint_max": max(fl.values())})
        med = {
            det: float(np.median([p["flagged"].get(det, 0.0) for p in per]))
            for det in ("D1", "D2", "D3", "D9", "D10", "D11")
        }
        out[variant] = {
            "median_flagged": med,
            "joint_max": max(med.values()),
            "clears": max(med.values()) <= 0.10,
            "per": per,
        }
    print(
        f"five: {cell['source']} n={cell['n']} S={cell['stagger_h']}: "
        + ", ".join(f"{k} {v['joint_max']:.2f}" for k, v in out.items()),
        flush=True,
    )
    return {**cell, "by_variant": out}


def all_days(job: dict) -> dict:
    """One (cell or population, variant) on every eligible placement day."""
    variant = job["variant"]
    per = []
    for day in range(G["day_min"], G["day_max"] + 1):
        seed = day - G["day_min"]
        if job["kind"] == "population":
            rng = np.random.default_rng(2000 + seed)
            t0 = float(day) * 86400
            if day > G["day_max"] - 40:
                continue
            recs = (
                organisation(G["benign_recs"], rng, t0)
                if job["name"] == "organisation"
                else batch_job(rng, t0)
                if job["name"] == "batch_job"
                else eval_fleet(rng, t0, 0.39)
            )
        else:
            recs = place(build(job, seed), day)
        if max(x.t_sched_ns for x in recs) / NS > G["t_max_s"]:
            continue
        fl = score(recs, variant)
        jm = max(fl.values())
        per.append({"day": day, "flagged": fl, "joint_max": jm})
    dets = sorted({d for p in per for d in p["flagged"]})
    summ = {"n": len(per)}
    for det in dets:
        v = np.array([p["flagged"][det] for p in per if det in p["flagged"]])
        summ[det] = {
            "median": float(np.median(v)),
            "p5": float(np.percentile(v, 5)),
            "p95": float(np.percentile(v, 95)),
            "max": float(v.max()),
        }
    jm = np.array([p["joint_max"] for p in per])
    summ["joint_max"] = {"median": float(np.median(jm)), "p95": float(np.percentile(jm, 95))}
    summ["p_any"] = float(np.mean(jm > 0))
    summ["p_over_0.10"] = float(np.mean(jm > 0.10))
    label = job.get("name") or f"{job['source']} n={job['n']} S={job['stagger_h']}"
    print(
        f"all-day {label} [{variant}]: {len(per)} days, joint median {summ['joint_max']['median']:.2f}, P(any) {summ['p_any']:.2f}, P(>0.10) {summ['p_over_0.10']:.2f}",
        flush=True,
    )
    return {**job, "summary": summ, "per": per}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--campaign-label", default="c_real_v2")
    ap.add_argument("--max-sessions", type=int, default=20)
    ap.add_argument("--search-label", default="v2_l9_search")
    ap.add_argument("--out-label", required=True)
    ap.add_argument("--cap", type=int, default=26)
    ap.add_argument("--workers", type=int, default=5)
    a = ap.parse_args()
    root = host_repo()
    bdir = root / "benign" / a.benign_label
    man = json.loads((bdir / "manifest_abs.json").read_text())
    benign = timeline_abs(bdir / "timeline_abs.jsonl")
    rows_b = identity_days(benign)
    feat_b = np.stack([features(r) for r in rows_b])
    days_b = np.array([r["day"] for r in rows_b])
    by_day: dict[int, list[int]] = {}
    for i, d in enumerate(days_b):
        by_day.setdefault(int(d), []).append(i)
    by_day = {d: np.array(v) for d, v in by_day.items()}
    variants = {}
    for name in VARIANTS:
        sc = Scaler(feat_b, name)
        zb = sc(feat_b)
        r = nearest_neighbour_radius(zb, days_b)
        cal10 = D.calibrate(same_day_density(zb, days_b, r).astype(float).tolist(), "high", 0.01)
        variants[name] = {"std": sc, "zb": zb, "r": r, "cal10": cal10}
        print(f"{name}: r {r:.3f} thr {cal10['threshold']:.0f}", flush=True)
    if variants["registered"]["cal10"]["threshold"] != 35:
        raise RuntimeError("registered D10 threshold not reproduced")
    bb = np.array(sorted(births(benign).values()))
    cal11 = D.calibrate(birth_burst(bb, 600.0).astype(float).tolist(), "high", 0.01)
    bvals: dict[str, list[float]] = defaultdict(list)
    for st in timeline_stats(benign):
        bvals[st.detector_id].append(st.value)
    cal_t = {det: D.calibrate(v, D.DIRECTION[det], 0.01) for det, v in bvals.items()}
    camp, _ = calibration_records(
        read_records(root / "results" / "raw" / "campaign" / a.campaign_label / "records.jsonl")
    )
    camp = [c for c in camp if int(c.session_id.rsplit(":s", 1)[1]) < a.max_sessions]
    day_min, day_max = int(man["t_min_s"] // 86400), int(man["t_max_s"] // 86400)
    state = dict(
        variants=variants,
        by_day=by_day,
        bb=bb,
        cal11=cal11,
        cal_t=cal_t,
        camp=camp,
        cap=a.cap,
        interval=3600.0 / (a.cap - 1),
        benign_counts=[row["requests"] for row in rows_b],
        benign_sess=[int(x) for row in rows_b for x in [row["session_len_median"]] if x >= 1],
        day_min=day_min,
        day_max=day_max,
        t_max_s=man["t_max_s"],
        benign_recs=benign,
    )
    G.update(state)
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
                }
            )
    ten = cells[0]
    fifty = next(
        c
        for c in cells
        if c["source"] == "search"
        and c["n"] == 50
        and c["count_cap"] == 26
        and c["session_mult"] == 10
        and c["stagger_h"] == 6
    )
    hundred = cells[1]
    jobs = [{**c, "variant": v} for v in VARIANTS for c in (ten, fifty, hundred)]
    jobs += [
        {"kind": "population", "name": nm, "variant": "registered"}
        for nm in ("organisation", "batch_job", "eval_fleet")
    ]
    with ProcessPoolExecutor(
        max_workers=a.workers, mp_context=get_context("spawn"), initializer=_init, initargs=(state,)
    ) as ex:
        five = list(ex.map(five_placements, cells))
        days = list(ex.map(all_days, jobs))
    # verdict agreement per variant (P39)
    agree = {}
    for v in VARIANTS[1:]:
        same = sum(
            1
            for c in five
            if c["by_variant"][v]["clears"] == c["by_variant"]["registered"]["clears"]
        )
        agree[v] = same / len(five)
    reg_sum = {}
    for d in days:
        key = d.get("name") or f"{d['source']}_n{d['n']}"
        reg_sum.setdefault(key, {})[d["variant"]] = d["summary"]
    p39 = {
        "verdict_agreement": agree,
        "headline_cells_p_over": {
            k: {v: s["p_over_0.10"] for v, s in vs.items()}
            for k, vs in reg_sum.items()
            if not k.startswith(("organisation", "batch", "eval"))
        },
    }
    # registered five-placement reproduction check: registered variant must match search.json joint max for search cells
    mism = [
        c
        for c in five
        if c["source"] == "search"
        and abs(c["by_variant"]["registered"]["joint_max"] - c["five_placement_joint_max"]) > 1e-9
    ]
    result = {
        "variants": {
            k: {"radius": v["r"], "threshold": v["cal10"]["threshold"]} for k, v in variants.items()
        },
        "five_placements": five,
        "all_days": days,
        "p39": p39,
        "n_registered_mismatch": len(mism),
    }
    out_dir = root / "results" / "aggregates" / "m6" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "scale_cells.json").write_text(json.dumps(result, indent=1, default=float))
    md = [
        f"D10 scalings on every reported cell, five registered placements. Verdict agreement with the registered scaling: {json.dumps(agree)}; registered-variant mismatches against the search evidence: {len(mism)}.",
        "| Source | Kind | n | Stagger | " + " | ".join(VARIANTS) + " |",
        "|---|---|---|---|" + "---|" * len(VARIANTS),
    ]
    for c in five:
        md.append(
            f"| {c['source']} | {c['kind']} | {c['n']} | {c['stagger_h']} | "
            + " | ".join(
                f"{c['by_variant'][v]['joint_max']:.2f}{'' if c['by_variant'][v]['clears'] else '*'}"
                for v in VARIANTS
            )
            + " |"
        )
    md += [
        "",
        "All-day: | Cell or population | Variant | Days | D10 median [p5, p95] | D11 median | Joint median | P(any) | P(>0.10) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for d in days:
        s = d["summary"]
        label = d.get("name") or f"{d['source']} n={d['n']} S={d['stagger_h']}"
        md.append(
            f"| {label} | {d['variant']} | {s['n']} | {s['D10']['median']:.2f} [{s['D10']['p5']:.2f}, {s['D10']['p95']:.2f}] | {s['D11']['median']:.2f} | {s['joint_max']['median']:.2f} | {s['p_any']:.2f} | {s['p_over_0.10']:.2f} |"
        )
    (out_dir / "table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    sys.exit(main())
