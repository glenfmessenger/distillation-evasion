#!/usr/bin/env python
"""M1 truncation test (charter 3.7): prove in-flight marking by killing the client mid-run.

Mode 'run': start N long requests in threads and hard-exit the process after `kill_after_s`
seconds via os._exit, leaving stubs for whatever had not completed.
Mode 'check': read the records file; report completed vs in-flight counts; fail unless at least
one record is in flight (otherwise the test did not exercise the path) and the calibration loader
excludes exactly that many.
"""

from __future__ import annotations

import os
import sys
import threading
import time

from dev_harness.client import ChatClient, Sampling
from dev_harness.paths import raw_results_root
from dev_harness.writer import RecordWriter, calibration_records, read_records

OUT = "m1_truncation/records.jsonl"


def run(base_url: str, model: str, n: int, kill_after_s: float, n_short: int = 0) -> None:
    """n long requests plus n_short short ones (max_tokens=16, thinking off) so some complete
    before the kill; the check then proves completed records survive alongside stubs."""
    out = raw_results_root() / OUT
    if out.exists():
        out.unlink()
    writer = RecordWriter(out)
    client = ChatClient(base_url, model, writer)

    def one(i: int, short: bool) -> None:
        if short:
            prompt = f"Reply with the single word OK. ({i})"
            sampling = Sampling(
                max_tokens=16, extra_body={"chat_template_kwargs": {"enable_thinking": False}}
            )
        else:
            prompt = f"Write a very long essay number {i} about the history of mathematics, at least 3000 words."
            sampling = Sampling(max_tokens=4096)
        client.send(
            run_id="m1_trunc",
            identity_id=f"id{i}",
            session_id=f"s{i}",
            request_index=0,
            arm="m1_truncation",
            messages=[{"role": "user", "content": prompt}],
            sampling=sampling,
        )

    threads = []
    for i in range(n_short):
        threads.append(threading.Thread(target=one, args=(i, True), daemon=True))
    for i in range(n_short, n_short + n):
        threads.append(threading.Thread(target=one, args=(i, False), daemon=True))
    for t in threads:
        t.start()
    time.sleep(kill_after_s)
    print(
        f"hard exit after {kill_after_s}s with {n_short} short + {n} long requests started",
        flush=True,
    )
    os._exit(0)


def check() -> int:
    recs = read_records(raw_results_root() / OUT)
    kept, excluded = calibration_records(recs)
    print(f"records={len(recs)} completed={len(kept)} in_flight_excluded={excluded}")
    if excluded == 0:
        print("FAIL: no in-flight records; the kill did not interrupt anything")
        return 1
    if any(r.in_flight for r in kept):
        print("FAIL: an in-flight record reached the calibration set")
        return 1
    if len(kept) == 0:
        print(
            "FAIL: no completed records; the run did not show that completed records survive a kill"
        )
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    if sys.argv[1] == "run":
        run(
            sys.argv[2],
            sys.argv[3],
            int(sys.argv[4]),
            float(sys.argv[5]),
            int(sys.argv[6]) if len(sys.argv) > 6 else 0,
        )
    else:
        sys.exit(check())
