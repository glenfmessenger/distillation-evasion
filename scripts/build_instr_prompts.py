#!/usr/bin/env python
"""C-instr prompt file (PROTOCOL v2.0 amendment B1 item 7): prompts from a public instruction
corpus not derived from chat logs (databricks/databricks-dolly-15k): the instruction, plus its
context when present, as a user would paste it. Exact-deduplicated; no 13-gram in common with
any benign replay prompt. Same output format as build_real_prompts.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter

from dev_harness.benign import read_schedule
from dev_harness.paths import host_repo
from dev_harness.pool import ngrams

SOURCE = "databricks/databricks-dolly-15k"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    root = host_repo()
    from datasets import load_dataset

    ds = load_dataset(SOURCE, split="train")
    grams = set()
    for r in read_schedule(root / "benign" / a.benign_label / "replay_schedule.jsonl"):
        grams |= ngrams(r.user_content, 13)
    seen, cands = set(), []
    counts = {"rows": 0, "dropped_duplicate": 0, "dropped_ngram_overlap": 0}
    for i, r in enumerate(ds):
        counts["rows"] += 1
        text = r["instruction"].strip()
        if r.get("context"):
            text = f"{text}\n\n{r['context'].strip()}"
        if text in seen:
            counts["dropped_duplicate"] += 1
            continue
        seen.add(text)
        if grams & ngrams(text, 13):
            counts["dropped_ngram_overlap"] += 1
            continue
        cands.append({"id": f"dolly:{i}", "text": text, "category": r.get("category")})
    counts["candidates"] = len(cands)
    if len(cands) < a.n:
        raise RuntimeError(f"only {len(cands)} candidates, need {a.n}")
    rng = random.Random(a.seed)
    chosen = rng.sample(cands, a.n)
    rng.shuffle(chosen)
    out = root / "campaign_prompts" / a.label
    out.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    with (out / "prompts.jsonl").open("w", encoding="utf-8") as fh:
        for d in chosen:
            line = (
                json.dumps(
                    {
                        "id": d["id"],
                        "source": SOURCE,
                        "messages": [{"role": "user", "content": d["text"]}],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            fh.write(line)
            h.update(line.encode())
    manifest = {
        "label": a.label,
        "source": SOURCE,
        "n": a.n,
        "seed": a.seed,
        "counts": counts,
        "categories": dict(sorted(Counter(d["category"] for d in chosen).items())),
        "prompts_sha256": h.hexdigest(),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(json.dumps(manifest, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
