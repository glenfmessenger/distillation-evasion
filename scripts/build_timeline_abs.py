#!/usr/bin/env python
"""Absolute-time benign timeline for D10 (PROTOCOL v2.0 amendment B2): every real pseudo-user of
the WildChat slice, sessionised with the same idle-gap rule as the replay timeline, but with the
corpus timestamp kept (t_abs_s, Unix seconds) instead of rebasing each identity to zero. No prompt
text, no teacher calls. Writes $HARNESS_HOST_REPO/benign/<label>/timeline_abs.jsonl and
manifest_abs.json.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

from dev_harness.benign import SESSION_GAP_S, BenignDataError, iter_wildchat
from dev_harness.paths import host_repo


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
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
    by_user: dict[str, list[tuple[float, str, int]]] = defaultdict(list)
    n_conv = skipped = 0
    for c in iter_wildchat(files):
        if c is None:
            skipped += 1
            continue
        n_conv += 1
        for i, (t, _content) in enumerate(c.turns):
            by_user[c.user_key].append((t, c.conv_hash, i))
    out = root / "benign" / a.label
    out.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    n_req = n_sess = 0
    tmin, tmax = float("inf"), float("-inf")
    with (out / "timeline_abs.jsonl").open("w") as fh:
        for u in sorted(by_user):
            reqs = sorted(by_user[u])
            sess, idx, last = 0, 0, reqs[0][0]
            for t, conv, turn in reqs:
                if t - last > SESSION_GAP_S:
                    sess, idx = sess + 1, 0
                line = (
                    json.dumps(
                        {
                            "identity_id": f"b:real:{u}",
                            "session_id": f"b:real:{u}:s{sess}",
                            "request_index": idx,
                            "t_abs_s": t,
                            "turn_index": turn,
                            "conv_id": conv,
                        }
                    )
                    + "\n"
                )
                fh.write(line)
                h.update(line.encode())
                idx, last = idx + 1, t
                n_req += 1
                tmin, tmax = min(tmin, t), max(tmax, t)
            n_sess += sess + 1
    manifest = {
        "label": a.label,
        "wildchat_snapshot": files[0].parts[-3],
        "session_gap_s": SESSION_GAP_S,
        "n_conversations": n_conv,
        "n_conversations_skipped_missing_timestamps": skipped,
        "identities": len(by_user),
        "sessions": n_sess,
        "requests": n_req,
        "t_min_s": tmin,
        "t_max_s": tmax,
        "span_days": (tmax - tmin) / 86400.0,
        "timeline_abs_sha256": h.hexdigest(),
    }
    (out / "manifest_abs.json").write_text(json.dumps(manifest, indent=1))
    print(json.dumps(manifest, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
