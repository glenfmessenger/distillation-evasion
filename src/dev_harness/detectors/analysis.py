"""Shared pieces of the detector analyses (m3_analyse, m4_levers): timeline loading, timeline
statistics, AUC with tie-averaged ranks, the split view, and the per-detector cell summary."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from dev_harness.detectors import stats as D
from dev_harness.records import RequestRecord

BUDGETS = (0.01, 0.001)
TIMELINE_DETECTORS = ("D1", "D2", "D3", "D9")
NS = 1_000_000_000


def timeline_records(path: Path) -> list[RequestRecord]:
    out = []
    with path.open() as fh:
        for line in fh:
            d = json.loads(line)
            t = int(d["t_sched_s"] * NS)
            out.append(
                RequestRecord(
                    run_id="timeline",
                    identity_id=d["identity_id"],
                    session_id=d["session_id"],
                    request_index_in_session=d["request_index"],
                    arm=f"benign:{d['component']}",
                    t_send_ns=t,
                    t_sched_ns=t,
                    t_first_byte_ns=t,
                    t_done_ns=t,
                    prompt_tokens=None,
                    generated_tokens=None,
                    total_tokens=None,
                    reasoning_tokens=None,
                    cached_prompt_tokens=None,
                    turn_count=d["turn_index"] + 1,
                    finish_reason=None,
                    http_status=None,
                    in_flight=False,
                )
            )
    if not out:
        raise RuntimeError(f"{path}: empty timeline")
    return out


def timeline_stats(recs: list[RequestRecord]) -> list:
    out = []
    for sess in D.by_session(recs).values():
        out += [D.d3_cadence(sess), D.d9_single_turn(sess)]
    for ident in D.by_identity(recs).values():
        out += [D.d1_rate(ident), D.d2_sessions_per_day(ident)]
    return out


def auc(pos: list[float], neg: list[float], direction: str) -> float | None:
    p = np.asarray([x for x in pos if not math.isnan(x)])
    n = np.asarray([x for x in neg if not math.isnan(x)])
    if p.size == 0 or n.size == 0:
        return None
    if direction == "low":
        p, n = -p, -n
    order = np.argsort(np.concatenate([p, n]), kind="mergesort")
    ranks = np.empty(order.size)
    allv = np.concatenate([p, n])[order]
    i = 0
    while i < order.size:  # average ranks for ties
        j = i
        while j + 1 < order.size and allv[j + 1] == allv[i]:
            j += 1
        ranks[order[i : j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return float((ranks[: p.size].sum() - p.size * (p.size + 1) / 2) / (p.size * n.size))


def as_identity(recs: list[RequestRecord]) -> list[RequestRecord]:
    """Each campaign session viewed as its own identity (the identity-splitting view)."""
    return [r.model_copy(update={"identity_id": r.session_id}) for r in recs]


def summarise(det: str, bvals: list[float], cvals: list[float], budgets=BUDGETS) -> dict:
    """One detector, one campaign population against its benign values: median, AUC and, per
    budget, the calibration plus flagged count and fraction (NaN campaign units excluded)."""
    direction = D.DIRECTION[det]
    scored = [v for v in cvals if not math.isnan(v)]
    out = {
        "n_units": len(cvals),
        "n_scoreable": len(scored),
        "median": float(np.median(scored)) if scored else None,
        "auc": auc(cvals, bvals, direction),
        "budgets": {},
    }
    for b in budgets:
        cal = D.calibrate(bvals, direction, b)
        fl = [D.fires(v, cal) for v in scored]
        n_fl = int(sum(bool(x) for x in fl))
        out["budgets"][str(b)] = {
            **cal,
            "n_flagged": n_fl,
            "frac_flagged": (n_fl / len(fl)) if fl else None,
        }
    return out
