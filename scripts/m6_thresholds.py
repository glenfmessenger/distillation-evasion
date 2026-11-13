#!/usr/bin/env python
"""Amendment B7 items 1 and 2: two detector thresholds recalibrated after the benign-tail check.

D3 (cadence) recalibrated on benign sessions of at least five and at least ten requests, and
the unevaded campaigns re-scored under each threshold with declared, idle-gap and size-matched
sessions. D5 (reasoning share) recalibrated with records cut off at the generation cap excluded
from every session, benign and campaign alike; each campaign's own truncation rate reported.

Writes results/aggregates/m6/<out-label>/{thresholds.json,table.md}.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict

import numpy as np

from dev_harness.detectors import stats as D
from dev_harness.detectors.analysis import auc, timeline_records
from dev_harness.paths import host_repo
from dev_harness.writer import calibration_records, read_records

NS = 1_000_000_000
BUDGET = 0.01
CAMPAIGNS = ("pilot_baseline", "c_real_v2:20", "c_real_v2_s1", "c_instr_v2")


def relabel(camp: list, rule: str, benign_sizes: list[int]) -> list:
    """Campaign sessions as declared, by the idle-gap rule, or cut to benign session sizes
    (the B5 definitions, as in m3_analyse.py)."""
    if rule == "declared":
        return camp
    camp = sorted(camp, key=lambda r: r.t_send_ns)
    out = []
    if rule == "gap":
        sess, last = 0, camp[0].t_send_ns
        for r in camp:
            if (r.t_send_ns - last) / NS > 1800.0:
                sess += 1
            last = r.t_send_ns
            out.append(r.model_copy(update={"session_id": f"{r.identity_id}:g{sess}"}))
        return out
    rng = np.random.default_rng(0)
    sess, left = 0, int(rng.choice(benign_sizes))
    for r in camp:
        if left == 0:
            sess, left = sess + 1, int(rng.choice(benign_sizes))
        out.append(r.model_copy(update={"session_id": f"{r.identity_id}:b{sess}"}))
        left -= 1
    return out


def frac_flagged(vals: list[float], cal: dict) -> float | None:
    sc = [v for v in vals if not math.isnan(v)]
    return float(np.mean([bool(D.fires(v, cal)) for v in sc])) if sc else None


def d5_no_truncation(session: list) -> float:
    kept = [r for r in session if r.finish_reason != "length"]
    if not kept:
        return math.nan
    return D.d5_reasoning_share(kept).value


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--out-label", required=True)
    a = ap.parse_args()
    root = host_repo()
    camps = {}
    for spec in CAMPAIGNS:
        label, _, k = spec.partition(":")
        recs, _ = calibration_records(
            read_records(root / "results" / "raw" / "campaign" / label / "records.jsonl")
        )
        if k:
            recs = [r for r in recs if int(r.session_id.rsplit(":s", 1)[1]) < int(k)]
        camps[spec] = recs

    # ---- item 1: D3 by minimum session size, calibrated on the timeline
    tl = timeline_records(root / "benign" / a.benign_label / "timeline.jsonl")
    d3_b = [(D.d3_cadence(s).value, len(s)) for s in D.by_session(tl).values()]
    replay, _ = calibration_records(
        read_records(root / "results" / "raw" / "benign" / a.benign_label / "records.jsonl")
    )
    benign_sizes = [len(v) for v in D.by_session(replay).values() if len(v) >= D.MIN_SCOREABLE]
    d3: dict = {"calibration": {}, "campaigns": defaultdict(dict)}
    for k in (3, 5, 10):
        bvals = [v for v, n in d3_b if n >= k]
        cal = D.calibrate(bvals, "low", BUDGET)
        d3["calibration"][str(k)] = cal
        for spec, recs in camps.items():
            for rule in ("declared", "gap", "benign-sized"):
                sess = D.by_session(relabel(recs, rule, benign_sizes))
                cvals = [D.d3_cadence(s).value for s in sess.values() if len(s) >= k]
                d3["campaigns"][spec][f"{rule}:{k}"] = {
                    "n_units": len(cvals),
                    "flagged": frac_flagged(cvals, cal),
                    "median": float(np.nanmedian(cvals)) if cvals else None,
                    "auc": auc(cvals, bvals, "low"),
                }
    if abs(d3["calibration"]["3"]["threshold"] - 0.0226) > 2e-4:
        raise RuntimeError("registered D3 threshold not reproduced")

    # ---- item 2: D5 without truncated records, calibrated on the replay
    bsess = D.by_session(replay)
    d5_reg = [D.d5_reasoning_share(s).value for s in bsess.values()]
    d5_cln = [d5_no_truncation(s) for s in bsess.values()]
    cal_reg = D.calibrate(d5_reg, "high", BUDGET)
    cal_cln = D.calibrate(d5_cln, "high", BUDGET)
    if abs(cal_reg["threshold"] - 0.991) > 1e-3:
        raise RuntimeError("registered D5 threshold not reproduced")
    d5: dict = {
        "calibration_registered": cal_reg,
        "calibration_no_truncation": cal_cln,
        "benign_truncated_share": sum(r.finish_reason == "length" for r in replay) / len(replay),
        "campaigns": {},
    }
    for spec, recs in camps.items():
        csess = D.by_session(recs)
        v_reg = [D.d5_reasoning_share(s).value for s in csess.values()]
        v_cln = [d5_no_truncation(s) for s in csess.values()]
        d5["campaigns"][spec] = {
            "truncated_share": sum(r.finish_reason == "length" for r in recs) / len(recs),
            "registered": {
                "flagged": frac_flagged(v_reg, cal_reg),
                "median": float(np.nanmedian(v_reg)),
                "auc": auc(v_reg, d5_reg, "high"),
            },
            "no_truncation": {
                "flagged": frac_flagged(v_cln, cal_cln),
                "median": float(np.nanmedian(v_cln)),
                "auc": auc(v_cln, d5_cln, "high"),
            },
        }
    p37 = all(
        (d3["campaigns"][spec][f"{rule}:{k}"]["flagged"] or 0.0) == 0.0
        for spec in camps
        for rule in ("declared", "gap", "benign-sized")
        for k in (5, 10)
    )
    bench = d5["campaigns"]["pilot_baseline"]
    p38 = (
        cal_cln["threshold"] < cal_reg["threshold"]
        and bench["no_truncation"]["flagged"] >= 0.10
        and all(
            d5["campaigns"][s]["no_truncation"]["flagged"] == 0.0
            for s in ("c_real_v2:20", "c_real_v2_s1")
        )
    )
    out = {"D3": d3, "D5": d5, "p37": p37, "p38": p38}
    out_dir = root / "results" / "aggregates" / "m6" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "thresholds.json").write_text(json.dumps(out, indent=1, default=float))
    md = [
        "D3 by minimum session size (timeline calibration): "
        + "; ".join(
            f"min {k}: threshold {c['threshold']:.4g} on {c['n_benign']:,} sessions"
            for k, c in d3["calibration"].items()
        )
        + f". P37 {'holds' if p37 else 'fails'}.",
        "| Campaign | Sessions | min 3 flagged (AUC) | min 5 flagged (AUC) | min 10 flagged (AUC) |",
        "|---|---|---|---|---|",
    ]
    for spec in camps:
        for rule in ("declared", "gap", "benign-sized"):
            cells = []
            for k in (3, 5, 10):
                r = d3["campaigns"][spec][f"{rule}:{k}"]
                cells.append(
                    f"{'n/a' if r['flagged'] is None else format(r['flagged'], '.2f')} ({'n/a' if r['auc'] is None else format(r['auc'], '.2f')}; n {r['n_units']})"
                )
            md.append(f"| {spec} | {rule} | " + " | ".join(cells) + " |")
    md += [
        "",
        f"D5: registered threshold {cal_reg['threshold']:.4g}; without truncated records {cal_cln['threshold']:.4g} "
        f"(benign truncated share {d5['benign_truncated_share']:.2%}). P38 {'holds' if p38 else 'fails'}.",
        "| Campaign | Truncated share | Registered flagged (AUC) | No-truncation flagged (AUC) |",
        "|---|---|---|---|",
    ]
    for spec, r in d5["campaigns"].items():
        md.append(
            f"| {spec} | {r['truncated_share']:.2%} | {r['registered']['flagged']:.2f} ({r['registered']['auc']:.2f}) | "
            f"{r['no_truncation']['flagged']:.2f} ({r['no_truncation']['auc']:.2f}) |"
        )
    (out_dir / "table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
