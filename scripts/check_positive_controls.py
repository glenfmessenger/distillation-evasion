#!/usr/bin/env python
"""Positive controls (F65): for every content-blind detector, a synthetic unit built to exceed
its registered threshold by a wide margin must be flagged by the calibrated pipeline. A detector
whose positive control is not flagged is reported; nothing is defaulted. Uses the committed
calibration in docs/evidence (m3_c_real.json) and the detector functions themselves.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from dev_harness.detectors import stats as D
from dev_harness.records import RequestRecord

EV = Path(__file__).resolve().parents[1] / "docs" / "evidence" / "m4" / "m3_c_real.json"
NS = 1_000_000_000


def rec(i, t_s, prompt=100, gen=200, reasoning=0, cached=0, turns=1, sess="s0"):
    t = int(t_s * NS)
    return RequestRecord(
        run_id="pc",
        identity_id="pc",
        session_id=f"pc:{sess}",
        request_index_in_session=i,
        arm="pc",
        t_send_ns=t,
        t_sched_ns=t,
        t_first_byte_ns=t,
        t_done_ns=t,
        prompt_tokens=prompt,
        generated_tokens=gen,
        total_tokens=prompt + gen,
        reasoning_tokens=reasoning,
        cached_prompt_tokens=cached,
        turn_count=turns,
        finish_reason="stop",
        http_status=200,
        in_flight=False,
        source_fields={
            k: "server:usage"
            for k in (
                "prompt_tokens",
                "generated_tokens",
                "total_tokens",
                "reasoning_tokens",
                "cached_prompt_tokens",
            )
        },
    )


def main() -> int:
    cal = {
        det: v["populations"]["campaign"]["budgets"]["0.01"]
        for det, v in json.loads(EV.read_text())["detectors"].items()
    }
    results = {}
    # D1: 1,000 requests in one hour (threshold 26)
    results["D1"] = D.d1_rate([rec(i, i * 3.0) for i in range(1000)]).value
    # D2: 200 sessions in one day (threshold 48)
    results["D2"] = D.d2_sessions_per_day(
        [rec(0, k * 400.0, sess=f"s{k}") for k in range(200)]
    ).value
    # D3: perfectly regular cadence (threshold CV 0.0226, direction low)
    results["D3"] = D.d3_cadence([rec(i, i * 10.0) for i in range(50)]).value
    # D5: reasoning share 1.0 (threshold 0.991)
    results["D5"] = D.d5_reasoning_share(
        [rec(i, i * 10.0, gen=200, reasoning=200) for i in range(30)]
    ).value
    # D7: cache share 1.0 (threshold 0.8085)
    results["D7"] = D.d7_cache_share(
        [rec(i, i * 10.0, prompt=100, cached=100) for i in range(30)]
    ).value
    # D9: all single-turn (threshold 1.0; registered as unscoreable since benign 99th percentile is 1.0)
    results["D9"] = D.d9_single_turn([rec(i, i * 10.0, turns=1) for i in range(30)]).value
    out = {}
    for det, v in results.items():
        c = cal[det]
        fired = D.fires(v, c)
        out[det] = {
            "value": v,
            "threshold": c["threshold"],
            "direction": c["direction"],
            "fired": fired,
        }
        print(
            f"{det}: value {v:.4g} threshold {c['threshold']:.4g} ({c['direction']}) -> {'FLAGGED' if fired else 'NOT FLAGGED'}"
        )
    # D4, D6, D8 need the benign reference distributions (replay records), which are not in docs/evidence; they are checked in the node-side table by construction (campaign KS vs pooled).
    print(
        "D4, D6, D8: need the replay reference; covered by the shape tests in tests/ and by the C-bench D5/D8 AUC > 0.9 rows (rank order works; thresholds are benign-set)."
    )
    missing = [d for d, r in out.items() if not r["fired"] and d != "D9"]
    print("positive controls not flagged (excluding D9, unscoreable by design):", missing or "none")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
