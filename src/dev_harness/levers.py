"""V1 evasion levers as re-schedulings of recorded campaign responses (PROTOCOL v2.0 §6; v1.0 §6
L1, L2). No new teacher calls: every server-side field of a record is kept; only identity,
session membership and scheduled time change. Pure functions, seeded, testable."""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Sequence

from dev_harness.records import RequestRecord

NS = 1_000_000_000


def split_identities(
    records: Sequence[RequestRecord], n: int, seed: int, session_size: int = 100
) -> list[RequestRecord]:
    """L1: the campaign's requests, in their original issue order, dealt round-robin over `n`
    identities from a seeded starting offset; each identity's stream is cut into sessions of
    `session_size`. n = 1 keeps one identity. Record count and server fields are unchanged."""
    if n < 1:
        raise ValueError("n must be >= 1")
    rng = random.Random(seed)
    order = sorted(records, key=_issue_order)
    start = rng.randrange(n)
    per: dict[int, list[RequestRecord]] = defaultdict(list)
    for k, r in enumerate(order):
        per[(start + k) % n].append(r)
    out = []
    for i in range(n):
        for k, r in enumerate(per[i]):
            out.append(
                r.model_copy(
                    update={
                        "identity_id": f"{r.identity_id}:L1n{n}:i{i}",
                        "session_id": f"{r.identity_id}:L1n{n}:i{i}:s{k // session_size}",
                        "request_index_in_session": k % session_size,
                    }
                )
            )
    return out


def shape_rate(
    records: Sequence[RequestRecord], cap_per_hour: int, seed: int
) -> list[RequestRecord]:
    """L2: each identity's requests re-timed in order at interval h = 3600 / (cap - 1) seconds
    plus seeded uniform jitter in [0, h / 2), from a seeded per-identity start, so that no closed
    3,600 s window holds more than `cap_per_hour` of them (cap + 1 consecutive points span at
    least cap * h - h / 2 = 3600 + h / 2). The original relative timing is discarded (that is the
    lever's effect); server fields are unchanged. cap_per_hour = 0 means unshaped."""
    if cap_per_hour < 0:
        raise ValueError("cap_per_hour must be >= 0")
    if cap_per_hour == 0:
        return list(records)
    rng = random.Random(seed)
    h_ns = int(3600 * NS / (cap_per_hour - 1)) if cap_per_hour > 1 else 2 * 3600 * NS
    by_ident: dict[str, list[RequestRecord]] = defaultdict(list)
    for r in sorted(records, key=_issue_order):
        by_ident[r.identity_id].append(r)
    out = []
    for ident in sorted(by_ident):
        start = rng.randrange(h_ns)
        for k, r in enumerate(by_ident[ident]):
            t = start + k * h_ns + rng.randrange(h_ns // 2)
            out.append(r.model_copy(update={"t_sched_ns": t}))
    return out


def price(records: Sequence[RequestRecord]) -> dict:
    """Per-cell price (v1.0 §7): identities, scheduled wall-clock, teacher tokens."""
    t = [r.t_sched_ns if r.t_sched_ns is not None else r.t_send_ns for r in records]
    return {
        "identities": len({r.identity_id for r in records}),
        "requests": len(records),
        "wall_clock_s": (max(t) - min(t)) / NS if records else 0.0,
        "prompt_tokens": sum(r.prompt_tokens or 0 for r in records),
        "generated_tokens": sum(r.generated_tokens or 0 for r in records),
    }


def _issue_order(r: RequestRecord):
    return (r.t_sched_ns if r.t_sched_ns is not None else r.t_send_ns, r.t_send_ns)


def split_heterogeneous(
    records: Sequence[RequestRecord],
    n: int,
    seed: int,
    benign_counts: Sequence[int],
    benign_session_lens: Sequence[int],
    stagger_s: float,
    interval_s: float,
    count_cap: int = 0,
    session_mult: float = 1.0,
) -> list[RequestRecord]:
    """L8 (amendment B2), extended for L9 (amendment B4): `count_cap` truncates the benign count
    draw at that many requests per identity (0 = no cap) and `session_mult` scales the drawn
    session sizes.: the campaign's requests dealt over `n` identities with per-identity
    request counts proportional to a seeded draw from `benign_counts` (summing to the campaign
    size), session sizes drawn from `benign_session_lens`, per-identity start offsets uniform in
    [0, stagger_s], and requests issued every `interval_s` seconds with jitter up to half the
    interval. Server fields unchanged; t_sched_ns rewritten on a timeline starting at zero."""
    if n < 1 or not benign_counts or not benign_session_lens:
        raise ValueError("need n >= 1 and non-empty benign draws")
    rng = random.Random(seed)
    order = sorted(records, key=_issue_order)
    total = len(order)
    draw = [max(1, rng.choice(list(benign_counts))) for _ in range(n)]
    if count_cap:
        draw = [min(d, count_cap) for d in draw]
    scale = total / sum(draw)
    counts = [max(1, int(round(d * scale))) for d in draw]
    diff = total - sum(counts)
    i = 0
    while diff != 0:  # fix rounding so the counts sum to the campaign size
        j = i % n
        if diff > 0:
            counts[j] += 1
            diff -= 1
        elif counts[j] > 1:
            counts[j] -= 1
            diff += 1
        i += 1
    out, pos = [], 0
    for ident in range(n):
        mine = order[pos : pos + counts[ident]]
        pos += counts[ident]
        start = rng.uniform(0.0, stagger_s)
        t = start
        sess_no, sess_left = (
            0,
            max(1, int(round(rng.choice(list(benign_session_lens)) * session_mult))),
        )
        idx = 0
        for r in mine:
            if sess_left == 0:
                sess_no += 1
                sess_left = max(1, int(round(rng.choice(list(benign_session_lens)) * session_mult)))
                idx = 0
                t += 1800.0 + 1.0  # a new session begins after the idle gap
            out.append(
                r.model_copy(
                    update={
                        "identity_id": f"{r.identity_id}:L8n{n}:i{ident}",
                        "session_id": f"{r.identity_id}:L8n{n}:i{ident}:s{sess_no}",
                        "request_index_in_session": idx,
                        "t_sched_ns": int(t * NS),
                    }
                )
            )
            t += interval_s + rng.uniform(0.0, interval_s / 2.0)
            idx += 1
            sess_left -= 1
    return out
