#!/usr/bin/env python
"""M3 analysis (PROTOCOL §5, §8; provisional amendment A3): calibrate every content-blind detector
on benign traffic and score a campaign against it. CPU only.

Benign sources: timeline.jsonl (all real users; D1, D2, D3, D9) and the replayed records (D4–D8).
Campaign: a campaign's records.jsonl. Campaign units: sessions for session-level detectors; for
identity-level detectors the whole identity AND each 100-request session treated as its own
identity (the view under identity splitting), reported separately.

Per detector and FPR budget the output gives: threshold, benign n and exceedances, the resolution
flag, the fraction of campaign units flagged, and the campaign-vs-benign AUC. Nothing is pooled
across detectors or budgets. Writes $HARNESS_HOST_REPO/results/aggregates/m3/<label>/
detectors.json, session_stats.jsonl (every unit's statistic, so budgets can be moved later) and
table.md. Usage: m3_analyse.py --benign-label m3_v1 --campaign-label pilot_baseline --out-label L
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict

import numpy as np

from dev_harness.detectors import stats as D
from dev_harness.paths import host_repo
from dev_harness.writer import calibration_records, read_records

from dev_harness.detectors.analysis import (
    BUDGETS,
    TIMELINE_DETECTORS,
    as_identity,
    auc,
    timeline_records,
    timeline_stats,
)

NS = 1_000_000_000


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--campaign-label", required=True)
    ap.add_argument("--out-label", required=True)
    ap.add_argument(
        "--allow-partial-replay",
        action="store_true",
        help="analyse a replay that is still running (output is marked partial)",
    )
    ap.add_argument(
        "--max-sessions", type=int, default=0, help="keep campaign sessions 0..k-1 (0 = all)"
    )
    ap.add_argument(
        "--campaign-sessions",
        choices=["declared", "gap", "benign-sized"],
        default="declared",
        help="B5: declared = client-declared blocks; gap = 1,800 s idle-gap rule on send times; "
        "benign-sized = consecutive sessions with sizes drawn from benign scoreable sessions",
    )
    a = ap.parse_args()
    root = host_repo()
    bdir = root / "results" / "raw" / "benign" / a.benign_label
    partial = not (bdir / "manifest.json").exists()
    if partial and not a.allow_partial_replay:
        raise RuntimeError(
            "benign replay has no manifest (still running?); pass --allow-partial-replay to peek"
        )
    benign, n_inflight_b = calibration_records(read_records(bdir / "records.jsonl"))
    camp_all = read_records(
        root / "results" / "raw" / "campaign" / a.campaign_label / "records.jsonl"
    )
    camp, n_inflight_c = calibration_records(camp_all)
    if a.max_sessions:
        camp = [r for r in camp if int(r.session_id.rsplit(":s", 1)[1]) < a.max_sessions]
        if not camp:
            raise RuntimeError("no campaign records after the session filter")
    if a.campaign_sessions != "declared":
        camp = sorted(camp, key=lambda r: r.t_send_ns)
        if a.campaign_sessions == "gap":
            sess, last, relabelled = 0, camp[0].t_send_ns, []
            for r in camp:
                if (r.t_send_ns - last) / NS > 1800.0:
                    sess += 1
                last = r.t_send_ns
                relabelled.append(r.model_copy(update={"session_id": f"{r.identity_id}:g{sess}"}))
        else:
            sizes = [len(v) for v in D.by_session(benign).values() if len(v) >= D.MIN_SCOREABLE]
            rng = np.random.default_rng(0)
            relabelled, sess, left = [], 0, int(rng.choice(sizes))
            for r in camp:
                if left == 0:
                    sess, left = sess + 1, int(rng.choice(sizes))
                relabelled.append(r.model_copy(update={"session_id": f"{r.identity_id}:b{sess}"}))
                left -= 1
        camp = relabelled
    ref = D.BenignReference.fit(benign)

    rows: dict[str, dict[str, list]] = defaultdict(
        lambda: defaultdict(list)
    )  # detector -> population -> stats
    for s in D.all_statistics(benign, ref):
        if s.detector_id not in TIMELINE_DETECTORS:
            rows[s.detector_id]["benign"].append(s)
    for s in timeline_stats(timeline_records(root / "benign" / a.benign_label / "timeline.jsonl")):
        rows[s.detector_id]["benign"].append(s)
    for s in D.all_statistics(camp, ref):
        rows[s.detector_id]["campaign"].append(s)
    for s in D.all_statistics(as_identity(camp), ref):
        if D.GRAIN[s.detector_id] == "identity":
            rows[s.detector_id]["campaign_split"].append(s)

    out_dir = root / "results" / "aggregates" / "m3" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "session_stats.jsonl").open("w") as fh:
        for det, pops in rows.items():
            for pop, lst in pops.items():
                for s in lst:
                    fh.write(
                        json.dumps(
                            {
                                "detector": det,
                                "population": pop,
                                "unit": s.session_id,
                                "identity": s.identity_id,
                                "value": None if math.isnan(s.value) else s.value,
                                "n_records": s.n_records,
                                "n_in_flight_excluded": s.n_excluded_in_flight,
                            }
                        )
                        + "\n"
                    )
    result = {
        "benign_label": a.benign_label,
        "campaign_label": a.campaign_label,
        "partial_replay": partial,
        "n_benign_replay_records": len(benign),
        "n_benign_in_flight_excluded": n_inflight_b,
        "n_campaign_records": len(camp),
        "n_campaign_in_flight_excluded": n_inflight_c,
        "detectors": {},
    }
    md = [
        "| Detector | Grain | Benign source | Benign scoreable | Budget | Threshold | Benign exceed | Below resolution | Campaign units | Flagged | Campaign median | AUC |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for det in sorted(rows):
        direction = D.DIRECTION[det]
        bvals = [s.value for s in rows[det]["benign"]]
        det_out = {
            "direction": direction,
            "grain": D.GRAIN[det],
            "benign_source": "timeline" if det in TIMELINE_DETECTORS else "replay",
            "populations": {},
        }
        for pop in ("campaign", "campaign_split"):
            if pop not in rows[det]:
                continue
            cvals = [s.value for s in rows[det][pop]]
            scored = [v for v in cvals if not math.isnan(v)]
            pop_out = {
                "n_units": len(cvals),
                "n_scoreable": len(scored),
                "median": float(np.median(scored)) if scored else None,
                "auc": auc(cvals, bvals, direction),
                "budgets": {},
            }
            for b in BUDGETS:
                cal = D.calibrate(bvals, direction, b)
                fl = [D.fires(v, cal) for v in scored]
                pop_out["budgets"][str(b)] = {
                    **cal,
                    "n_flagged": int(sum(bool(x) for x in fl)),
                    "frac_flagged": (sum(bool(x) for x in fl) / len(fl)) if fl else None,
                }
                r = pop_out["budgets"][str(b)]
                md.append(
                    f"| {det} | {D.GRAIN[det]}{' (split view)' if pop == 'campaign_split' else ''} | {det_out['benign_source']} | {cal['n_benign']} | {b:.1%} | {cal['threshold']:.4g} | {cal['n_exceed']} | {'yes' if cal['below_resolution'] else 'no'} | {len(scored)}/{len(cvals)} | "
                    f"{'n/a' if r['frac_flagged'] is None else format(r['frac_flagged'], '.2f')} | {'n/a' if pop_out['median'] is None else format(pop_out['median'], '.4g')} | {'n/a' if pop_out['auc'] is None else format(pop_out['auc'], '.3f')} |"
                )
            det_out["populations"][pop] = pop_out
        result["detectors"][det] = det_out
    (out_dir / "detectors.json").write_text(json.dumps(result, indent=1))
    header = (
        f"M3 detector table ({'PARTIAL replay, ' if partial else ''}benign `{a.benign_label}`, campaign `{a.campaign_label}`). "
        f"Per-cell; nothing pooled. Benign replay records {len(benign)} (in flight excluded: {n_inflight_b}); "
        f"campaign records {len(camp)} (in flight excluded: {n_inflight_c}).\n\n"
    )
    (out_dir / "table.md").write_text(header + "\n".join(md) + "\n")
    print(header + "\n".join(md))
    hot = [
        (d, p, v["auc"])
        for d, o in result["detectors"].items()
        for p, v in o["populations"].items()
        if v["auc"] is not None and v["auc"] >= 0.95
    ]
    if hot:
        print("\nTOO-GOOD STOP RULE: AUC >= 0.95 for", hot)
    return 0


if __name__ == "__main__":
    sys.exit(main())
