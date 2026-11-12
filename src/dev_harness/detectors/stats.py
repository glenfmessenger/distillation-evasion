"""Content-blind detector statistics D1–D9 (PROTOCOL §5, decision 3).

Every statistic reads only RequestRecord fields: timestamps, token counts, cache counts, turn
counts, identity/session ids. No prompt or response text is available to this module by
construction (RequestRecord carries none). Statistics are computed per session or per identity;
thresholds are set later from benign statistics per FPR budget (calibrate()). In-flight records
are excluded before any statistic is computed and the exclusion is counted.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np

from dev_harness.detectors.base import SessionStatistic, drop_in_flight
from dev_harness.records import RequestRecord, event_time_ns

NS_PER_S = 1_000_000_000
TOKEN_EDGES = (0, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 1 << 30)
MIN_SCOREABLE = 10  # D4/D6/D8 need at least this many completed records (PROTOCOL §5)
N_MATCH = 30  # D8 matched request count (decision 3)
N_SUBSAMPLES = 20


def _bucket(x: int | None) -> int:
    if x is None:
        raise ValueError("token count is None on a completed record")
    for i in range(len(TOKEN_EDGES) - 1):
        if TOKEN_EDGES[i] <= x < TOKEN_EDGES[i + 1]:
            return i
    raise ValueError(x)


def cell(r: RequestRecord) -> tuple[int, int]:
    return _bucket(r.prompt_tokens), _bucket(r.generated_tokens)


def _check_time_base(group: list[RequestRecord]) -> None:
    kinds = {r.t_sched_ns is None for r in group}
    if len(kinds) > 1:
        raise ValueError(
            f"mixed scheduled/unscheduled timestamps in {group[0].identity_id}/{group[0].session_id}"
        )


def by_session(records: Iterable[RequestRecord]) -> dict[str, list[RequestRecord]]:
    out: dict[str, list[RequestRecord]] = defaultdict(list)
    for r in records:
        out[r.session_id].append(r)
    for v in out.values():
        _check_time_base(v)
        v.sort(key=lambda r: event_time_ns(r))
    return dict(out)


def by_identity(records: Iterable[RequestRecord]) -> dict[str, list[RequestRecord]]:
    out: dict[str, list[RequestRecord]] = defaultdict(list)
    for r in records:
        out[r.identity_id].append(r)
    for v in out.values():
        _check_time_base(v)
        v.sort(key=lambda r: event_time_ns(r))
    return dict(out)


def _stat(
    det: str, recs: Sequence[RequestRecord], value: float, n_excl: int, key: str
) -> SessionStatistic:
    return SessionStatistic(
        detector_id=det,
        session_id=key,
        identity_id=recs[0].identity_id,
        value=float(value),
        n_records=len(recs),
        n_excluded_in_flight=n_excl,
    )


# ---------- reference (benign) model ----------


@dataclass
class BenignReference:
    """Pooled benign distributions needed by D4, D6, D8. Fit on benign records only."""

    gen_tokens: np.ndarray
    prompt_tokens: np.ndarray
    cell_hist: dict[tuple[int, int], float]  # normalised

    @classmethod
    def fit(cls, benign_records: Iterable[RequestRecord]) -> BenignReference:
        kept, _ = drop_in_flight(list(benign_records))
        if len(kept) < 100:
            raise ValueError(f"benign reference needs >= 100 completed records, got {len(kept)}")
        cells = Counter(cell(r) for r in kept)
        tot = sum(cells.values())
        return cls(
            gen_tokens=np.sort([r.generated_tokens for r in kept]),
            prompt_tokens=np.sort([r.prompt_tokens for r in kept]),
            cell_hist={k: v / tot for k, v in cells.items()},
        )


def ks_distance(sample: Sequence[float], ref_sorted: np.ndarray) -> float:
    s = np.sort(np.asarray(sample, dtype=float))
    allv = np.concatenate([s, ref_sorted])
    cdf_s = np.searchsorted(s, allv, side="right") / s.size
    cdf_r = np.searchsorted(ref_sorted, allv, side="right") / ref_sorted.size
    return float(np.max(np.abs(cdf_s - cdf_r)))


def jsd(p: dict, q: dict) -> float:
    keys = set(p) | set(q)
    P = np.array([p.get(k, 0.0) for k in keys])
    Q = np.array([q.get(k, 0.0) for k in keys])
    M = 0.5 * (P + Q)

    def kl(a, b):
        m = a > 0
        return float(np.sum(a[m] * np.log2(a[m] / b[m])))

    return 0.5 * kl(P, M) + 0.5 * kl(Q, M)


# ---------- per-session detectors ----------


def d3_cadence(session: Sequence[RequestRecord], n_excl: int = 0) -> SessionStatistic:
    """Coefficient of variation of inter-arrival (scheduled send times). Direction: LOW = campaign."""
    kept, e = drop_in_flight(session)
    if len(kept) < 3:
        return _stat("D3", session, math.nan, n_excl + e, session[0].session_id)
    gaps = np.diff([event_time_ns(r) for r in kept]) / NS_PER_S
    cv = float(gaps.std() / gaps.mean()) if gaps.mean() > 0 else 0.0
    return _stat("D3", kept, cv, n_excl + e, kept[0].session_id)


def d4_output_shape(session: Sequence[RequestRecord], ref: BenignReference) -> SessionStatistic:
    kept, e = drop_in_flight(session)
    if len(kept) < MIN_SCOREABLE:
        return _stat("D4", session, math.nan, e, session[0].session_id)
    return _stat(
        "D4",
        kept,
        ks_distance([r.generated_tokens for r in kept], ref.gen_tokens),
        e,
        kept[0].session_id,
    )


def d5_reasoning_share(session: Sequence[RequestRecord]) -> SessionStatistic:
    kept, e = drop_in_flight(session)
    shares = [
        r.reasoning_tokens / r.generated_tokens
        for r in kept
        if r.reasoning_tokens is not None and r.generated_tokens
    ]
    if not shares:
        return _stat("D5", session, math.nan, e, session[0].session_id)
    return _stat("D5", kept, float(np.median(shares)), e, kept[0].session_id)


def d6_prompt_shape(session: Sequence[RequestRecord], ref: BenignReference) -> SessionStatistic:
    kept, e = drop_in_flight(session)
    if len(kept) < MIN_SCOREABLE:
        return _stat("D6", session, math.nan, e, session[0].session_id)
    return _stat(
        "D6",
        kept,
        ks_distance([r.prompt_tokens for r in kept], ref.prompt_tokens),
        e,
        kept[0].session_id,
    )


def d7_cache_share(session: Sequence[RequestRecord]) -> SessionStatistic:
    kept, e = drop_in_flight(session)
    vals = [
        r.cached_prompt_tokens / r.prompt_tokens
        for r in kept
        if r.cached_prompt_tokens is not None and r.prompt_tokens
    ]
    if not vals:
        return _stat("D7", session, math.nan, e, session[0].session_id)
    return _stat("D7", kept, float(np.mean(vals)), e, kept[0].session_id)


def d9_single_turn(session: Sequence[RequestRecord]) -> SessionStatistic:
    kept, e = drop_in_flight(session)
    if not kept:
        return _stat("D9", session, math.nan, e, session[0].session_id)
    return _stat(
        "D9", kept, float(np.mean([r.turn_count == 1 for r in kept])), e, kept[0].session_id
    )


# ---------- per-identity detectors ----------


def d1_rate(identity: Sequence[RequestRecord], window_s: float = 3600.0) -> SessionStatistic:
    """Max requests per identity in any sliding window of window_s (scheduled send times)."""
    kept, e = drop_in_flight(identity)
    if not kept:
        return _stat("D1", identity, math.nan, e, identity[0].identity_id)
    t = np.array([event_time_ns(r) for r in kept]) / NS_PER_S
    best, j = 0, 0
    for i in range(len(t)):
        while t[i] - t[j] > window_s:
            j += 1
        best = max(best, i - j + 1)
    return _stat("D1", kept, best, e, kept[0].identity_id)


def d2_sessions_per_day(identity: Sequence[RequestRecord]) -> SessionStatistic:
    kept, e = drop_in_flight(identity)
    if not kept:
        return _stat("D2", identity, math.nan, e, identity[0].identity_id)
    span_days = max((event_time_ns(kept[-1]) - event_time_ns(kept[0])) / NS_PER_S / 86400.0, 1e-9)
    n_sess = len({r.session_id for r in kept})
    return _stat("D2", kept, n_sess / max(span_days, 1.0 / 24), e, kept[0].identity_id)


def d8_coverage(
    identity: Sequence[RequestRecord],
    ref: BenignReference,
    seed: int = 0,
    n_match: int = N_MATCH,
    n_sub: int = N_SUBSAMPLES,
) -> SessionStatistic:
    """JSD at matched request count between the identity's cell histogram and the benign
    population histogram; median over n_sub subsamples of size n_match (decision 3, F13)."""
    kept, e = drop_in_flight(identity)
    if len(kept) < n_match:
        return _stat("D8", identity, math.nan, e, identity[0].identity_id)
    rng = np.random.default_rng(seed)
    cells = [cell(r) for r in kept]
    vals = []
    for _ in range(n_sub):
        idx = rng.choice(len(cells), size=n_match, replace=False)
        h = Counter(cells[i] for i in idx)
        vals.append(jsd({k: v / n_match for k, v in h.items()}, ref.cell_hist))
    return _stat("D8", kept, float(np.median(vals)), e, kept[0].identity_id)


def d8b_distinct_cells(
    identity: Sequence[RequestRecord],
    seed: int = 0,
    n_match: int = N_MATCH,
    n_sub: int = N_SUBSAMPLES,
) -> SessionStatistic:
    kept, e = drop_in_flight(identity)
    if len(kept) < n_match:
        return _stat("D8b", identity, math.nan, e, identity[0].identity_id)
    rng = np.random.default_rng(seed)
    cells = [cell(r) for r in kept]
    vals = [
        len({cells[i] for i in rng.choice(len(cells), size=n_match, replace=False)})
        for _ in range(n_sub)
    ]
    return _stat("D8b", kept, float(np.median(vals)), e, kept[0].identity_id)


DIRECTION = {
    "D1": "high",
    "D2": "high",
    "D3": "low",
    "D4": "high",
    "D5": "high",
    "D6": "high",
    "D7": "high",
    "D8": "high",
    "D8b": "low",
    "D9": "high",
}
GRAIN = {
    "D1": "identity",
    "D2": "identity",
    "D8": "identity",
    "D8b": "identity",
    "D3": "session",
    "D4": "session",
    "D5": "session",
    "D6": "session",
    "D7": "session",
    "D9": "session",
}


def all_statistics(
    records: Iterable[RequestRecord], ref: BenignReference, seed: int = 0
) -> list[SessionStatistic]:
    recs = list(records)
    out: list[SessionStatistic] = []
    for sess in by_session(recs).values():
        out += [
            d3_cadence(sess),
            d4_output_shape(sess, ref),
            d5_reasoning_share(sess),
            d6_prompt_shape(sess, ref),
            d7_cache_share(sess),
            d9_single_turn(sess),
        ]
    for ident in by_identity(recs).values():
        out += [
            d1_rate(ident),
            d2_sessions_per_day(ident),
            d8_coverage(ident, ref, seed),
            d8b_distinct_cells(ident, seed),
        ]
    return out


# ---------- calibration ----------


def calibrate(benign_values: Sequence[float], direction: str, fpr: float) -> dict:
    """Threshold at FPR budget `fpr` from benign statistics (NaNs excluded and counted).
    Returns the threshold, the number of benign exceedances, and whether the budget is below the
    resolution floor (fewer than 10 exceedances, PROTOCOL §4)."""
    v = np.asarray([x for x in benign_values if not math.isnan(x)], dtype=float)
    n_nan = len(benign_values) - v.size
    if v.size == 0:
        raise ValueError("no scoreable benign values")
    k = int(math.floor(fpr * v.size))  # exactly k benign values exceed the threshold
    s = np.sort(v)
    if direction == "high":
        thr = s[-k - 1] if k < v.size else s[0] - 1e-9
    else:
        thr = s[k] if k < v.size else s[-1] + 1e-9
    exceed = int(np.sum(v > thr)) if direction == "high" else int(np.sum(v < thr))
    return {
        "threshold": float(thr),
        "direction": direction,
        "fpr_budget": fpr,
        "n_benign": int(v.size),
        "n_unscoreable": int(n_nan),
        "n_exceed": exceed,
        "resolution": 1.0 / v.size,
        "below_resolution": exceed < 10,
    }


def fires(value: float, cal: dict) -> bool | None:
    if math.isnan(value):
        return None
    return value > cal["threshold"] if cal["direction"] == "high" else value < cal["threshold"]
