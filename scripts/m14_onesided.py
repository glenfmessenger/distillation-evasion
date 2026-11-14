#!/usr/bin/env python
"""Amendment B15 (2): one-sided thresholds on the matched pattern units of B14 (B).

Each of the six statistics with a 1% threshold on each side separately, on benign replay
sessions of at least ten records and campaigns cut to benign session sizes.

Writes results/aggregates/m14/<out-label>/onesided.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from dev_harness.detectors import stats as D
from dev_harness.paths import host_repo
from dev_harness.writer import calibration_records, read_records

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m13_pattern import BUDGET, FEATS, matrix  # noqa: E402
from m6_thresholds import CAMPAIGNS, relabel  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--out-label", required=True)
    a = ap.parse_args()
    root = host_repo()
    replay, _ = calibration_records(
        read_records(root / "results" / "raw" / "benign" / a.benign_label / "records.jsonl")
    )
    ref = D.BenignReference.fit(replay)
    sizes = [len(v) for v in D.by_session(replay).values() if len(v) >= D.MIN_SCOREABLE]
    xb, _ = matrix(replay, ref)
    out: dict = {"n_benign_sessions": len(xb), "statistics": {}}
    best = (0.0, None)
    camps = {}
    for spec in CAMPAIGNS:
        label, _, k = spec.partition(":")
        recs, _ = calibration_records(
            read_records(root / "results" / "raw" / "campaign" / label / "records.jsonl")
        )
        if k:
            recs = [r for r in recs if int(r.session_id.rsplit(":s", 1)[1]) < int(k)]
        camps[spec], _ = matrix(relabel(recs, "benign-sized", sizes), ref)
    for j, f in enumerate(FEATS):
        b = xb[:, j]
        b = b[~np.isnan(b)]
        out["statistics"][f] = {}
        for side in ("low", "high"):
            cal = D.calibrate(b.tolist(), side, BUDGET)
            row = {
                "threshold": cal["threshold"],
                "n_exceed": cal["n_exceed"],
                "below_resolution": cal["below_resolution"],
                "campaigns": {},
            }
            for spec, xc in camps.items():
                c = xc[:, j]
                c = c[~np.isnan(c)]
                fl = float(np.mean([bool(D.fires(v, cal)) for v in c])) if len(c) else None
                row["campaigns"][spec] = fl
                if fl is not None and not cal["below_resolution"] and fl > best[0]:
                    best = (fl, (f, side, spec))
            out["statistics"][f][side] = row
    out["max_resolved"] = {"flagged": best[0], "where": best[1]}
    out["p65"] = {
        "max": best[0],
        "where": best[1],
        "holds": best[0] <= 0.15
        and best[1] is not None
        and best[1][0] == "D4"
        and best[1][1] == "low"
        and best[1][2] in ("c_real_v2:20", "c_real_v2_s1"),
    }
    out_dir = root / "results" / "aggregates" / "m14" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "onesided.json").write_text(json.dumps(out, indent=1, default=float))
    for f, sides in out["statistics"].items():
        for side, r in sides.items():
            print(
                f,
                side,
                f"thr {r['threshold']:.3g} exceed {r['n_exceed']}{' (below res.)' if r['below_resolution'] else ''}",
                {k: (None if v is None else round(v, 2)) for k, v in r["campaigns"].items()},
            )
    print("P65", out["p65"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
