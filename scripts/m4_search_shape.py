#!/usr/bin/env python
"""Supplement to the L9 search (F66): score the output-shape detectors D4 to D8b, which depend on
session membership and identity composition, on every search cell, against the replay
calibration, and recompute the clearing criterion over all content-blind detectors. Rebuilds
each cell's records deterministically from the same seeds. Writes
results/aggregates/m4/<out-label>/{search_shape.json,table.md}.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from collections import defaultdict


from dev_harness.detectors import stats as D
from dev_harness.detectors.analysis import summarise
from dev_harness.detectors.coordination import identity_days
from dev_harness.levers import split_heterogeneous
from dev_harness.paths import host_repo
from dev_harness.writer import calibration_records, read_records

GRID = {
    "n": [50, 100, 200, 500, 1000],
    "count_cap": [26, 100, 300],
    "session_mult": [1.0, 3.0, 10.0],
    "stagger_h": [0, 6, 24, 72, 168],
}
SHAPE = ("D4", "D5", "D6", "D7", "D8", "D8b")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--campaign-label", required=True)
    ap.add_argument("--search-label", required=True)
    ap.add_argument("--out-label", required=True)
    ap.add_argument("--max-sessions", type=int, default=0)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--cap", type=int, default=26)
    a = ap.parse_args()
    root = host_repo()
    benign, _ = calibration_records(
        read_records(root / "results" / "raw" / "benign" / a.benign_label / "records.jsonl")
    )
    ref = D.BenignReference.fit(benign)
    bvals: dict[str, list[float]] = defaultdict(list)
    for s in D.all_statistics(benign, ref):
        if s.detector_id in SHAPE:
            bvals[s.detector_id].append(s.value)
    import sys as _s

    _s.path.insert(0, str(root))
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from m4_coordination import timeline_abs  # noqa: E402

    tl = timeline_abs(root / "benign" / a.benign_label / "timeline_abs.jsonl")
    rows_b = identity_days(tl)
    benign_counts = [r["requests"] for r in rows_b]
    benign_sess = [int(x) for r in rows_b for x in [r["session_len_median"]] if x >= 1]
    camp, _ = calibration_records(
        read_records(root / "results" / "raw" / "campaign" / a.campaign_label / "records.jsonl")
    )
    if a.max_sessions:
        camp = [c for c in camp if int(c.session_id.rsplit(":s", 1)[1]) < a.max_sessions]
    interval = 3600.0 / (a.cap - 1)
    search = json.loads(
        (root / "results" / "aggregates" / "m4" / a.search_label / "search.json").read_text()
    )
    by_key = {
        (c["n"], c["count_cap"], c["session_mult"], c["stagger_h"]): c for c in search["cells"]
    }
    out_cells = []
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
            cvals: dict[str, list[float]] = defaultdict(list)
            for s in D.all_statistics(recs, ref):
                if s.detector_id in SHAPE:
                    cvals[s.detector_id].append(s.value)
            fl = {}
            for det in SHAPE:
                sm_ = summarise(det, bvals[det], cvals.get(det, []))
                f = sm_["budgets"]["0.01"]["frac_flagged"]
                fl[det] = None if f is None else float(f)
            per.append(fl)
        med = {
            det: (
                sorted(v)[len(v) // 2]
                if (v := [p[det] for p in per if p[det] is not None])
                else None
            )
            for det in SHAPE
        }
        base = by_key[(n, cc, sm, S)]
        joint_all = max([base["joint_max"]] + [v for v in med.values() if v is not None])
        out_cells.append(
            {
                "n": n,
                "count_cap": cc,
                "session_mult": sm,
                "stagger_h": S,
                "shape_median_flagged": med,
                "joint_max_six": base["joint_max"],
                "joint_max_all": joint_all,
                "clears_all": joint_all <= 0.10,
                "wall_clock_h": base["wall_clock_h"],
                "per_seed_shape": per,
            }
        )
        print(
            f"n={n} cap={cc} sm={sm} S={S}: shape max {max([v for v in med.values() if v is not None] or [0]):.2f} joint_all {joint_all:.2f}",
            flush=True,
        )
    clearing = [c for c in out_cells if c["clears_all"]]
    out_dir = root / "results" / "aggregates" / "m4" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "search_shape.json").write_text(
        json.dumps(
            {"n_cells": len(out_cells), "n_clearing_all": len(clearing), "cells": out_cells},
            indent=1,
        )
    )
    md = [
        f"Shape detectors on the L9 search ({len(out_cells)} cells): clearing under all content-blind detectors = {len(clearing)}.\n",
        "| n | cap | sm | S | D4 | D5 | D6 | D7 | D8 | D8b | joint (six) | joint (all) | wall-clock h |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for c in sorted(clearing, key=lambda c: (c["wall_clock_h"], c["n"]))[:12]:
        m = c["shape_median_flagged"]
        md.append(
            f"| {c['n']} | {c['count_cap']} | {c['session_mult']:g} | {c['stagger_h']} | "
            + " | ".join("n/a" if m[d] is None else f"{m[d]:.2f}" for d in SHAPE)
            + f" | {c['joint_max_six']:.2f} | {c['joint_max_all']:.2f} | {c['wall_clock_h']:.1f} |"
        )
    (out_dir / "table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
