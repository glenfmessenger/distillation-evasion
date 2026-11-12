#!/usr/bin/env python
"""Build the benign replay schedule from WildChat-1M plus public multiple-choice sets for the
eval-harness component (PROTOCOL §4). CPU only. Writes $HARNESS_HOST_REPO/benign/<label>/
schedule.jsonl and manifest.json. Usage: build_benign.py --label L --n-identities N --files K --seed S
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

from datasets import load_dataset

from dev_harness.benign import BenignDataError, build_schedule, iter_wildchat, write_schedule
from dev_harness.paths import host_repo


def eval_prompts() -> list[str]:
    """Multiple-choice prompts an evaluation harness would send (not from the capability suites)."""
    out = []
    mm = load_dataset("cais/mmlu", "all", split="test")
    for r in mm:
        opts = "\n".join(f"{c}. {t}" for c, t in zip("ABCD", r["choices"]))
        out.append(f"{r['question']}\n{opts}\nAnswer with the letter of the correct option.")
    arc = load_dataset("allenai/ai2_arc", "ARC-Challenge", split="test")
    for r in arc:
        opts = "\n".join(f"{c}. {t}" for c, t in zip(r["choices"]["label"], r["choices"]["text"]))
        out.append(f"{r['question']}\n{opts}\nAnswer with the letter of the correct option.")
    if len(out) < 10000:
        raise BenignDataError(f"eval prompt pool unexpectedly small: {len(out)}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--n-identities", type=int, required=True)
    ap.add_argument("--files", type=int, default=14)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    root = host_repo()
    files = sorted(
        glob.glob(str(root / "hf/hub/datasets--allenai--WildChat-1M/snapshots/*/data/*.parquet"))
    )
    if len(files) < a.files:
        raise BenignDataError(f"found {len(files)} WildChat parquet files, need {a.files}")
    files = [Path(f) for f in files[: a.files]]
    sched, manifest = build_schedule(iter_wildchat(files), a.n_identities, a.seed, eval_prompts())
    out = root / "benign" / a.label
    manifest["schedule_sha256"] = write_schedule(sched, out / "schedule.jsonl")
    manifest["wildchat_files"] = [f.name for f in files]
    manifest["wildchat_snapshot"] = files[0].parts[-3]
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(
        json.dumps(
            {k: v for k, v in manifest.items() if k not in ("wildchat_files", "weights")}, indent=1
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
