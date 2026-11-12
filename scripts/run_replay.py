#!/usr/bin/env python
"""Replay a benign schedule against the local teacher (PROTOCOL §4). Thinking on, the teacher's
recommended sampling, and the SAME generation cap as the campaign (14,000; amendment A1), reduced
per request only when the prompt leaves less room in the 16,384-token context. Prompt length for
that sizing is measured with the tokenizer here; it is never written to a record (records carry
server-reported counts only). Usage: run_replay.py --schedule S --label L --base-url U [--concurrency N]
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from pathlib import Path

from transformers import AutoTokenizer

from dev_harness.benign import read_schedule
from dev_harness.client import ChatClient, Sampling
from dev_harness.paths import host_repo
from dev_harness.replay import replay
from dev_harness.writer import RecordWriter

CAP, CONTEXT, MARGIN, MIN_ROOM = 14000, 16384, 32, 512


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schedule", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--base-url", default="http://127.0.0.1:8001")
    ap.add_argument("--model", default="Qwen/Qwen3-8B")
    ap.add_argument("--concurrency", type=int, default=64)
    a = ap.parse_args()
    sched = read_schedule(Path(a.schedule))
    tok = AutoTokenizer.from_pretrained(a.model)
    lock = threading.Lock()

    def sampling_fn(messages):
        with lock:
            n = len(
                tok(tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True))[
                    "input_ids"
                ]
            )
        room = CONTEXT - n - MARGIN
        if room < MIN_ROOM:
            return None
        return Sampling(temperature=0.6, top_p=0.95, top_k=20, max_tokens=min(CAP, room))

    out = host_repo() / "results" / "raw" / "benign" / a.label
    out.mkdir(parents=True, exist_ok=True)
    if (out / "records.jsonl").exists():
        raise RuntimeError(
            f"{out}/records.jsonl exists; choose a new label rather than appending to a finished replay"
        )
    writer = RecordWriter(out / "records.jsonl")
    client = ChatClient(a.base_url, a.model, writer, timeout=1800.0)
    t0 = time.time()

    def progress(n, total, stats):
        print(
            f"{n}/{total} sessions, {stats['completed']} requests done, failed={stats['failed']} "
            f"too_long={stats['requests_too_long']} {round(time.time() - t0)}s",
            flush=True,
        )

    stats = replay(
        sched, client, f"benign:{a.label}", Sampling(), a.concurrency, progress, sampling_fn
    )
    writer.close()
    stats.update(
        {
            "label": a.label,
            "schedule": a.schedule,
            "seconds": round(time.time() - t0),
            "cap": CAP,
            "context": CONTEXT,
            "concurrency": a.concurrency,
            "model": a.model,
        }
    )
    (out / "manifest.json").write_text(json.dumps(stats, indent=1))
    print("REPLAY_DONE", json.dumps(stats))
    return 0


if __name__ == "__main__":
    sys.exit(main())
