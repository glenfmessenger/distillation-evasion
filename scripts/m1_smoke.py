#!/usr/bin/env python
"""M1 smoke: prove the server populates reasoning_tokens and cached_tokens per request.

Sends the same long-prefix thinking request twice through ChatClient and asserts:
  - usage present, token identity holds (client raises otherwise),
  - reasoning_tokens is not None and > 0 on a thinking request,
  - cached_tokens is not None and, on the second request, > 0 (prefix cache hit).
Writes records to $HARNESS_HOST_REPO/results/raw/m1_smoke/records.jsonl and prints a summary.
Exit 1 on any failed assertion. Nothing here is a reportable number.
"""

from __future__ import annotations

import sys

from dev_harness.client import ChatClient, Sampling
from dev_harness.paths import raw_results_root
from dev_harness.writer import RecordWriter, read_records

PREFIX = ("You are a careful assistant. " * 40).strip()  # long shared prefix (> one cache block)


def main(base_url: str, model: str) -> int:
    out = raw_results_root() / "m1_smoke" / "records.jsonl"
    writer = RecordWriter(out)
    client = ChatClient(base_url, model, writer)
    msgs = [
        {"role": "system", "content": PREFIX},
        {"role": "user", "content": "What is 17 * 23? Think it through, then answer."},
    ]
    recs = []
    for i in range(2):
        comp = client.send(
            run_id="m1_smoke",
            identity_id="smoke",
            session_id="s0",
            request_index=i,
            arm="m1_smoke",
            messages=msgs,
            sampling=Sampling(max_tokens=1024),
        )
        recs.append(comp.record)
        print(
            f"req {i}: prompt={comp.record.prompt_tokens} gen={comp.record.generated_tokens} "
            f"reasoning={comp.record.reasoning_tokens} cached={comp.record.cached_prompt_tokens} "
            f"finish={comp.record.finish_reason} ttfb_ms={(comp.record.t_first_byte_ns - comp.record.t_send_ns) / 1e6:.0f}"
        )
    writer.close()
    failures = []
    if any(r.reasoning_tokens is None for r in recs):
        failures.append("reasoning_tokens is None (reasoning parser not configured?)")
    elif recs[0].reasoning_tokens == 0:
        failures.append("reasoning_tokens == 0 on a thinking request")
    if any(r.cached_prompt_tokens is None for r in recs):
        failures.append("cached_tokens is None (enable_prompt_tokens_details off?)")
    elif recs[1].cached_prompt_tokens == 0:
        failures.append("cached_tokens == 0 on the repeated-prefix request (prefix cache off?)")
    stored = read_records(out)
    if len(stored) != 2 or any(r.in_flight for r in stored):
        failures.append(
            f"stored records wrong: {len(stored)} records, in_flight={[r.in_flight for r in stored]}"
        )
    for f in failures:
        print("FAIL:", f)
    print("PASS" if not failures else "FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(
        main(
            sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000",
            sys.argv[2] if len(sys.argv) > 2 else "Qwen/Qwen3-8B",
        )
    )
