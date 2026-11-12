#!/usr/bin/env python
"""Amendment B4 item 2: the combined adaptive attacker L9, an exhaustive grid searched against
every content-blind detector at once (D1, D2, D3, D9 from the timeline calibration; D10; D11;
D4 to D8 are session-shape statistics unchanged by re-scheduling and were 0 flagged in every
lever cell, F47/F49). A cell clears when every detector's median flagged fraction over 5
placements is at most 0.10. Writes results/aggregates/m4/<out-label>/{search.json,table.md}.
"""

from __future__ import annotations

import argparse
import itertools
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
from dev_harness.levers import price, split_heterogeneous
from dev_harness.paths import host_repo
from dev_harness.writer import calibration_records, read_records

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m4_coordination import timeline_abs  # noqa: E402

NS = 1_000_000_000
GRID = {
    "n": [50, 100, 200, 500, 1000],
    "count_cap": [26, 100, 300],
    "session_mult": [1.0, 3.0, 10.0],
    "stagger_h": [0, 6, 24, 72, 168],
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--campaign-label", required=True)
    ap.add_argument("--out-label", required=True)
    ap.add_argument("--max-sessions", type=int, default=0)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--cap", type=int, default=26)
    a = ap.parse_args()
    root = host_repo()
    bdir = root / "benign" / a.benign_label
    man = json.loads((bdir / "manifest_abs.json").read_text())
    benign = timeline_abs(bdir / "timeline_abs.jsonl")
    rows_b = identity_days(benign)
    zb = Standardiser(np.stack([features(r) for r in rows_b]))
    std = zb
    zb = std(np.stack([features(r) for r in rows_b]))
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
    benign_counts = [row["requests"] for row in rows_b]
    benign_sess = [int(x) for row in rows_b for x in [row["session_len_median"]] if x >= 1]
    cdir = root / "results" / "raw" / "campaign" / a.campaign_label
    camp, _ = calibration_records(read_records(cdir / "records.jsonl"))
    if a.max_sessions:
        camp = [c for c in camp if int(c.session_id.rsplit(":s", 1)[1]) < a.max_sessions]
    day_min, day_max = int(man["t_min_s"] // 86400), int(man["t_max_s"] // 86400)
    interval = 3600.0 / (a.cap - 1)

    cells = []
    for n, cc, sm, S in itertools.product(
        GRID["n"], GRID["count_cap"], GRID["session_mult"], GRID["stagger_h"]
    ):
        per = []
        for seed in range(a.seeds):
            recs = split_heterogeneous(
                camp,
                n,
                seed,
                benign_counts,
                benign_sess,
                S * 3600.0,
                interval,
                count_cap=cc,
                session_mult=sm,
            )
            rng = np.random.default_rng(1000 + seed)
            t0 = int(rng.integers(day_min, day_max)) * 86400 * NS
            base = min(x.t_sched_ns for x in recs)
            recs = [x.model_copy(update={"t_sched_ns": x.t_sched_ns - base + t0}) for x in recs]
            rows_c = identity_days(recs)
            dens = score_campaign(
                zb,
                days_b,
                std(np.stack([features(x) for x in rows_c])),
                np.array([x["day"] for x in rows_c]),
                r,
            )
            flagged = {"D10": float(np.mean([D.fires(float(v), cal10) for v in dens]))}
            v11 = score_births(bb, np.array(list(births(recs).values())), 600.0)
            flagged["D11"] = float(np.mean([D.fires(float(v), cal11) for v in v11]))
            cv: dict[str, list[float]] = defaultdict(list)
            for st in timeline_stats(recs):
                cv[st.detector_id].append(st.value)
            for det, vals in cv.items():
                sc = [v for v in vals if not math.isnan(v)]
                if sc:
                    flagged[det] = float(np.mean([D.fires(v, cal_t[det]) for v in sc]))
            per.append({"seed": seed, "flagged": flagged, "price": price(recs)})
        med = {
            det: sorted(p["flagged"].get(det, 0.0) for p in per)[len(per) // 2]
            for det in ("D1", "D2", "D3", "D9", "D10", "D11")
        }
        wc = sorted(p["price"]["wall_clock_s"] / 3600 for p in per)[len(per) // 2]
        cells.append(
            {
                "n": n,
                "count_cap": cc,
                "session_mult": sm,
                "stagger_h": S,
                "median_flagged": med,
                "joint_max": max(med.values()),
                "clears": max(med.values()) <= 0.10,
                "wall_clock_h": wc,
                "per_seed": per,
            }
        )
        print(
            f"n={n} cap={cc} sm={sm} S={S}: joint {max(med.values()):.2f} wall {wc:.1f}", flush=True
        )

    out_dir = root / "results" / "aggregates" / "m4" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    clearing = [c for c in cells if c["clears"]]
    result = {"grid": GRID, "n_cells": len(cells), "n_clearing": len(clearing), "cells": cells}
    (out_dir / "search.json").write_text(json.dumps(result, indent=1))
    md = [
        f"L9 search ({len(cells)} cells, {a.seeds} placements each; a cell clears when every content-blind detector's median flagged fraction is at most 0.10). Clearing cells: {len(clearing)}.\n",
        "| n | count cap | session mult | stagger h | D1 | D2 | D3 | D9 | D10 | D11 | joint max | wall-clock h |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for c in (
        sorted(clearing, key=lambda c: (c["wall_clock_h"], c["n"]))
        or sorted(cells, key=lambda c: c["joint_max"])[:15]
    ):
        m = c["median_flagged"]
        md.append(
            f"| {c['n']} | {c['count_cap']} | {c['session_mult']:g} | {c['stagger_h']} | {m['D1']:.2f} | {m['D2']:.2f} | {m['D3']:.2f} | {m['D9']:.2f} | {m['D10']:.2f} | {m['D11']:.2f} | {c['joint_max']:.2f} | {c['wall_clock_h']:.1f} |"
        )
    (out_dir / "table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[:25]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
