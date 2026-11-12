#!/usr/bin/env python
"""Build the C-real prompt file (PROTOCOL v2.0 §3): first user turns of WildChat conversations
whose pseudo-user is absent from the benign replay subset, exact-deduplicated, with no 13-gram in
common with any replay prompt. Same parquet files and snapshot as the benign build.

Writes $HARNESS_HOST_REPO/campaign_prompts/<label>/prompts.jsonl (id, source, messages) and
manifest.json (counts, seed, snapshot, sha256). Usage: build_real_prompts.py --benign-label m3_v1
--label c_real_v2 --n 8000 --seed 0
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import sys
from pathlib import Path

from dev_harness.benign import BenignDataError, iter_wildchat, read_schedule
from dev_harness.paths import host_repo
from dev_harness.real_prompts import replay_user_keys, select_real_prompts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--n", type=int, default=8000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--files", type=int, default=14)
    ap.add_argument(
        "--exclude-label",
        default="",
        help="exclude the prompt ids (conversations) already used by this earlier label",
    )
    a = ap.parse_args()
    root = host_repo()
    files = sorted(
        Path(p)
        for p in glob.glob(
            str(root / "hf/hub/datasets--allenai--WildChat-1M/snapshots/*/data/*.parquet")
        )
    )
    if len(files) != a.files:
        raise BenignDataError(f"found {len(files)} WildChat parquet files, need {a.files}")
    sched = read_schedule(root / "benign" / a.benign_label / "replay_schedule.jsonl")
    excluded = replay_user_keys(r.identity_id for r in sched)
    replay_prompts = [r.user_content for r in sched]
    excluded_ids: set[str] = set()
    for lab in [x for x in a.exclude_label.split(",") if x.strip()]:
        with (root / "campaign_prompts" / lab / "prompts.jsonl").open(encoding="utf-8") as fh:
            excluded_ids |= {json.loads(line)["id"] for line in fh if line.strip()}
    convs = (
        c for c in iter_wildchat(files) if c is not None and f"wc:{c.conv_hash}" not in excluded_ids
    )
    chosen, counts = select_real_prompts(convs, excluded, replay_prompts, a.n, a.seed)
    out = root / "campaign_prompts" / a.label
    out.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    with (out / "prompts.jsonl").open("w") as fh:
        for d in chosen:
            line = (
                json.dumps(
                    {
                        "id": d["id"],
                        "source": "allenai/WildChat-1M:heldout",
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
        "benign_label": a.benign_label,
        "n": a.n,
        "seed": a.seed,
        "wildchat_snapshot": files[0].parts[-3],
        "n_replay_users_excluded": len(excluded),
        "exclude_label": a.exclude_label,
        "n_prior_prompt_ids_excluded": len(excluded_ids),
        "n_replay_prompts_for_ngram_check": len(replay_prompts),
        "counts": counts,
        "prompts_sha256": h.hexdigest(),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(json.dumps(manifest, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
