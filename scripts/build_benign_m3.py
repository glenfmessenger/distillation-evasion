#!/usr/bin/env python
"""M3 benign model, two artefacts (PROTOCOL §4 as amended by A3; CPU only, no teacher requests):

1. timeline.jsonl — EVERY real pseudo-user in the WildChat slice on the corpus timeline, with no
   prompt text (identity, session, index, scheduled time, turn index, component). Calibrates the
   timeline detectors D1, D2, D3, D9, which need no serving statistic.
2. replay_schedule.jsonl — the stratified subset actually sent to the teacher (heavy real users,
   light real users, constructed heavy-tail components), each identity capped at `--cap` requests.
   Calibrates the serving-statistic detectors D4–D8 and the content-aware arm C1.

Usage: build_benign_m3.py --label L [--files 14] [--n-heavy 1000] [--n-light 1500] [--cap 40]
                          [--n-eval 30] [--n-batch 30] [--n-agent 60] [--seed 0]
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from build_benign import eval_prompts

from dev_harness.benign import (
    BenignDataError,
    constructed_schedule,
    iter_wildchat,
    real_user_schedule,
    select_replay_subset,
    write_schedule,
)
from dev_harness.paths import host_repo


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--files", type=int, default=14)
    ap.add_argument("--n-heavy", type=int, default=1000)
    ap.add_argument("--n-light", type=int, default=1500)
    ap.add_argument("--cap", type=int, default=40)
    ap.add_argument("--n-eval", type=int, default=30)
    ap.add_argument("--n-batch", type=int, default=30)
    ap.add_argument("--n-agent", type=int, default=60)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    root = host_repo()
    files = sorted(
        glob.glob(str(root / "hf/hub/datasets--allenai--WildChat-1M/snapshots/*/data/*.parquet"))
    )
    if len(files) < a.files:
        raise BenignDataError(f"found {len(files)} WildChat parquet files, need {a.files}")
    files = [Path(f) for f in files[: a.files]]
    convs = list(iter_wildchat(files))
    full, skipped = real_user_schedule(convs)
    out = root / "benign" / a.label
    out.mkdir(parents=True, exist_ok=True)
    with (out / "timeline.jsonl").open("w") as fh:
        for r in full:
            fh.write(
                json.dumps(
                    {
                        "identity_id": r.identity_id,
                        "session_id": r.session_id,
                        "request_index": r.request_index,
                        "t_sched_s": r.t_sched_s,
                        "turn_index": r.turn_index,
                        "component": r.component,
                    }
                )
                + "\n"
            )
    subset, info = select_replay_subset(full, a.n_heavy, a.n_light, a.cap, a.seed)
    built = constructed_schedule(convs, eval_prompts(), a.seed, a.n_eval, a.n_batch, a.n_agent)
    replay_sched = subset + built
    sha = write_schedule(replay_sched, out / "replay_schedule.jsonl")
    per_i, per_s, comp = Counter(), Counter(), {}
    for r in replay_sched:
        per_i[r.identity_id] += 1
        per_s[r.session_id] += 1
        comp[r.identity_id] = r.component
    pop_i = Counter(r.identity_id for r in full)
    by_comp = defaultdict(lambda: [0, 0, 0])
    for i, n in per_i.items():
        by_comp[comp[i]][0] += 1
        by_comp[comp[i]][1] += n
        by_comp[comp[i]][2] += n >= 30
    manifest = {
        "label": a.label,
        "args": vars(a),
        "wildchat_files": [f.name for f in files],
        "wildchat_snapshot": files[0].parts[-3],
        "n_conversations_skipped_missing_timestamps": skipped,
        "timeline": {
            "identities": len(pop_i),
            "sessions": len({r.session_id for r in full}),
            "requests": len(full),
            "identities_ge_30": sum(v >= 30 for v in pop_i.values()),
        },
        "replay": {
            "identities": len(per_i),
            "sessions": len(per_s),
            "requests": len(replay_sched),
            "identities_ge_30": sum(v >= 30 for v in per_i.values()),
            "sessions_ge_10": sum(v >= 10 for v in per_s.values()),
            "by_component": {
                k: {"identities": v[0], "requests": v[1], "identities_ge_30": v[2]}
                for k, v in sorted(by_comp.items())
            },
            "prompt_chars_total": sum(len(r.user_content) for r in replay_sched),
            "schedule_sha256": sha,
        },
        "strata": info,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(json.dumps({k: manifest[k] for k in ("timeline", "replay", "strata")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
