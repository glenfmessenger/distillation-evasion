"""D10, the cross-identity coordination detector (PROTOCOL v2.0 amendment B2). Content-blind:
features come from timing and turn structure only. Pure numpy; the caller supplies identity-day
rows.

An identity-day row: dict with identity, day (int, UTC days since epoch), requests (int),
sessions (int), session_len_median (float), gap_median_s (float, median intra-session
inter-arrival; NaN when no session has two requests), span_s (float, last - first within the
day), start_hour (float, 0..24), single_turn_frac (float). Features follow the amendment text.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Sequence

import numpy as np

FEATURES = (
    "log_requests",
    "log_sessions",
    "session_len_median",
    "log_gap_median",
    "log_span",
    "start_sin",
    "start_cos",
    "single_turn_frac",
)


def features(row: dict) -> np.ndarray:
    gap = row["gap_median_s"]
    gap = 0.0 if gap is None or (isinstance(gap, float) and math.isnan(gap)) else gap
    a = 2 * math.pi * row["start_hour"] / 24.0
    return np.array(
        [
            math.log1p(row["requests"]),
            math.log1p(row["sessions"]),
            float(row["session_len_median"]),
            math.log1p(gap),
            math.log1p(row["span_s"]),
            math.sin(a),
            math.cos(a),
            float(row["single_turn_frac"]),
        ]
    )


class Standardiser:
    """Benign median and MAD per feature (MAD floored so a constant feature does not blow up)."""

    def __init__(self, benign: np.ndarray) -> None:
        if benign.ndim != 2 or len(benign) < 100:
            raise ValueError("need at least 100 benign feature rows")
        self.med = np.median(benign, axis=0)
        mad = np.median(np.abs(benign - self.med), axis=0)
        self.scale = np.maximum(mad, 1e-3)

    def __call__(self, x: np.ndarray) -> np.ndarray:
        return (x - self.med) / self.scale


def same_day_density(z: np.ndarray, days: np.ndarray, r: float) -> np.ndarray:
    """For each row, the number of OTHER rows with the same day within distance r."""
    out = np.zeros(len(z), dtype=int)
    by_day: dict[int, list[int]] = defaultdict(list)
    for i, d in enumerate(days):
        by_day[int(d)].append(i)
    for idx in by_day.values():
        if len(idx) < 2:
            continue
        a = z[idx]
        d2 = np.maximum(
            np.sum(a * a, axis=1)[:, None] + np.sum(a * a, axis=1)[None, :] - 2.0 * (a @ a.T), 0.0
        )
        within = d2 <= r * r
        np.fill_diagonal(within, False)
        out[idx] = within.sum(axis=1)
    return out


def nearest_neighbour_radius(z: np.ndarray, days: np.ndarray) -> float:
    """r: the median over rows (that have a same-day neighbour) of the distance to the nearest
    same-day neighbour."""
    nn = []
    by_day: dict[int, list[int]] = defaultdict(list)
    for i, d in enumerate(days):
        by_day[int(d)].append(i)
    for idx in by_day.values():
        if len(idx) < 2:
            continue
        a = z[idx]
        d2 = np.maximum(
            np.sum(a * a, axis=1)[:, None] + np.sum(a * a, axis=1)[None, :] - 2.0 * (a @ a.T), 0.0
        )
        np.fill_diagonal(d2, np.inf)
        nn.extend(np.sqrt(d2.min(axis=1)).tolist())
    if not nn:
        raise ValueError("no day has two identity-days; cannot set r")
    return float(np.median(nn))


def score_campaign(
    z_benign: np.ndarray,
    days_benign: np.ndarray,
    z_camp: np.ndarray,
    days_camp: np.ndarray,
    r: float,
) -> np.ndarray:
    """D10 for campaign identity-days placed among the benign identity-days of the same days
    (the campaign rows count each other and the benign rows; benign rows are not re-scored)."""
    z = np.concatenate([z_benign, z_camp])
    days = np.concatenate([days_benign, days_camp])
    return same_day_density(z, days, r)[len(z_benign) :]


def identity_days(records: Sequence, day_zero_s: float = 0.0) -> list[dict]:
    """Identity-day rows from records with absolute scheduled times (t_sched_ns)."""
    by: dict[tuple[str, int], list] = defaultdict(list)
    for rec in records:
        t = rec.t_sched_ns / 1e9
        by[(rec.identity_id, int((t - day_zero_s) // 86400))].append(rec)
    rows = []
    for (ident, day), rs in by.items():
        rs.sort(key=lambda x: x.t_sched_ns)
        t = np.array([x.t_sched_ns / 1e9 for x in rs])
        sess: dict[str, list[float]] = defaultdict(list)
        for x in rs:
            sess[x.session_id].append(x.t_sched_ns / 1e9)
        gaps = [g for v in sess.values() if len(v) > 1 for g in np.diff(sorted(v))]
        rows.append(
            {
                "identity": ident,
                "day": day,
                "requests": len(rs),
                "sessions": len(sess),
                "session_len_median": float(np.median([len(v) for v in sess.values()])),
                "gap_median_s": float(np.median(gaps)) if gaps else float("nan"),
                "span_s": float(t[-1] - t[0]),
                "start_hour": float(((t[0] - day_zero_s) % 86400) / 3600.0),
                "single_turn_frac": float(np.mean([x.turn_count == 1 for x in rs])),
            }
        )
    return rows


def births(records: Sequence) -> dict[str, float]:
    """identity -> scheduled time (s) of its first request."""
    out: dict[str, float] = {}
    for rec in records:
        t = rec.t_sched_ns / 1e9
        if rec.identity_id not in out or t < out[rec.identity_id]:
            out[rec.identity_id] = t
    return out


def birth_burst(birth_times: np.ndarray, window_s: float) -> np.ndarray:
    """D11 (amendment B3): for each birth, the number of OTHER births within +/- window_s."""
    t = np.sort(birth_times)
    order = np.argsort(birth_times, kind="mergesort")
    lo = np.searchsorted(t, t - window_s, side="left")
    hi = np.searchsorted(t, t + window_s, side="right")
    counts_sorted = hi - lo - 1
    out = np.empty(len(birth_times), dtype=int)
    out[order] = counts_sorted
    return out


def score_births(benign_births: np.ndarray, camp_births: np.ndarray, window_s: float) -> np.ndarray:
    """D11 for campaign births placed among the benign births (campaign births count each other)."""
    allb = np.concatenate([benign_births, camp_births])
    return birth_burst(allb, window_s)[len(benign_births) :]
