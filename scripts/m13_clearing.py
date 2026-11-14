#!/usr/bin/env python
"""Amendment B14 (A): clearing recomputed with the corrected cadence detector.

For every recorded lever cell, five re-schedulings: the ten-request cadence detector on
completion times (B13) with four denominators (scoreable sessions, all sessions, accounts,
requests). The corrected joint statistic is the larger of the cell's recorded joint maximum on
each placement day (docs/evidence/m5/placements.json) and its cadence fraction. No lever is
changed; the cells are those already recorded.

Writes results/aggregates/m13/<out-label>/{clearing.json,clearing_table.md}.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from dev_harness.detectors import stats as D
from dev_harness.detectors.coordination import identity_days
from dev_harness.levers import shape_rate, split_heterogeneous, split_identities
from dev_harness.paths import host_repo
from dev_harness.writer import calibration_records, read_records

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m4_coordination import timeline_abs  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
NS = 1_000_000_000
MIN_K = 10
SEEDS = 5
DENOMS = ("scoreable", "sessions", "accounts", "requests")


def cadence(recs: list, thr: float, gap_sessions: bool = False) -> dict:
    """Ten-request cadence detector on completion times, four denominators."""
    by: dict[str, list] = defaultdict(list)
    if gap_sessions:
        per_acc: dict[str, list] = defaultdict(list)
        for r in recs:
            per_acc[r.identity_id].append(r)
        for acc, rs in per_acc.items():
            ct = lambda x: (x.t_sched_ns + (x.t_done_ns - x.t_send_ns)) / NS  # noqa: E731
            rs.sort(key=ct)
            k, last = 0, ct(rs[0])
            for r in rs:
                if ct(r) - last > 1800.0:
                    k += 1
                last = ct(r)
                by[f"{acc}:g{k}"].append(r)
    else:
        for r in recs:
            by[r.session_id].append(r)
    n_sc = n_fl = req_fl = 0
    acc_fl: set[str] = set()
    for s in by.values():
        if len(s) < MIN_K:
            continue
        t = np.sort([(x.t_sched_ns + (x.t_done_ns - x.t_send_ns)) / NS for x in s])
        g = np.diff(t)
        if len(g) < 2 or g.mean() <= 0:
            continue
        n_sc += 1
        if g.std() / g.mean() < thr:
            n_fl += 1
            req_fl += len(s)
            acc_fl.add(s[0].identity_id)
    n_acc = len({r.identity_id for r in recs})
    return {
        "n_sessions": len(by),
        "n_scoreable": n_sc,
        "n_flagged": n_fl,
        "scoreable": n_fl / n_sc if n_sc else None,
        "sessions": n_fl / len(by),
        "accounts": len(acc_fl) / n_acc,
        "requests": req_fl / len(recs),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--campaign-label", default="c_real_v2")
    ap.add_argument("--out-label", required=True)
    ap.add_argument("--cap", type=int, default=26)
    ap.add_argument(
        "--daily",
        action="store_true",
        help="B18: add the hourly-rate statistic with a 24-hour window, calibrated on the timeline",
    )
    ap.add_argument(
        "--gap-sessions",
        action="store_true",
        help="B17: sessions derived per account by the 1,800 s idle-gap rule on completion times",
    )
    a = ap.parse_args()
    root = host_repo()
    tb = json.loads((ROOT / "docs" / "evidence" / "m12" / "timebase.json").read_text())
    thr = tb["thresholds"]["10"]
    fu = json.loads((ROOT / "docs" / "evidence" / "m10" / "followup.json").read_text())
    if not math.isclose(thr, fu["cadence"]["threshold"], rel_tol=1e-9):
        raise RuntimeError("ten-request cadence threshold differs between B11 and B13 evidence")
    pl = json.loads((ROOT / "docs" / "evidence" / "m5" / "placements.json").read_text())
    babs = timeline_abs(root / "benign" / a.benign_label / "timeline_abs.jsonl")
    daily_cal = None
    if a.daily:
        dvals = [
            D.d1_rate(sorted(v, key=lambda r: r.t_sched_ns), 86400.0).value
            for v in D.by_identity(babs).values()
        ]
        daily_cal = D.calibrate(dvals, "high", 0.01)
        print(
            f"24-hour rate threshold {daily_cal['threshold']} ({daily_cal['n_exceed']} of {len(dvals)} accounts above)",
            flush=True,
        )
    rows_b = identity_days(babs)
    benign_counts = [row["requests"] for row in rows_b]
    benign_sess = [int(x) for row in rows_b for x in [row["session_len_median"]] if x >= 1]
    del babs, rows_b
    camp, _ = calibration_records(
        read_records(root / "results" / "raw" / "campaign" / a.campaign_label / "records.jsonl")
    )
    camp = [c for c in camp if int(c.session_id.rsplit(":s", 1)[1]) < 20]
    interval = 3600.0 / (a.cap - 1)

    def build(cell: dict, seed: int) -> list:
        if cell["kind"] == "roundrobin":
            return shape_rate(split_identities(camp, cell["n"], seed), cell["cap"], seed)
        return split_heterogeneous(
            camp,
            cell["n"],
            seed,
            benign_counts,
            benign_sess,
            cell["stagger_h"] * 3600.0,
            interval,
            count_cap=cell.get("count_cap", 0),
            session_mult=cell.get("session_mult", 1.0),
        )

    cells = []
    # price cells: no placement dependence; joint from the recorded 50 re-schedulings
    for row in pl["table4"]:
        if not row["cap"]:
            continue
        joint = max(v["median"] for v in row["flagged"].values())
        cells.append(
            {
                "source": "price",
                "kind": "roundrobin",
                "n": row["n"],
                "cap": row["cap"],
                "hours": row["wall_clock_h"]["median"],
                "joint_days": [joint],
            }
        )
    for c in pl["cells"]:
        cells.append(
            {
                "source": c["source"],
                "kind": c["kind"],
                "n": c["n"],
                "cap": a.cap,
                "stagger_h": c.get("stagger_h"),
                "count_cap": c.get("count_cap", 0),
                "session_mult": c.get("session_mult", 1.0),
                "hours": c["summary_all"]["wall_clock_h_median"],
                "joint_days": [p["joint_max"] for p in c["per"]],
            }
        )
    out = []
    for cell in cells:
        per = [cadence(build(cell, s), thr, a.gap_sessions) for s in range(SEEDS)]
        cad = {}
        for d in DENOMS:
            v = [p[d] for p in per if p[d] is not None]
            cad[d] = float(np.median(v)) if v else None
        daily = None
        if daily_cal is not None:
            dv = []
            for s in range(SEEDS):
                fl = [
                    bool(
                        D.fires(
                            D.d1_rate(sorted(v, key=lambda r: r.t_sched_ns), 86400.0).value,
                            daily_cal,
                        )
                    )
                    for v in D.by_identity(build(cell, s)).values()
                ]
                dv.append(float(np.mean(fl)))
            daily = float(np.median(dv))
        jd = np.asarray(cell.pop("joint_days"))
        row = {
            **cell,
            "n_placements": len(jd),
            "cadence": cad,
            "daily": daily,
            "share_sessions_scoreable": float(
                np.median([p["n_scoreable"] / p["n_sessions"] for p in per])
            ),
            "registered": {
                "joint_median": float(np.median(jd)),
                "clears": bool(np.median(jd) <= 0.10),
                "p_over": float(np.mean(jd > 0.10)),
                "reliable": bool(np.mean(jd > 0.10) <= 0.10),
            },
        }
        for d in ("scoreable", "sessions"):
            c = cad[d] if cad[d] is not None else 0.0
            j = np.maximum(jd, max(c, daily or 0.0))
            row[f"corrected_{d}"] = {
                "joint_median": float(np.median(j)),
                "clears": bool(np.median(j) <= 0.10),
                "p_over": float(np.mean(j > 0.10)),
                "reliable": bool(np.mean(j > 0.10) <= 0.10),
            }
        out.append(row)
        print(
            f"{row['source']} {row['kind']} n={row['n']} cap={row.get('cap')} S={row.get('stagger_h')} "
            f"cc={row.get('count_cap')} m={row.get('session_mult')}: {row['hours']:.1f} h, cadence "
            f"{cad}, daily {daily}, registered clears {row['registered']['clears']}, corrected "
            f"{row['corrected_scoreable']['clears']} / {row['corrected_sessions']['clears']}",
            flush=True,
        )

    def tally(rows: list, key: str) -> dict:
        cl = [r for r in rows if r[key]["clears"]]
        rel = [r for r in cl if r[key]["reliable"]]
        best = min(rel, key=lambda r: r["hours"]) if rel else None
        bestc = min(cl, key=lambda r: r["hours"]) if cl else None
        pick = lambda r: (  # noqa: E731
            None
            if r is None
            else {
                k: r.get(k)
                for k in ("source", "n", "cap", "stagger_h", "count_cap", "session_mult", "hours")
            }
            | {"share_sessions_scoreable": r["share_sessions_scoreable"], "cadence": r["cadence"]}
        )
        return {
            "n_cells": len(rows),
            "n_clear": len(cl),
            "n_reliable": len(rel),
            "cheapest_clearing": pick(bestc),
            "cheapest_reliable": pick(best),
        }

    search = [r for r in out if r["source"] == "search"]
    summary = {
        grp: {
            k: tally(rows, k) for k in ("registered", "corrected_scoreable", "corrected_sessions")
        }
        for grp, rows in (
            ("search", search),
            ("price", [r for r in out if r["source"] == "price"]),
            ("table5", [r for r in out if r["source"] == "table5"]),
        )
    }
    has_sc = [r for r in out if r["cadence"]["scoreable"] is not None]

    def head(n: int, **kw) -> dict:
        m = [r for r in out if r["n"] == n and all(r.get(k) == v for k, v in kw.items())]
        if len(m) != 1:
            raise RuntimeError(f"headline cell n={n} {kw}: {len(m)} matches")
        return m[0]

    reg_rel = [r for r in search if r["registered"]["clears"] and r["registered"]["reliable"]]
    fifty = min(reg_rel, key=lambda r: r["hours"])
    heads = {
        "one_account_cap26": head(1, source="price", cap=26),
        "ten_account_cap26": head(10, source="price", cap=26),
        "fifty_reliable": fifty,
    }
    p59 = {
        "primary_n_with_scoreable": len(has_sc),
        "primary_n_clear": sum(1 for r in has_sc if r["corrected_scoreable"]["clears"]),
        "secondary_search_clear": summary["search"]["corrected_sessions"]["n_clear"],
        "secondary_heads_clear": {k: v["corrected_sessions"]["clears"] for k, v in heads.items()},
    }
    p59["holds"] = (
        p59["primary_n_clear"] == 0
        and p59["secondary_search_clear"] >= 31
        and not any(p59["secondary_heads_clear"].values())
    )
    result = {
        "gap_sessions": a.gap_sessions,
        "daily_calibration": daily_cal,
        "threshold": thr,
        "cells": out,
        "summary": summary,
        "p59": p59,
    }
    out_dir = root / "results" / "aggregates" / "m13" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "clearing.json").write_text(json.dumps(result, indent=1, default=float))
    md = [
        f"Clearing with the ten-request cadence detector on completion times (threshold {thr:.4f}) in the joint rule. P59 {'holds' if p59['holds'] else 'fails'}: {json.dumps(p59)}",
        "",
        "| Group | Rule | Cells | Clear | Reliable | Cheapest clearing (n, h) | Cheapest reliable (n, h) |",
        "|---|---|---|---|---|---|---|",
    ]
    for grp, s in summary.items():
        for k, t in s.items():
            f = lambda x: "none" if x is None else f"{x['n']}, {x['hours']:.1f}"  # noqa: E731
            md.append(
                f"| {grp} | {k} | {t['n_cells']} | {t['n_clear']} | {t['n_reliable']} | {f(t['cheapest_clearing'])} | {f(t['cheapest_reliable'])} |"
            )
    (out_dir / "clearing_table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
