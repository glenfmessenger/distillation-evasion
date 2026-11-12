"""Held-out ordinary prompts for the C-real campaign (PROTOCOL v2.0 §3). Pure selection logic,
testable without the corpus. Every exclusion is counted and named."""

from __future__ import annotations

import random
from collections import Counter
from collections.abc import Iterable

from dev_harness.benign import Conversation
from dev_harness.pool import ngrams


def replay_user_keys(identity_ids: Iterable[str]) -> set[str]:
    """Pseudo-user keys behind the replay subset's real-user identities ('b:conv:<key>')."""
    keys = set()
    for i in identity_ids:
        parts = i.split(":")
        if len(parts) == 3 and parts[0] == "b" and parts[1] == "conv":
            keys.add(parts[2])
    if not keys:
        raise ValueError("no real-user identities found in the replay schedule")
    return keys


def select_real_prompts(
    convs: Iterable[Conversation],
    excluded_users: set[str],
    replay_prompts: Iterable[str],
    n: int,
    seed: int,
    ngram_n: int = 13,
) -> tuple[list[dict], dict]:
    """First user turn of held-out conversations: pseudo-user not in the replay subset, text not
    seen before (exact), and sharing no `ngram_n`-gram with any replay prompt. A seeded sample
    of `n` from what survives, in a shuffled order. Raises if fewer than `n` survive."""
    grams = set()
    for p in replay_prompts:
        grams |= ngrams(p, ngram_n)
    counts = Counter()
    seen_text: set[str] = set()
    cands: list[dict] = []
    for c in convs:
        counts["conversations"] += 1
        if c.user_key in excluded_users:
            counts["dropped_user_in_replay_subset"] += 1
            continue
        text = c.turns[0][1]
        if text in seen_text:
            counts["dropped_duplicate_text"] += 1
            continue
        seen_text.add(text)
        if grams & ngrams(text, ngram_n):
            counts["dropped_ngram_overlap_with_replay"] += 1
            continue
        cands.append({"id": f"wc:{c.conv_hash}", "user_key": c.user_key, "text": text})
    counts["candidates"] = len(cands)
    if len(cands) < n:
        raise ValueError(f"only {len(cands)} held-out prompts survive, need {n}")
    rng = random.Random(seed)
    chosen = rng.sample(cands, n)
    rng.shuffle(chosen)
    return chosen, dict(counts)
