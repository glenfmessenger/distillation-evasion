#!/usr/bin/env python
"""Amendment B8 item 4: the replay-calibrated pattern detectors under three recalibrations.

(a) D5 (reasoning share) and D7 (cache share) calibrated on benign sessions of at least ten
    requests; campaigns scored with declared and size-matched sessions.
(b) D4 to D8b calibrated with the 120 constructed accounts (evaluation harness, batch
    summarisation, agent loops) removed from the replay; campaigns scored with declared sessions.
(c) Post hoc: a low-side threshold at 1% for D4, D6 and D7, campaigns scored with declared
    sessions.

Writes results/aggregates/m7/<out-label>/{recalibrate.json,table.md}.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict


from dev_harness.detectors import stats as D
from dev_harness.detectors.analysis import auc
from dev_harness.paths import host_repo
from dev_harness.writer import calibration_records, read_records

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from m6_thresholds import CAMPAIGNS, frac_flagged, relabel  # noqa: E402

BUDGET = 0.01
REPLAY_DETS = ("D4", "D5", "D6", "D7", "D8", "D8b")
REAL_PREFIXES = ("b:conv:", "b:code:")


def stats_by_det(records, ref, min_session: int = 0) -> dict[str, list[float]]:
    out: dict[str, list[float]] = defaultdict(list)
    for s in D.all_statistics(records, ref):
        if s.detector_id in REPLAY_DETS:
            if D.GRAIN[s.detector_id] == "session" and s.n_records < min_session:
                continue
            out[s.detector_id].append(s.value)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--out-label", required=True)
    a = ap.parse_args()
    root = host_repo()
    replay, _ = calibration_records(
        read_records(root / "results" / "raw" / "benign" / a.benign_label / "records.jsonl")
    )
    real = [r for r in replay if r.identity_id.startswith(REAL_PREFIXES)]
    n_constructed = len({r.identity_id for r in replay}) - len({r.identity_id for r in real})
    camps = {}
    for spec in CAMPAIGNS:
        label, _, k = spec.partition(":")
        recs, _ = calibration_records(
            read_records(root / "results" / "raw" / "campaign" / label / "records.jsonl")
        )
        if k:
            recs = [r for r in recs if int(r.session_id.rsplit(":s", 1)[1]) < int(k)]
        camps[spec] = recs
    benign_sizes = [len(v) for v in D.by_session(replay).values() if len(v) >= D.MIN_SCOREABLE]
    ref_all = D.BenignReference.fit(replay)
    ref_real = D.BenignReference.fit(real)
    out: dict = {
        "n_constructed_accounts_removed": n_constructed,
        "registered": {},
        "min_ten": {},
        "no_constructed": {},
        "low_side": {},
    }

    # registered (reproduction check) and (a) min-ten sessions
    b_all = stats_by_det(replay, ref_all)
    b_ten = stats_by_det(replay, ref_all, min_session=10)
    b_real = stats_by_det(real, ref_real)
    for det in REPLAY_DETS:
        direction = D.DIRECTION[det]
        cal_reg = D.calibrate(b_all[det], direction, BUDGET)
        out["registered"][det] = {
            "threshold": cal_reg["threshold"],
            "n_benign": cal_reg["n_benign"],
            "campaigns": {},
        }
        cal_ten = D.calibrate(b_ten[det], direction, BUDGET) if det in ("D5", "D7") else None
        if cal_ten:
            out["min_ten"][det] = {
                "threshold": cal_ten["threshold"],
                "n_benign": cal_ten["n_benign"],
                "campaigns": {},
            }
        cal_real = D.calibrate(b_real[det], direction, BUDGET)
        out["no_constructed"][det] = {
            "threshold": cal_real["threshold"],
            "n_benign": cal_real["n_benign"],
            "campaigns": {},
        }
        if det in ("D4", "D6", "D7"):
            low = D.calibrate(b_all[det], "low", BUDGET)
            out["low_side"][det] = {
                "threshold": low["threshold"],
                "n_exceed": low["n_exceed"],
                "campaigns": {},
            }
        for spec, recs in camps.items():
            c_all = stats_by_det(recs, ref_all)
            out["registered"][det]["campaigns"][spec] = {
                "flagged": frac_flagged(c_all[det], cal_reg),
                "auc": auc(c_all[det], b_all[det], direction),
            }
            if cal_ten:
                res = {}
                for rule in ("declared", "benign-sized"):
                    cv = stats_by_det(relabel(recs, rule, benign_sizes), ref_all, min_session=10)
                    res[rule] = {
                        "flagged": frac_flagged(cv[det], cal_ten),
                        "auc": auc(cv[det], b_ten[det], direction),
                        "n_units": len(cv[det]),
                    }
                out["min_ten"][det]["campaigns"][spec] = res
            c_real = stats_by_det(recs, ref_real)
            out["no_constructed"][det]["campaigns"][spec] = {
                "flagged": frac_flagged(c_real[det], cal_real),
                "auc": auc(c_real[det], b_real[det], direction),
            }
            if det in ("D4", "D6", "D7"):
                c_sized = stats_by_det(relabel(recs, "benign-sized", benign_sizes), ref_all)
                out["low_side"][det]["campaigns"][spec] = {
                    "flagged": frac_flagged(c_all[det], low),
                    "flagged_size_matched": frac_flagged(c_sized[det], low),
                }
    reg_thr = {"D4": 0.8701, "D5": 0.9909, "D6": 0.8403, "D7": 0.8085, "D8": 0.811}
    for det, thr in reg_thr.items():
        if abs(out["registered"][det]["threshold"] - thr) > 2e-3:
            raise RuntimeError(
                f"{det}: registered threshold not reproduced: {out['registered'][det]['threshold']}"
            )
    worst = 0.0
    for block in ("min_ten", "no_constructed"):
        for det, r in out[block].items():
            for spec, c in r["campaigns"].items():
                vals = [c["flagged"]] if "flagged" in c else [v["flagged"] for v in c.values()]
                worst = max(worst, max(v for v in vals if v is not None))
    out["p46"] = {"max_flagged": worst, "holds": worst <= 0.10}
    d4low = out["low_side"]["D4"]["campaigns"]["c_real_v2:20"]["flagged"]
    out["p47"] = {"d4_low_flagged_c_real": d4low, "holds": d4low is not None and d4low >= 0.5}
    out_dir = root / "results" / "aggregates" / "m7" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "recalibrate.json").write_text(json.dumps(out, indent=1, default=float))
    md = [
        f"Replay-calibrated detectors recalibrated (B8 item 4); {n_constructed} constructed accounts removed in (b). P46 {'holds' if out['p46']['holds'] else 'fails'} (max flagged {worst:.2f}); P47 {'holds' if out['p47']['holds'] else 'fails'} (D4 low-side on C-real {d4low}).",
        "| Detector | Registered thr | Min-10 thr | No-constructed thr | Low-side thr | "
        + " | ".join(CAMPAIGNS)
        + " |",
        "|---|---|---|---|---|" + "---|" * len(CAMPAIGNS),
    ]
    for det in REPLAY_DETS:
        cells = []
        for spec in CAMPAIGNS:
            r = out["registered"][det]["campaigns"][spec]
            t = out["min_ten"].get(det, {}).get("campaigns", {}).get(spec)
            nc = out["no_constructed"][det]["campaigns"][spec]
            lo = out["low_side"].get(det, {}).get("campaigns", {}).get(spec)
            cells.append(
                f"reg {r['flagged']:.2f}; min10 {'--' if not t else format(t['declared']['flagged'] if t['declared']['flagged'] is not None else -1, '.2f') + '/' + format(t['benign-sized']['flagged'] if t['benign-sized']['flagged'] is not None else -1, '.2f')}; noc {nc['flagged']:.2f}; low {'--' if not lo else format(lo['flagged'], '.2f') + '/' + format(lo['flagged_size_matched'], '.2f')}"
            )
        md.append(
            f"| {det} | {out['registered'][det]['threshold']:.4g} | {out['min_ten'].get(det, {}).get('threshold', float('nan')):.4g} | {out['no_constructed'][det]['threshold']:.4g} | {out['low_side'].get(det, {}).get('threshold', float('nan')):.4g} | "
            + " | ".join(cells)
            + " |"
        )
    (out_dir / "table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
