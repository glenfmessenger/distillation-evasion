#!/usr/bin/env python
"""Build the query pool and suite files under $HARNESS_HOST_REPO/pool (PLAN M2 step 1).
Writes pool.jsonl, suites/<name>.jsonl, and pool_manifest.json (counts, contamination report,
sha256 of pool.jsonl). Exit 1 on any loader error; nothing is substituted."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from dev_harness.paths import host_repo
from dev_harness.pool import contamination, pool_sources, suites, write_jsonl


def main() -> int:
    root = host_repo() / "pool"
    root.mkdir(parents=True, exist_ok=True)
    su = suites()
    po = pool_sources()
    clean, report = contamination(po, su, n=13)
    suite_hashes = {k: write_jsonl(v, root / "suites" / f"{k}.jsonl") for k, v in su.items()}
    allpool = [
        it for k in ("math_train", "gsm8k_train", "apps_train", "mbpp_pool") for it in clean[k]
    ]
    pool_hash = write_jsonl(allpool, root / "pool.jsonl")
    manifest = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "suite_counts": {k: len(v) for k, v in su.items()},
        "pool_counts_raw": {k: len(v) for k, v in po.items()},
        "contamination": report,
        "pool_count_clean": len(allpool),
        "pool_sha256": pool_hash,
        "suite_sha256": suite_hashes,
        "sources": {
            "math_train": "EleutherAI/hendrycks_math (7 configs, train)",
            "gsm8k_train": "openai/gsm8k main train",
            "apps_train": "codeparrot/apps default train @refs/convert/parquet (standard-IO items with tests)",
            "mbpp_pool": "google-research-datasets/mbpp full train+validation",
            "math500": "HuggingFaceH4/MATH-500 test",
            "gsm8k_test": "openai/gsm8k main test",
            "humaneval": "openai/openai_humaneval test",
            "mbpp_test": "google-research-datasets/mbpp full test",
        },
    }
    (root / "pool_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(
        json.dumps(
            {k: manifest[k] for k in ("suite_counts", "pool_counts_raw", "pool_count_clean")},
            indent=1,
        )
    )
    print("contamination removed:", report["removed"])
    print("exact hits:", report["exact_hits"])
    print("ngram hits:", report["ngram_hits"])
    print("pool sha256:", pool_hash)
    return 0


if __name__ == "__main__":
    sys.exit(main())
