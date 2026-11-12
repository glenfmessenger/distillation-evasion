#!/usr/bin/env python
"""Amendment B6 item 5: what sits in the benign tails that set four thresholds.

(a) D5: finish reasons of the records in benign sessions above the reasoning-share threshold.
(b) D3: session sizes of benign sessions below the cadence threshold; the threshold recomputed
    with minimum session sizes 5 and 10.
(c) B2: replayed accounts whose every prompt shares an 8-token suffix with another, and the
    most common suffix of each.
(d) D1: descriptive quantiles of the accounts above the hourly-rate threshold.

Writes results/aggregates/m5/<out-label>/{tails.json,table.md}.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict

import numpy as np

from dev_harness.benign import read_schedule
from dev_harness.detectors import stats as D
from dev_harness.detectors.analysis import timeline_records
from dev_harness.paths import host_repo
from dev_harness.writer import calibration_records, read_records

BUDGET = 0.01


def q(v, ps=(10, 50, 90)) -> dict:
    v = np.asarray(v, dtype=float)
    return {str(p): float(np.percentile(v, p)) for p in ps} if v.size else {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--content-unit-stats", required=True)
    ap.add_argument("--out-label", required=True)
    ap.add_argument("--registered", default="", help="json {D3: thr, D5: thr} to check against")
    a = ap.parse_args()
    root = host_repo()
    out: dict = {}

    # (a) D5
    replay, _ = calibration_records(
        read_records(root / "results" / "raw" / "benign" / a.benign_label / "records.jsonl")
    )
    sessions = D.by_session(replay)
    d5 = {sid: D.d5_reasoning_share(s).value for sid, s in sessions.items()}
    cal5 = D.calibrate(list(d5.values()), "high", BUDGET)
    over = [sid for sid, v in d5.items() if not math.isnan(v) and D.fires(v, cal5)]
    recs_over = [r for sid in over for r in sessions[sid]]
    trunc_all = sum(r.finish_reason == "length" for r in replay) / len(replay)
    trunc_over = sum(r.finish_reason == "length" for r in recs_over) / len(recs_over)
    full_share = sum(
        1
        for r in recs_over
        if r.reasoning_tokens is not None
        and r.generated_tokens
        and r.reasoning_tokens >= r.generated_tokens
    ) / len(recs_over)
    out["D5"] = {
        "threshold": cal5["threshold"],
        "n_sessions_scoreable": cal5["n_benign"],
        "n_over": len(over),
        "n_records_over": len(recs_over),
        "truncated_share_replay": trunc_all,
        "truncated_share_over": trunc_over,
        "share_over_records_with_no_answer_tokens": full_share,
        "generated_tokens_over": q([r.generated_tokens for r in recs_over]),
        "generated_tokens_replay": q([r.generated_tokens for r in replay]),
        "session_sizes_over": Counter(len(sessions[sid]) for sid in over),
        "p35_fewer_than_half_truncated": trunc_over < 0.5,
    }

    # (b) D3
    tl = timeline_records(root / "benign" / a.benign_label / "timeline.jsonl")
    tsess = D.by_session(tl)
    d3 = {sid: (D.d3_cadence(s).value, len(s)) for sid, s in tsess.items()}
    vals = [v for v, _ in d3.values()]
    cal3 = D.calibrate(vals, "low", BUDGET)
    below = [(sid, n) for sid, (v, n) in d3.items() if not math.isnan(v) and D.fires(v, cal3)]
    size_hist = Counter(n for _, n in below)
    alt = {}
    for k in (5, 10):
        vk = [v for v, n in d3.values() if n >= k]
        alt[str(k)] = {**D.calibrate(vk, "low", BUDGET), "n_sessions": len(vk)}
    out["D3"] = {
        "threshold": cal3["threshold"],
        "n_sessions_scoreable": cal3["n_benign"],
        "n_below": len(below),
        "session_size_hist_below": dict(sorted(size_hist.items())),
        "share_below_with_three_requests": size_hist.get(3, 0) / len(below) if below else None,
        "share_scoreable_with_three_requests": sum(
            1 for v, n in d3.values() if not math.isnan(v) and n == 3
        )
        / cal3["n_benign"],
        "threshold_min_size": alt,
        "p34_at_least_half_size_three": (size_hist.get(3, 0) / len(below) >= 0.5)
        if below
        else None,
    }
    if a.registered:
        reg = json.loads(a.registered)
        for det, thr in reg.items():
            got = out[det]["threshold"]
            if not math.isclose(got, thr, rel_tol=2e-3):
                raise RuntimeError(
                    f"{det}: recomputed threshold {got} differs from registered {thr}"
                )

    # (c) B2
    rows = [json.loads(line) for line in open(a.content_unit_stats, encoding="utf-8")]
    ben = [r for r in rows if r["population"] == "benign" and r.get("B2") is not None]
    b2 = np.array([r["B2"] for r in ben])
    sched = read_schedule(root / "benign" / a.benign_label / "replay_schedule.jsonl")
    by_ident: dict[str, list[str]] = defaultdict(list)
    for r in sched:
        by_ident[r.identity_id].append(r.user_content)
    units = {i: v for i, v in by_ident.items() if len(v) >= 30}
    examples = []
    for i, v in units.items():
        if b2_full(v):
            suf = Counter(tuple(p.split()[-8:]) for p in v if len(p.split()) >= 8)
            top, cnt = suf.most_common(1)[0] if suf else ((), 0)
            examples.append(
                {
                    "n_prompts": len(v),
                    "top_suffix_share": cnt / len(v),
                    "top_suffix": " ".join(top)[:120],
                }
            )
    out["B2"] = {
        "n_benign_units": len(ben),
        "share_b2_equal_1": float(np.mean(b2 >= 1.0)),
        "share_b2_at_least_0.5": float(np.mean(b2 >= 0.5)),
        "n_units_full_reuse_recomputed": len(examples),
        "examples": sorted(examples, key=lambda e: -e["top_suffix_share"])[:10],
    }

    # (d) D1 tail
    by_acc = D.by_identity(tl)
    d1 = {acc: D.d1_rate(v).value for acc, v in by_acc.items()}
    cal1 = D.calibrate(list(d1.values()), "high", BUDGET)
    top = [acc for acc, v in d1.items() if D.fires(v, cal1)]

    def describe(accs):
        req, sess, st, cv, span = [], [], [], [], []
        for acc in accs:
            v = by_acc[acc]
            req.append(len(v))
            ss = D.by_session(v)
            sess.append(len(ss))
            st.append(np.mean([r.turn_count == 1 for r in v]))
            cvs = [D.d3_cadence(s).value for s in ss.values()]
            cvs = [c for c in cvs if not math.isnan(c)]
            if cvs:
                cv.append(float(np.median(cvs)))
            span.append((v[-1].t_sched_ns - v[0].t_sched_ns) / 1e9 / 86400)
        return {
            "n": len(accs),
            "requests": q(req),
            "sessions": q(sess),
            "single_turn_fraction": q(st),
            "median_cadence_cv": q(cv),
            "active_span_days": q(span),
        }

    out["D1"] = {
        "threshold": cal1["threshold"],
        "above": describe(top),
        "all": describe(list(by_acc)),
    }

    out_dir = root / "results" / "aggregates" / "m5" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "tails.json").write_text(json.dumps(out, indent=1, default=float))
    d5, d3s, b2o, d1o = out["D5"], out["D3"], out["B2"], out["D1"]
    md = [
        "Benign tails (B6 item 5).",
        f"- D5 threshold {d5['threshold']:.4g}: {d5['n_over']} sessions over, {d5['n_records_over']} records; truncated share {d5['truncated_share_over']:.2%} against {d5['truncated_share_replay']:.2%} replay-wide; records with no answer tokens {d5['share_over_records_with_no_answer_tokens']:.2%}; generated tokens over: {d5['generated_tokens_over']}; replay: {d5['generated_tokens_replay']}. P35 {'holds' if d5['p35_fewer_than_half_truncated'] else 'fails'}.",
        f"- D3 threshold {d3s['threshold']:.4g}: {d3s['n_below']} sessions below; size histogram {d3s['session_size_hist_below']}; share with three requests {d3s['share_below_with_three_requests']:.2%} (scoreable sessions with three requests: {d3s['share_scoreable_with_three_requests']:.2%}); threshold at min size 5: {d3s['threshold_min_size']['5']['threshold']:.4g} (n {d3s['threshold_min_size']['5']['n_sessions']}), at 10: {d3s['threshold_min_size']['10']['threshold']:.4g} (n {d3s['threshold_min_size']['10']['n_sessions']}). P34 {'holds' if d3s['p34_at_least_half_size_three'] else 'fails'}.",
        f"- B2: {b2o['share_b2_equal_1']:.2%} of {b2o['n_benign_units']} benign units have B2 = 1.0 and {b2o['share_b2_at_least_0.5']:.2%} have B2 >= 0.5; examples (top suffix share): "
        + "; ".join(
            f"{e['top_suffix_share']:.2f} '{e['top_suffix']}'" for e in b2o["examples"][:5]
        ),
        f"- D1 threshold {d1o['threshold']:.4g}: {d1o['above']['n']} accounts above. Above: {json.dumps(d1o['above'])}. All: {json.dumps(d1o['all'])}.",
    ]
    (out_dir / "table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


def b2_full(prompts: list[str]) -> bool:
    from dev_harness.detectors.content import b2_template_reuse

    return b2_template_reuse(prompts) >= 1.0


if __name__ == "__main__":
    sys.exit(main())
