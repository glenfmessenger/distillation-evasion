#!/usr/bin/env python
"""Content-level calibration set of all heavy real users (PROTOCOL v2.0 amendment B1 item 2): every
WildChat pseudo-user with at least --min-turns user turns, excluding users who own any
conversation used by the listed campaign prompt files; up to --cap prompts per user in time
order. Prompt text only; no teacher calls. Writes
$HARNESS_HOST_REPO/content_calibration/<label>/{users.jsonl,manifest.json}.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

from dev_harness.benign import BenignDataError, iter_wildchat
from dev_harness.paths import host_repo


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--exclude-labels", default="", help="comma-separated campaign prompt labels")
    ap.add_argument("--min-turns", type=int, default=30)
    ap.add_argument("--cap", type=int, default=100)
    ap.add_argument("--files", type=int, default=14)
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
    excluded_convs: set[str] = set()
    for lab in [x for x in a.exclude_labels.split(",") if x.strip()]:
        with (root / "campaign_prompts" / lab / "prompts.jsonl").open(encoding="utf-8") as fh:
            excluded_convs |= {json.loads(line)["id"][3:] for line in fh if line.strip()}
    turns: dict[str, list[tuple[float, str]]] = defaultdict(list)
    excluded_users: set[str] = set()
    n_conv = 0
    for c in iter_wildchat(files):
        if c is None:
            continue
        n_conv += 1
        if c.conv_hash in excluded_convs:
            excluded_users.add(c.user_key)
        turns[c.user_key].extend(c.turns)
    out = root / "content_calibration" / a.label
    out.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    n_users = n_heavy = n_excl = 0
    with (out / "users.jsonl").open("w", encoding="utf-8") as fh:
        for user, ts in turns.items():
            n_users += 1
            if len(ts) < a.min_turns:
                continue
            n_heavy += 1
            if user in excluded_users:
                n_excl += 1
                continue
            prompts = [t for _, t in sorted(ts, key=lambda x: x[0])[: a.cap]]
            line = (
                json.dumps(
                    {"identity": f"h:{user}", "n_total": len(ts), "prompts": prompts},
                    ensure_ascii=False,
                )
                + "\n"
            )
            fh.write(line)
            h.update(line.encode())
    manifest = {
        "label": a.label,
        "min_turns": a.min_turns,
        "cap": a.cap,
        "exclude_labels": a.exclude_labels,
        "wildchat_snapshot": files[0].parts[-3],
        "n_conversations": n_conv,
        "n_users": n_users,
        "n_heavy_users": n_heavy,
        "n_heavy_users_excluded_campaign_owners": n_excl,
        "n_written": n_heavy - n_excl,
        "users_sha256": h.hexdigest(),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(json.dumps(manifest, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
