#!/usr/bin/env python
"""Amendment B9: the recorded lever cells scored under the cadence thresholds recalibrated on
benign sessions of at least five and at least ten requests (B7 item 1), with the cells' own
sessions and with sessions re-derived by the idle-gap rule. Placement does not enter the cadence
statistic; five re-schedulings per cell.

Writes results/aggregates/m8/<out-label>/{cadence_cells.json,table.md}.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

from dev_harness.detectors import stats as D
from dev_harness.detectors.analysis import timeline_records
from dev_harness.levers import price, shape_rate, split_heterogeneous, split_identities
from dev_harness.paths import host_repo
from dev_harness.writer import calibration_records, read_records

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m4_coordination import timeline_abs  # noqa: E402
from m6_thresholds import relabel  # noqa: E402

NS = 1_000_000_000
MINS = (3, 5, 10)


def d3_values(recs: list, k: int) -> list[float]:
    vals = []
    for s in D.by_session(recs).values():
        if len(s) >= k:
            v = D.d3_cadence(s).value
            if not math.isnan(v):
                vals.append(v)
    return vals


def gap_sessions(recs: list) -> list:
    """Sessions re-derived per account by the 1,800 s idle-gap rule on scheduled times."""
    by: dict[str, list] = {}
    for r in recs:
        by.setdefault(r.identity_id, []).append(r)
    out = []
    for acc, rs in by.items():
        et = lambda x: x.t_sched_ns if x.t_sched_ns is not None else x.t_send_ns  # noqa: E731
        rs = sorted(rs, key=et)
        sess, last = 0, et(rs[0])
        for r in rs:
            if (et(r) - last) / NS > 1800.0:
                sess += 1
            last = et(r)
            out.append(r.model_copy(update={"session_id": f"{acc}:g{sess}"}))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--campaign-label", default="c_real_v2")
    ap.add_argument("--out-label", required=True)
    ap.add_argument("--cap", type=int, default=26)
    ap.add_argument("--seeds", type=int, default=5)
    a = ap.parse_args()
    root = host_repo()
    tl = timeline_records(root / "benign" / a.benign_label / "timeline.jsonl")
    cal = {}
    for k in MINS:
        vals = [D.d3_cadence(s).value for s in D.by_session(tl).values() if len(s) >= k]
        cal[k] = D.calibrate(vals, "low", 0.01)
    if abs(cal[3]["threshold"] - 0.0226) > 2e-4:
        raise RuntimeError("registered cadence threshold not reproduced")
    del tl
    babs = timeline_abs(root / "benign" / a.benign_label / "timeline_abs.jsonl")
    from dev_harness.detectors.coordination import identity_days

    rows_b = identity_days(babs)
    benign_counts = [row["requests"] for row in rows_b]
    benign_sess = [int(x) for row in rows_b for x in [row["session_len_median"]] if x >= 1]
    del babs, rows_b
    cdir = root / "results" / "raw" / "campaign" / a.campaign_label
    camp_all, _ = calibration_records(read_records(cdir / "records.jsonl"))
    camp = [c for c in camp_all if int(c.session_id.rsplit(":s", 1)[1]) < 20]
    interval = 3600.0 / (a.cap - 1)
    replay, _ = calibration_records(
        read_records(root / "results" / "raw" / "benign" / a.benign_label / "records.jsonl")
    )
    benign_sizes = [len(v) for v in D.by_session(replay).values() if len(v) >= D.MIN_SCOREABLE]
    del replay

    cells = []
    for n in (1, 10, 100, 1000):
        for capc in (0, 26, 8, 2):
            cells.append(
                (
                    "price",
                    f"round-robin {n}, cap {capc or 'none'}",
                    lambda s, n=n, capc=capc: shape_rate(split_identities(camp, n, s), capc, s)
                    if capc
                    else split_identities(camp, n, s),
                )
            )
    for n in (100, 1000):
        for S in (0, 6, 24, 72):
            cells.append(
                (
                    "table7",
                    f"heterogeneous {n}, stagger {S}",
                    lambda s, n=n, S=S: split_heterogeneous(
                        camp, n, s, benign_counts, benign_sess, S * 3600.0, interval
                    ),
                )
            )
    cells.append(
        (
            "search",
            "search 50, stagger 6",
            lambda s: split_heterogeneous(
                camp,
                50,
                s,
                benign_counts,
                benign_sess,
                6 * 3600.0,
                interval,
                count_cap=26,
                session_mult=10.0,
            ),
        )
    )
    cells.append(
        (
            "search",
            "search 100, stagger 6",
            lambda s: split_heterogeneous(
                camp,
                100,
                s,
                benign_counts,
                benign_sess,
                6 * 3600.0,
                interval,
                count_cap=26,
                session_mult=10.0,
            ),
        )
    )
    cells.append(
        ("unevaded", "unevaded single account", lambda s: relabel(camp, "declared", benign_sizes))
    )

    out = []
    for source, name, build in cells:
        per = []
        for seed in range(a.seeds):
            recs = build(seed)
            if source == "unevaded":
                recs = [r.model_copy(update={"t_sched_ns": r.t_send_ns}) for r in recs]
            row = {"seed": seed, "hours": price(recs)["wall_clock_s"] / 3600}
            for label, rr in (("own", recs), ("gap", gap_sessions(recs))):
                for k in MINS:
                    vals = d3_values(rr, k)
                    row[f"{label}:{k}"] = {
                        "n_sessions": len(vals),
                        "flagged": float(np.mean([bool(D.fires(v, cal[k])) for v in vals]))
                        if vals
                        else None,
                        "median": float(np.median(vals)) if vals else None,
                    }
            per.append(row)
        summ = {}
        for label in ("own", "gap"):
            for k in MINS:
                f = [
                    p[f"{label}:{k}"]["flagged"]
                    for p in per
                    if p[f"{label}:{k}"]["flagged"] is not None
                ]
                summ[f"{label}:{k}"] = {
                    "flagged_median": float(np.median(f)) if f else None,
                    "flagged_max": max(f) if f else None,
                    "n_sessions": per[0][f"{label}:{k}"]["n_sessions"],
                    "cv_median": per[0][f"{label}:{k}"]["median"],
                }
        out.append(
            {
                "source": source,
                "cell": name,
                "hours": float(np.median([p["hours"] for p in per])),
                "summary": summ,
                "per": per,
            }
        )
        print(
            f"{name}: "
            + ", ".join(
                f"{lab}:{k} {summ[f'{lab}:{k}']['flagged_median']}"
                for lab in ("own", "gap")
                for k in MINS
            ),
            flush=True,
        )
    heads = {"round-robin 1, cap 26", "round-robin 10, cap 26", "search 50, stagger 6"}
    p51 = {c["cell"]: c["summary"]["own:10"]["flagged_median"] for c in out if c["cell"] in heads}
    p51["holds"] = any((v or 0) > 0.10 for k, v in p51.items() if k != "holds")
    result = {
        "thresholds": {str(k): cal[k]["threshold"] for k in MINS},
        "n_benign_sessions": {str(k): cal[k]["n_benign"] for k in MINS},
        "cells": out,
        "p51": p51,
    }
    out_dir = root / "results" / "aggregates" / "m8" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "cadence_cells.json").write_text(json.dumps(result, indent=1, default=float))
    md = [
        "Cadence thresholds: "
        + ", ".join(f"min {k}: {cal[k]['threshold']:.4g}" for k in MINS)
        + f". P51 {'holds' if p51['holds'] else 'fails'}.",
        "| Cell | Hours | own sessions: min 3 / 5 / 10 | idle-gap sessions: min 3 / 5 / 10 | median CV (own, min 3) |",
        "|---|---|---|---|---|",
    ]
    for c in out:
        s = c["summary"]

        def fmt(lab: str) -> str:
            return " / ".join(
                "n/a"
                if s[f"{lab}:{k}"]["flagged_median"] is None
                else f"{s[f'{lab}:{k}']['flagged_median']:.2f}"
                for k in MINS
            )

        md.append(
            f"| {c['cell']} | {c['hours']:.1f} | {fmt('own')} | {fmt('gap')} | {s['own:3']['cv_median']} |"
        )
    (out_dir / "table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
