#!/usr/bin/env python
"""Amendment B8 item 3: budgets and campaign size for the timeline-calibrated detectors.

Thresholds at 1%, 0.1% and 0.01% for D1, D2, D3, D9 (timeline) and D10, D11; the price-table
cells (round-robin × cap, 2,000 and 8,000 requests) scored by D1 and D2 at each budget; the
ten-account rate-capped, 50-account search and 100-account round-robin cells scored by every
timeline-calibrated detector at each budget on the five registered placements; the ten- and
50-account cells on the 8,000-request run at 1%.

Writes results/aggregates/m7/<out-label>/{budgets.json,table.md}.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
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
BUDGETS = (0.01, 0.001, 0.0001)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--campaign-label", default="c_real_v2")
    ap.add_argument("--out-label", required=True)
    ap.add_argument("--cap", type=int, default=26)
    a = ap.parse_args()
    root = host_repo()
    bdir = root / "benign" / a.benign_label
    man = json.loads((bdir / "manifest_abs.json").read_text())
    benign = timeline_abs(bdir / "timeline_abs.jsonl")
    rows_b = identity_days(benign)
    feat_b = np.stack([features(r) for r in rows_b])
    days_b = np.array([r["day"] for r in rows_b])
    std = Standardiser(feat_b)
    zb = std(feat_b)
    r = nearest_neighbour_radius(zb, days_b)
    dens_b = same_day_density(zb, days_b, r).astype(float).tolist()
    bb = np.array(sorted(births(benign).values()))
    burst_b = birth_burst(bb, 600.0).astype(float).tolist()
    bvals: dict[str, list[float]] = defaultdict(list)
    for st in timeline_stats(benign):
        bvals[st.detector_id].append(st.value)
    cal: dict[str, dict[str, dict]] = {}
    for b in BUDGETS:
        cal[str(b)] = {det: D.calibrate(v, D.DIRECTION[det], b) for det, v in bvals.items()}
        cal[str(b)]["D10"] = D.calibrate(dens_b, "high", b)
        cal[str(b)]["D11"] = D.calibrate(burst_b, "high", b)
    if cal["0.01"]["D1"]["threshold"] != 26 or cal["0.01"]["D10"]["threshold"] != 35:
        raise RuntimeError("registered thresholds not reproduced")
    d1_benign = np.asarray([v for v in bvals["D1"] if not math.isnan(v)])
    caps = {str(qq): max(1, int(math.floor(np.quantile(d1_benign, qq)))) for qq in (0.99, 0.9, 0.5)}
    cdir = root / "results" / "raw" / "campaign" / a.campaign_label
    camp_all, _ = calibration_records(read_records(cdir / "records.jsonl"))
    camp20 = [c for c in camp_all if int(c.session_id.rsplit(":s", 1)[1]) < 20]
    day_min, day_max = int(man["t_min_s"] // 86400), int(man["t_max_s"] // 86400)
    benign_counts = [row["requests"] for row in rows_b]
    benign_sess = [int(x) for row in rows_b for x in [row["session_len_median"]] if x >= 1]
    interval = 3600.0 / (a.cap - 1)

    def tl_flags(recs, b):
        cv: dict[str, list[float]] = defaultdict(list)
        for st in timeline_stats(recs):
            cv[st.detector_id].append(st.value)
        out = {}
        for det, vals in cv.items():
            sc = [v for v in vals if not math.isnan(v)]
            out[det] = float(np.mean([D.fires(v, cal[str(b)][det]) for v in sc])) if sc else None
        return out

    # ---- price-table cells by budget (placement-free)
    price_rows = []
    for size, camp in (("2000", camp20), ("8000", camp_all)):
        for n in (1, 10, 100, 1000):
            for capc in (0, caps["0.99"], caps["0.9"], caps["0.5"]):
                per = []
                for seed in range(5):
                    recs = split_identities(camp, n, seed)
                    if capc:
                        recs = shape_rate(recs, capc, seed)
                    per.append(
                        {b: tl_flags(recs, b) for b in BUDGETS}
                        | {"hours": price(recs)["wall_clock_s"] / 3600}
                    )
                price_rows.append(
                    {
                        "size": size,
                        "n": n,
                        "cap": capc,
                        "hours": float(np.median([p["hours"] for p in per])),
                        "flagged": {
                            str(b): {
                                det: float(
                                    np.median([p[b][det] for p in per if p[b].get(det) is not None])
                                )
                                for det in ("D1", "D2")
                            }
                            for b in BUDGETS
                        },
                    }
                )
        print(f"price cells at {size}: done", flush=True)

    # ---- headline cross-account cells by budget, five registered placements
    def place(recs, seed):
        rng = np.random.default_rng(1000 + seed)
        t0 = int(rng.integers(day_min, day_max)) * 86400 * NS
        base = min(x.t_sched_ns for x in recs)
        return [x.model_copy(update={"t_sched_ns": x.t_sched_ns - base + t0}) for x in recs]

    def cross(recs):
        rows_c = identity_days(recs)
        dens = score_campaign(
            zb,
            days_b,
            std(np.stack([features(x) for x in rows_c])),
            np.array([x["day"] for x in rows_c]),
            r,
        )
        v11 = score_births(bb, np.array(list(births(recs).values())), 600.0)
        return dens, v11

    cells = {
        "round-robin 10": lambda camp, s: shape_rate(split_identities(camp, 10, s), a.cap, s),
        "round-robin 100": lambda camp, s: shape_rate(split_identities(camp, 100, s), a.cap, s),
        "search 50": lambda camp, s: split_heterogeneous(
            camp,
            50,
            s,
            benign_counts,
            benign_sess,
            6 * 3600.0,
            interval,
            count_cap=26,
            session_mult=10.0,
        ),
    }
    cell_rows = []
    for size, camp in (("2000", camp20), ("8000", camp_all)):
        for name, build in cells.items():
            if size == "8000" and name == "round-robin 100":
                continue
            per = []
            for seed in range(5):
                recs = place(build(camp, seed), seed)
                dens, v11 = cross(recs)
                row = {"hours": price(recs)["wall_clock_s"] / 3600}
                for b in BUDGETS:
                    fl = tl_flags(recs, b)
                    fl["D10"] = float(
                        np.mean([D.fires(float(v), cal[str(b)]["D10"]) for v in dens])
                    )
                    fl["D11"] = float(np.mean([D.fires(float(v), cal[str(b)]["D11"]) for v in v11]))
                    row[str(b)] = fl
                per.append(row)
            summary = {}
            for b in BUDGETS:
                dets = sorted({d for p in per for d in p[str(b)]})
                med = {
                    d: float(np.median([p[str(b)][d] for p in per if p[str(b)].get(d) is not None]))
                    for d in dets
                }
                summary[str(b)] = {"median_flagged": med, "joint_max": max(v for v in med.values())}
            cell_rows.append(
                {
                    "size": size,
                    "cell": name,
                    "hours": float(np.median([p["hours"] for p in per])),
                    "by_budget": summary,
                }
            )
            print(
                f"{name} at {size}: "
                + ", ".join(f"{b}: {summary[str(b)]['joint_max']:.2f}" for b in BUDGETS),
                flush=True,
            )

    thr = {str(b): {det: cal[str(b)][det]["threshold"] for det in cal[str(b)]} for b in BUDGETS}
    p45 = {
        "thr_d1": {b: thr[b]["D1"] for b in thr},
        "hundred_at_tenth": cell_rows[1]["by_budget"]["0.001"]["median_flagged"],
        "ten_8000": next(
            c for c in cell_rows if c["size"] == "8000" and c["cell"] == "round-robin 10"
        ),
        "fifty_8000": next(
            c for c in cell_rows if c["size"] == "8000" and c["cell"] == "search 50"
        ),
    }
    result = {
        "thresholds": thr,
        "rate_caps": caps,
        "price_cells": price_rows,
        "cross_cells": cell_rows,
        "p45": p45,
    }
    out_dir = root / "results" / "aggregates" / "m7" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "budgets.json").write_text(json.dumps(result, indent=1, default=float))
    md = [
        "Thresholds by budget: "
        + "; ".join(f"{b}: " + ", ".join(f"{d} {v:.4g}" for d, v in thr[b].items()) for b in thr),
        "",
        "| Size | n | cap | hours | D1 1% / 0.1% / 0.01% | D2 1% / 0.1% / 0.01% |",
        "|---|---|---|---|---|---|",
    ]
    for p in price_rows:
        md.append(
            f"| {p['size']} | {p['n']} | {p['cap'] or 'none'} | {p['hours']:.1f} | "
            + " / ".join(f"{p['flagged'][str(b)]['D1']:.2f}" for b in BUDGETS)
            + " | "
            + " / ".join(f"{p['flagged'][str(b)]['D2']:.2f}" for b in BUDGETS)
            + " |"
        )
    md += [
        "",
        "| Size | Cell | hours | budget | D1 | D2 | D3 | D9 | D10 | D11 | joint |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for c in cell_rows:
        for b in BUDGETS:
            m = c["by_budget"][str(b)]["median_flagged"]
            md.append(
                f"| {c['size']} | {c['cell']} | {c['hours']:.1f} | {b} | "
                + " | ".join(
                    f"{m.get(d, float('nan')):.2f}" for d in ("D1", "D2", "D3", "D9", "D10", "D11")
                )
                + f" | {c['by_budget'][str(b)]['joint_max']:.2f} |"
            )
    (out_dir / "table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
