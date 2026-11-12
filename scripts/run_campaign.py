#!/usr/bin/env python
"""Issue a distillation campaign against the local teacher and record (prompt, reasoning, answer)
pairs plus one RequestRecord per request (PROTOCOL §3; PLAN M2 step 3).

Pilot/baseline policy: a fixed, seeded, stratified sample of pool prompts, ONE identity, sessions
of `--session-size` consecutive requests, issued as fast as `--concurrency` allows. No evasion
lever is applied here; levers are separate policies added in M4. Selection ids are written to a
manifest so every arm's data is reproducible from the pool hash.

Outputs under $HARNESS_HOST_REPO/results/raw/campaign/<label>/: pairs.jsonl, records.jsonl,
manifest.json. Only pool prompts, or the prompts of a committed prompt file (--prompt-file,
PROTOCOL v2.0 C-real), are ever sent; the endpoint is the local teacher.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from dev_harness.client import ChatClient, Sampling
from dev_harness.paths import host_repo
from dev_harness.pool import read_jsonl
from dev_harness.prompts import chat_messages
from dev_harness.writer import RecordWriter

SAMPLING = Sampling(temperature=0.6, top_p=0.95, top_k=20, max_tokens=14000)
STRATA = {
    "EleutherAI/hendrycks_math": "math",
    "openai/gsm8k": "gsm8k",
    "codeparrot/apps": "apps",
    "google-research-datasets/mbpp": "mbpp",
}


@dataclass(frozen=True)
class _Prompt:
    """A prompt-file item: the message list is sent as given (no instruction suffix)."""

    id: str
    source: str
    messages: list
    verifier: str = "none"
    payload: dict = field(default_factory=dict)


def _messages(it) -> list[dict[str, str]]:
    return it.messages if isinstance(it, _Prompt) else chat_messages(it)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    ap.add_argument("--model", default="Qwen/Qwen3-8B")
    ap.add_argument("--label", required=True)
    ap.add_argument("--n-math", type=int, default=1000)
    ap.add_argument("--n-gsm8k", type=int, default=500)
    ap.add_argument("--n-apps", type=int, default=400)
    ap.add_argument("--n-mbpp", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--identity", default="campaign-0")
    ap.add_argument("--session-size", type=int, default=100)
    ap.add_argument("--concurrency", type=int, default=32)
    ap.add_argument(
        "--prompt-file",
        default="",
        help="C-real: a prompts.jsonl from build_real_prompts.py, sent in file order; "
        "the pool strata arguments are ignored",
    )
    a = ap.parse_args()

    root = host_repo()
    if a.prompt_file:
        # one JSON object per "\n"-terminated line; str.splitlines would also split on
        # U+2028 and other separators that occur inside real user prompts (F45)
        with Path(a.prompt_file).open(encoding="utf-8") as fh:
            chosen = [_Prompt(**json.loads(line)) for line in fh if line.strip()]
        if not chosen:
            raise RuntimeError(f"{a.prompt_file}: empty")
        want = {"prompt_file": a.prompt_file, "n": len(chosen)}
    else:
        pool = read_jsonl(root / "pool" / "pool.jsonl")
        by = {k: [] for k in STRATA.values()}
        for it in pool:
            by[STRATA[it.source]].append(it)
        rng = random.Random(a.seed)
        want = {"math": a.n_math, "gsm8k": a.n_gsm8k, "apps": a.n_apps, "mbpp": a.n_mbpp}
        chosen = []
        for k, n in want.items():
            if n > len(by[k]):
                raise RuntimeError(f"stratum {k}: asked {n}, pool has {len(by[k])}")
            chosen += rng.sample(by[k], n)
        rng.shuffle(chosen)

    out = root / "results" / "raw" / "campaign" / a.label
    out.mkdir(parents=True, exist_ok=True)
    already: set[str] = set()
    if (out / "pairs.jsonl").exists():  # resume: completed pairs are kept, the rest re-issued
        for line in (out / "pairs.jsonl").read_text().splitlines():
            d = json.loads(line)
            if "content" in d:
                already.add(d["id"])
        print(f"resuming: {len(already)} pairs already completed", flush=True)
    (out / "manifest.json").write_text(
        json.dumps(
            {
                "label": a.label,
                "seed": a.seed,
                "strata": want,
                "identity": a.identity,
                "session_size": a.session_size,
                "sampling": SAMPLING.__dict__,
                "model": a.model,
                "ids": [it.id for it in chosen],
                "started": time.time(),
            },
            indent=1,
        )
    )
    writer = RecordWriter(out / "records.jsonl")
    client = ChatClient(a.base_url, a.model, writer)
    pairs = (out / "pairs.jsonl").open("a")
    lock = threading.Lock()
    stats = {"done": 0, "length": 0, "errors": 0}

    def one(idx_item):
        idx, it = idx_item
        if it.id in already:
            return
        sess = f"{a.identity}:s{idx // a.session_size}"
        try:
            comp = client.send(
                run_id=f"campaign:{a.label}",
                identity_id=a.identity,
                session_id=sess,
                request_index=idx % a.session_size,
                arm=f"campaign:{a.label}",
                messages=_messages(it),
                sampling=SAMPLING,
            )
        except Exception as e:  # noqa: BLE001 - counted, never silently dropped
            with lock:
                stats["errors"] += 1
                pairs.write(json.dumps({"id": it.id, "error": repr(e)}) + "\n")
            return
        with lock:
            stats["done"] += 1
            stats["length"] += comp.record.finish_reason == "length"
            pairs.write(
                json.dumps(
                    {
                        "id": it.id,
                        "source": it.source,
                        "verifier": it.verifier,
                        "payload": it.payload,
                        "messages": _messages(it),
                        "reasoning": comp.reasoning,
                        "content": comp.content,
                        "finish": comp.record.finish_reason,
                        "prompt_tokens": comp.record.prompt_tokens,
                        "generated_tokens": comp.record.generated_tokens,
                        "reasoning_tokens": comp.record.reasoning_tokens,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            if stats["done"] % 100 == 0:
                print(
                    f"{stats['done']}/{len(chosen)} done, length={stats['length']}, errors={stats['errors']}",
                    flush=True,
                )

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=a.concurrency) as ex:
        list(ex.map(one, enumerate(chosen)))
    pairs.close()
    writer.close()
    m = json.loads((out / "manifest.json").read_text())
    m.update({"finished": time.time(), "seconds": round(time.time() - t0), **stats})
    (out / "manifest.json").write_text(json.dumps(m, indent=1))
    print(f"campaign {a.label}: {stats} in {m['seconds']}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
