#!/usr/bin/env python
"""Amendment B4 item 3: D3 (cadence CV) for the campaigns computed on response completion times,
so that campaign inter-arrivals include generation latency as the benign reply-stamped
inter-arrivals do; reported beside the registered send-time version. Timeline calibration.
Writes results/aggregates/m4/<out-label>/{d3_completion.json,table.md}.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

from dev_harness.detectors import stats as D
from dev_harness.detectors.analysis import auc, timeline_stats
from dev_harness.paths import host_repo
from dev_harness.writer import calibration_records, read_records

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m4_coordination import timeline_abs  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--campaigns", required=True, help="label[:max_sessions],...")
    ap.add_argument("--out-label", required=True)
    a = ap.parse_args()
    root = host_repo()
    benign = timeline_abs(root / "benign" / a.benign_label / "timeline_abs.jsonl")
    bvals = [s.value for s in timeline_stats(benign) if s.detector_id == "D3"]
    cal = {str(b): D.calibrate(bvals, "low", b) for b in (0.01, 0.001)}
    out, md = (
        {},
        [
            "| Campaign | Time base | Sessions | Median CV | Flagged 1% | Flagged 0.1% | AUC |",
            "|---|---|---|---|---|---|---|",
        ],
    )
    for spec in a.campaigns.split(","):
        label, _, k = spec.partition(":")
        camp, _ = calibration_records(
            read_records(root / "results" / "raw" / "campaign" / label / "records.jsonl")
        )
        if k:
            camp = [c for c in camp if int(c.session_id.rsplit(":s", 1)[1]) < int(k)]
        res = {}
        for base, field in (("send", "t_send_ns"), ("completion", "t_done_ns")):
            recs = [c.model_copy(update={"t_sched_ns": getattr(c, field)}) for c in camp]
            vals = [s.value for s in timeline_stats(recs) if s.detector_id == "D3"]
            sc = [v for v in vals if not math.isnan(v)]
            fl = {b: float(np.mean([D.fires(v, cal[b]) for v in sc])) for b in cal}
            res[base] = {
                "n_sessions": len(sc),
                "median_cv": float(np.median(sc)),
                "flagged": fl,
                "auc": auc(vals, bvals, "low"),
            }
            md.append(
                f"| {spec} | {base} | {len(sc)} | {np.median(sc):.4f} | {fl['0.01']:.2f} | {fl['0.001']:.2f} | {res[base]['auc']:.3f} |"
            )
        out[spec] = res
    out_dir = root / "results" / "aggregates" / "m4" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "d3_completion.json").write_text(
        json.dumps({"calibration": cal, "campaigns": out}, indent=1)
    )
    (out_dir / "table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
