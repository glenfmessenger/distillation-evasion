#!/usr/bin/env python
"""Score a served model on the capability suites (PROTOCOL §2).

Usage: score_suite.py --base-url URL --model NAME --mode chat|completion --label LABEL
                      [--suites math500,gsm8k_test,humaneval,mbpp_test] [--k 4] [--concurrency 48]
                      [--limit N]   (limit is for smoke only and is recorded in the summary)
Writes $HARNESS_HOST_REPO/results/raw/scores/<label>/<suite>.jsonl (every sample, raw text,
verdict) and summary.json (pass@1 mean with BCa CI per suite). Records for every request go to
records.jsonl via the write-ahead writer, so in-flight requests are marked if the run dies.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

from dev_harness.client import ChatClient, Sampling
from dev_harness.paths import host_repo
from dev_harness.pool import Item, read_jsonl
from dev_harness.prompts import chat_messages, completion_prompt
from dev_harness.stats import mean_bca_ci
from dev_harness.verify import verify_item
from dev_harness.writer import RecordWriter

SAMPLING = Sampling(temperature=0.6, top_p=0.95, top_k=20, max_tokens=14000)


def few_shots(suite: str, pool_dir: Path) -> list[Item]:
    """Fixed few-shot exemplars from TRAIN splits (never from the suite being scored).
    MATH exemplars need worked solutions, which the pool does not carry, so they are taken
    directly from the first train items of EleutherAI/hendrycks_math (algebra) with a boxed answer."""
    if suite == "math500":
        from datasets import load_dataset

        from dev_harness.pool import _boxed

        ds = load_dataset("EleutherAI/hendrycks_math", "algebra", split="train")
        out = []
        for i, r in enumerate(ds):
            if _boxed(r["solution"]) is not None and len(r["solution"]) < 800:
                out.append(
                    Item(
                        f"math_shot:{i}",
                        "EleutherAI/hendrycks_math",
                        "math",
                        r["problem"],
                        "math_boxed",
                        {"answer": _boxed(r["solution"]), "solution": r["solution"]},
                    )
                )
            if len(out) == 4:
                break
        return out
    pool = read_jsonl(pool_dir / "pool.jsonl")
    if suite == "gsm8k_test":
        return [it for it in pool if it.source == "openai/gsm8k"][:4]
    if suite == "mbpp_test":
        return [it for it in pool if it.source == "google-research-datasets/mbpp"][:3]
    return []


def completion_call(
    base_url: str, model: str, prompt: str, stop: list[str], max_tokens: int, seed: int
) -> dict:
    body = {
        "model": model,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": SAMPLING.temperature,
        "top_p": SAMPLING.top_p,
        "top_k": SAMPLING.top_k,
        "stop": stop,
        "seed": seed,
    }
    r = httpx.post(f"{base_url}/v1/completions", json=body, timeout=600)
    r.raise_for_status()
    d = r.json()
    if "usage" not in d:
        raise RuntimeError("no usage in completion response")
    return {
        "text": d["choices"][0]["text"],
        "finish_reason": d["choices"][0]["finish_reason"],
        "usage": d["usage"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    ap.add_argument("--model", required=True)
    ap.add_argument("--mode", choices=["chat", "completion"], required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--suites", default="math500,gsm8k_test,humaneval,mbpp_test")
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--concurrency", type=int, default=48)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    root = host_repo()
    pool_dir = root / "pool"
    out_dir = root / "results" / "raw" / "scores" / a.label
    out_dir.mkdir(parents=True, exist_ok=True)
    writer = RecordWriter(out_dir / "records.jsonl")
    client = ChatClient(a.base_url, a.model, writer, sticky="session")
    lock = threading.Lock()
    summary = {
        "label": a.label,
        "model": a.model,
        "mode": a.mode,
        "k": a.k,
        "limit": a.limit,
        "sampling": SAMPLING.__dict__,
        "suites": {},
        "started": time.time(),
    }

    for suite in a.suites.split(","):
        items = read_jsonl(pool_dir / "suites" / f"{suite}.jsonl")
        if a.limit:
            items = items[: a.limit]
        shots = few_shots(suite, pool_dir) if a.mode == "completion" else []
        if a.mode == "completion" and suite != "humaneval" and not shots:
            raise RuntimeError(f"no few-shot exemplars found for {suite}")
        per_item: dict[str, list[int]] = {it.id: [] for it in items}
        done: set[tuple[str, int]] = set()
        n_len, n_err = 0, 0
        out_path = out_dir / f"{suite}.jsonl"
        if out_path.exists():  # resume: keep completed samples, redo only missing ones
            for line in out_path.read_text().splitlines():
                d = json.loads(line)
                if "ok" in d and d["id"] in per_item:
                    per_item[d["id"]].append(int(d["ok"]))
                    done.add((d["id"], d["sample"]))
                    n_len += d.get("finish") == "length"
            print(f"{suite}: resuming, {len(done)} samples already scored", flush=True)
        fh = out_path.open("a")

        def one(job):
            nonlocal n_len, n_err
            it, s = job
            try:
                if a.mode == "chat":
                    comp = client.send(
                        run_id=f"score:{a.label}",
                        identity_id=f"score:{a.label}",
                        session_id=f"{suite}:{it.id}",
                        request_index=s,
                        arm=f"score:{a.label}",
                        messages=chat_messages(it),
                        sampling=SAMPLING,
                    )
                    text, finish, reasoning = (
                        comp.content,
                        comp.record.finish_reason,
                        comp.reasoning,
                    )
                    usage = {
                        "prompt": comp.record.prompt_tokens,
                        "gen": comp.record.generated_tokens,
                        "reasoning": comp.record.reasoning_tokens,
                    }
                else:
                    prompt, stop, mt = completion_prompt(it, shots)
                    r = completion_call(client.base_urls[0], a.model, prompt, stop, mt, seed=s)
                    text, finish, reasoning, usage = r["text"], r["finish_reason"], None, r["usage"]
                ok = verify_item(it.verifier, it.payload, text, it.prompt, a.mode == "completion")
            except Exception as e:  # noqa: BLE001 - recorded as an error row, never as a silent 0
                with lock:
                    n_err += 1
                    fh.write(json.dumps({"id": it.id, "sample": s, "error": repr(e)}) + "\n")
                return
            with lock:
                per_item[it.id].append(int(ok))
                if finish == "length":
                    n_len += 1
                fh.write(
                    json.dumps(
                        {
                            "id": it.id,
                            "sample": s,
                            "ok": ok,
                            "finish": finish,
                            "usage": usage,
                            "text": text,
                            "reasoning": reasoning,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

        jobs = [(it, s) for it in items for s in range(a.k) if (it.id, s) not in done]
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=a.concurrency) as ex:
            list(ex.map(one, jobs))
        fh.close()
        scored = [sum(v) / len(v) for v in per_item.values() if v]
        if n_err:
            print(
                f"{suite}: {n_err} request errors (rows written with 'error'); items with no samples are excluded",
                file=sys.stderr,
            )
        ci = mean_bca_ci(scored, seed=0)
        summary["suites"][suite] = {
            "pass_at_1": ci,
            "n_items": len(items),
            "n_items_scored": len(scored),
            "n_samples": sum(len(v) for v in per_item.values()),
            "n_finish_length": n_len,
            "n_errors": n_err,
            "seconds": round(time.time() - t0),
        }
        print(
            f"{suite}: pass@1={ci['mean']:.4f} [{ci['lo']:.4f},{ci['hi']:.4f}] n={len(scored)} "
            f"len_trunc={n_len} err={n_err} {summary['suites'][suite]['seconds']}s",
            flush=True,
        )
        (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    writer.close()
    summary["finished"] = time.time()
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
