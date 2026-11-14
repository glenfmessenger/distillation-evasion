#!/usr/bin/env python
"""Amendment B14 (D)(i), step 1: group replayed real accounts by the corpus's hashed address.

The account key is sha1(hashed address | user agent). This reads the two columns from the public
corpus, one file at a time (each file is deleted after reading), and writes for every replayed
real account a salted label of its address. The address itself is not stored.

Writes <data root>/benign/<label>/address_groups.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download

from dev_harness.benign import read_schedule, user_key
from dev_harness.paths import host_repo

REPO = "allenai/WildChat-1M"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--scratch", required=True)
    a = ap.parse_args()
    root = host_repo()
    man = json.loads((root / "benign" / a.benign_label / "manifest.json").read_text())
    want = set()
    for r in read_schedule(root / "benign" / a.benign_label / "replay_schedule.jsonl"):
        if r.identity_id.startswith(("b:conv:", "b:code:")):
            want.add(r.identity_id.split(":", 2)[2])
    salt = os.urandom(16)
    label: dict[str, set[str]] = defaultdict(set)
    scratch = Path(a.scratch)
    for name in man["wildchat_files"]:
        path = hf_hub_download(
            REPO,
            f"data/{name}",
            repo_type="dataset",
            revision=man["wildchat_snapshot"],
            cache_dir=scratch,
        )
        pf = pq.ParquetFile(path)
        for batch in pf.iter_batches(batch_size=20000, columns=["hashed_ip", "header"]):
            for ip, hdr in zip(
                batch.column("hashed_ip").to_pylist(), batch.column("header").to_pylist()
            ):
                key = user_key(ip, (hdr or {}).get("user-agent"))
                if key in want:
                    label[key].add(hashlib.sha256(salt + ip.encode()).hexdigest()[:16])
        shutil.rmtree(scratch, ignore_errors=True)
        print(f"{name}: {len(label)} of {len(want)} accounts located", flush=True)
    missing = want - set(label)
    if missing:
        raise RuntimeError(f"{len(missing)} replayed accounts not found in the corpus")
    multi = [k for k, v in label.items() if len(v) != 1]
    if multi:
        raise RuntimeError(f"{len(multi)} account keys map to more than one address")
    groups: dict[str, list[str]] = defaultdict(list)
    for k, v in label.items():
        groups[next(iter(v))].append(k)
    out = {"n_accounts": len(label), "groups": {g: sorted(v) for g, v in groups.items()}}
    (root / "benign" / a.benign_label / "address_groups.json").write_text(json.dumps(out))
    sizes = sorted((len(v) for v in groups.values()), reverse=True)
    print(
        f"{len(groups)} addresses; {sum(1 for s in sizes if s >= 2)} with two or more replayed accounts; largest {sizes[:10]}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
