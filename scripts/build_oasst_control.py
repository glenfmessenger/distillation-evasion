#!/usr/bin/env python
"""Amendment B8 item 7: an out-of-corpus benign prompt sample.

Three thousand English first user turns of the public OpenAssistant conversations (oasst1,
Apache-2.0), sampled with a seed, written as a control prompt file in the campaign prompt
format. Prompts only; nothing is sent to any model here.

Writes $HARNESS_HOST_REPO/campaign_prompts/oasst_ctrl/{prompts.jsonl,manifest.json}.
"""

from __future__ import annotations

import argparse
import json
import random
import sys

from dev_harness.paths import host_repo


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    import pandas as pd
    from huggingface_hub import hf_hub_download

    path = hf_hub_download(
        "OpenAssistant/oasst1",
        "data/train-00000-of-00001-b42a775f407cee45.parquet",
        repo_type="dataset",
    )
    df = pd.read_parquet(path)
    first = df[(df["role"] == "prompter") & (df["parent_id"].isna()) & (df["lang"] == "en")]
    texts = sorted(set(first["text"].tolist()))
    if len(texts) < a.n:
        raise RuntimeError(f"only {len(texts)} English first turns, need {a.n}")
    rng = random.Random(a.seed)
    chosen = rng.sample(texts, a.n)
    rng.shuffle(chosen)
    out_dir = host_repo() / "campaign_prompts" / "oasst_ctrl"
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "prompts.jsonl").open("w", encoding="utf-8") as fh:
        for t in chosen:
            fh.write(json.dumps({"messages": [{"role": "user", "content": t}]}) + "\n")
    man = {
        "source": "OpenAssistant/oasst1 train split, English first prompter turns, de-duplicated",
        "n_candidates": len(texts),
        "n": a.n,
        "seed": a.seed,
        "parquet": path.rsplit("/", 1)[-1],
    }
    (out_dir / "manifest.json").write_text(json.dumps(man, indent=1))
    print(json.dumps(man))
    return 0


if __name__ == "__main__":
    sys.exit(main())
