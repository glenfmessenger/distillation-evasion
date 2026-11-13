#!/usr/bin/env python
"""Amendment B11: the recalibrated cadence detector characterised, and a benign reference for
the any-account-flagged measure. Defender-side; no lever is changed.

(1) Cadence threshold on benign sessions of at least ten requests: held-out false-alarm rate
    over 20 account splits; a description of the benign sessions it flags; every clearing cell
    of the search and every cell of B9 scored under it, with the share of each cell's sessions
    that are scoreable (ten or more requests).
(2) Groups of 10, 50 and 100 benign accounts drawn at random from the timeline: the share of
    groups with at least one account flagged by any of the six timeline-calibrated detectors.

Writes results/aggregates/m10/<out-label>/{followup.json,table.md}.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import beta

from dev_harness.detectors import stats as D
from dev_harness.detectors.analysis import timeline_records, timeline_stats
from dev_harness.detectors.coordination import (
    Standardiser,
    birth_burst,
    births,
    features,
    identity_days,
    nearest_neighbour_radius,
    same_day_density,
)
from dev_harness.levers import shape_rate, split_heterogeneous, split_identities
from dev_harness.paths import host_repo
from dev_harness.writer import calibration_records, read_records

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m4_coordination import timeline_abs  # noqa: E402

MIN = 10


def cp(k: int, n: int) -> list[float]:
    lo = 0.0 if k == 0 else float(beta.ppf(0.025, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(0.975, k + 1, n - k))
    return [lo, hi]


def cell_score(recs: list, cal: dict) -> dict:
    sess = D.by_session(recs)
    n_all = len(sess)
    vals = [D.d3_cadence(s).value for s in sess.values() if len(s) >= MIN]
    vals = [v for v in vals if not math.isnan(v)]
    n_req = sum(len(s) for s in sess.values())
    n_req_scored = sum(len(s) for s in sess.values() if len(s) >= MIN)
    return {
        "n_sessions": n_all,
        "n_scoreable": len(vals),
        "share_sessions_scoreable": len(vals) / n_all if n_all else None,
        "share_requests_in_scoreable": n_req_scored / n_req if n_req else None,
        "flagged": float(np.mean([bool(D.fires(v, cal)) for v in vals])) if vals else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--campaign-label", default="c_real_v2")
    ap.add_argument("--search-label", default="v2_l9_search")
    ap.add_argument("--out-label", required=True)
    ap.add_argument("--cap", type=int, default=26)
    a = ap.parse_args()
    root = host_repo()
    rng = np.random.default_rng(0)

    # ---- (1a) recalibrated cadence: threshold, held-out rate, who it flags
    tl = timeline_records(root / "benign" / a.benign_label / "timeline.jsonl")
    sess = D.by_session(tl)
    rows = []
    for sid, s in sess.items():
        if len(s) >= MIN:
            v = D.d3_cadence(s).value
            if not math.isnan(v):
                rows.append(
                    (s[0].identity_id, v, len(s), float(np.mean([r.turn_count == 1 for r in s])))
                )
    vals = [r[1] for r in rows]
    cal = D.calibrate(vals, "low", 0.01)
    if abs(cal["threshold"] - 0.3053) > 2e-3:
        raise RuntimeError(f"recalibrated cadence threshold not reproduced: {cal['threshold']}")
    accs = np.array(sorted({r[0] for r in rows}))
    held = []
    for seed in range(20):
        perm = np.random.default_rng(seed).permutation(len(accs))
        A = set(accs[perm[: len(accs) // 2]].tolist())
        ca = D.calibrate([r[1] for r in rows if r[0] in A], "low", 0.01)
        vb = [r[1] for r in rows if r[0] not in A]
        k = int(sum(bool(D.fires(v, ca)) for v in vb))
        held.append({"k": k, "n": len(vb), "fpr": k / len(vb), "threshold": ca["threshold"]})
    mid = sorted(held, key=lambda h: h["fpr"])[len(held) // 2]
    flagged = [r for r in rows if D.fires(r[1], cal)]
    q = lambda v: {str(p): float(np.percentile(v, p)) for p in (10, 50, 90)}  # noqa: E731
    cadence = {
        "threshold": cal["threshold"],
        "n_sessions": cal["n_benign"],
        "n_flagged": len(flagged),
        "n_flagged_accounts": len({r[0] for r in flagged}),
        "alerts_per_day": len(flagged) / 387.0,
        "heldout_fpr_mean": float(np.mean([h["fpr"] for h in held])),
        "heldout_fpr_min": min(h["fpr"] for h in held),
        "heldout_fpr_max": max(h["fpr"] for h in held),
        "median_split_k_n": [mid["k"], mid["n"]],
        "median_split_ci": cp(mid["k"], mid["n"]),
        "flagged_session_size": q([r[2] for r in flagged]),
        "all_session_size": q([r[2] for r in rows]),
        "flagged_single_turn_share": q([r[3] for r in flagged]),
        "all_single_turn_share": q([r[3] for r in rows]),
        "flagged_cv": q([r[1] for r in flagged]),
    }
    print(
        f"cadence: thr {cal['threshold']:.4f}, flagged {len(flagged)} sessions, held-out {cadence['heldout_fpr_mean']:.4f}",
        flush=True,
    )

    # ---- (2) benign reference for the any-account-flagged measure
    hits: dict[str, bool] = defaultdict(bool)
    bvals: dict[str, list[float]] = defaultdict(list)
    stats = timeline_stats(tl)
    for s in stats:
        bvals[s.detector_id].append(s.value)
    cal_t = {det: D.calibrate(v, D.DIRECTION[det], 0.01) for det, v in bvals.items()}
    tl_accounts = sorted({s.identity_id for s in stats})
    for s in stats:
        if not math.isnan(s.value) and D.fires(s.value, cal_t[s.detector_id]):
            hits[s.identity_id] = True
    del tl, sess, stats
    babs = timeline_abs(root / "benign" / a.benign_label / "timeline_abs.jsonl")
    rows_b = identity_days(babs)
    feat_b = np.stack([features(r) for r in rows_b])
    days_b = np.array([r["day"] for r in rows_b])
    std = Standardiser(feat_b)
    zb = std(feat_b)
    r = nearest_neighbour_radius(zb, days_b)
    dens = same_day_density(zb, days_b, r)
    cal10 = D.calibrate(dens.astype(float).tolist(), "high", 0.01)
    conv = lambda acc: acc.replace("b:real:", "b:conv:", 1)  # noqa: E731
    for row, v in zip(rows_b, dens):
        if D.fires(float(v), cal10):
            hits[conv(row["identity"])] = True
    bm = births(babs)
    ba = np.array(sorted(bm))
    bt = np.array([bm[i] for i in ba])
    bur = birth_burst(bt, 600.0)
    cal11 = D.calibrate(bur.astype(float).tolist(), "high", 0.01)
    for acc, v in zip(ba, bur):
        if D.fires(float(v), cal11):
            hits[conv(acc)] = True
    flag = np.array([hits.get(acc, False) for acc in tl_accounts])
    per_account = float(flag.mean())
    groups = {}
    for g in (10, 50, 100):
        anyf = [bool(flag[rng.choice(len(flag), size=g, replace=False)].any()) for _ in range(1000)]
        groups[str(g)] = {
            "p_any": float(np.mean(anyf)),
            "expected_independent": 1 - (1 - per_account) ** g,
        }
    benign_ref = {"per_account_any_six": per_account, "groups": groups}
    print(
        f"benign reference: per-account {per_account:.4f}; groups {json.dumps(groups)}", flush=True
    )

    # ---- (1b) every clearing cell and the B9 cells under the recalibrated threshold
    benign_counts = [row["requests"] for row in rows_b]
    benign_sess = [int(x) for row in rows_b for x in [row["session_len_median"]] if x >= 1]
    del babs, rows_b, feat_b, zb
    camp, _ = calibration_records(
        read_records(root / "results" / "raw" / "campaign" / a.campaign_label / "records.jsonl")
    )
    camp = [c for c in camp if int(c.session_id.rsplit(":s", 1)[1]) < 20]
    interval = 3600.0 / (a.cap - 1)
    search = json.loads(
        (root / "results" / "aggregates" / "m4" / a.search_label / "search.json").read_text()
    )
    cells = []
    for c in search["cells"]:
        if c["clears"]:
            per = [
                cell_score(
                    split_heterogeneous(
                        camp,
                        c["n"],
                        s,
                        benign_counts,
                        benign_sess,
                        c["stagger_h"] * 3600.0,
                        interval,
                        count_cap=c["count_cap"],
                        session_mult=c["session_mult"],
                    ),
                    cal,
                )
                for s in range(5)
            ]
            cells.append(
                {
                    "source": "search",
                    "n": c["n"],
                    "count_cap": c["count_cap"],
                    "session_mult": c["session_mult"],
                    "stagger_h": c["stagger_h"],
                    "per": per,
                }
            )
    for n in (1, 10, 100):
        for capc in (26, 8, 2):
            per = [
                cell_score(shape_rate(split_identities(camp, n, s), capc, s), cal) for s in range(5)
            ]
            cells.append({"source": "price", "n": n, "cap": capc, "per": per})
    for n in (100, 1000):
        for S in (0, 6, 24, 72):
            per = [
                cell_score(
                    split_heterogeneous(
                        camp, n, s, benign_counts, benign_sess, S * 3600.0, interval
                    ),
                    cal,
                )
                for s in range(5)
            ]
            cells.append({"source": "table7", "n": n, "stagger_h": S, "per": per})
    for c in cells:

        def med(k, c=c):
            v = [p[k] for p in c["per"] if p[k] is not None]
            return float(np.median(v)) if v else None

        c["flagged"] = med("flagged")
        c["share_sessions_scoreable"] = med("share_sessions_scoreable")
        c["share_requests_in_scoreable"] = med("share_requests_in_scoreable")
    sc = [c for c in cells if c["source"] == "search"]
    p53 = {
        "n_cells": len(sc),
        "n_flagged_ge_0.9": sum(1 for c in sc if (c["flagged"] or 0) >= 0.9),
        "n_under_half_sessions_scoreable": sum(
            1 for c in sc if (c["share_sessions_scoreable"] or 0) < 0.5
        ),
        "min_share_requests_in_scoreable": min(c["share_requests_in_scoreable"] for c in sc),
        "min_share_sessions_scoreable": min(c["share_sessions_scoreable"] for c in sc),
    }
    p53["holds"] = (
        p53["n_flagged_ge_0.9"] == len(sc) and p53["n_under_half_sessions_scoreable"] >= len(sc) / 2
    )
    p54 = {"p_any_50": groups["50"]["p_any"], "holds": groups["50"]["p_any"] >= 0.5}
    out = {
        "cadence": cadence,
        "benign_reference": benign_ref,
        "cells": cells,
        "p53": p53,
        "p54": p54,
    }
    out_dir = root / "results" / "aggregates" / "m10" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "followup.json").write_text(json.dumps(out, indent=1, default=float))
    md = [
        f"Recalibrated cadence (sessions >= {MIN}): threshold {cadence['threshold']:.4f} on {cadence['n_sessions']:,} sessions; {cadence['n_flagged']} flagged from {cadence['n_flagged_accounts']} accounts ({cadence['alerts_per_day']:.2f} a day); held-out mean {cadence['heldout_fpr_mean']:.2%} [{cadence['heldout_fpr_min']:.2%}, {cadence['heldout_fpr_max']:.2%}], median split {mid['k']}/{mid['n']}; flagged session size {cadence['flagged_session_size']} (all {cadence['all_session_size']}); single-turn share {cadence['flagged_single_turn_share']} (all {cadence['all_single_turn_share']}).",
        f"Benign reference: per-account any-of-six {per_account:.2%}; groups {json.dumps(groups)}. P54 {'holds' if p54['holds'] else 'fails'}.",
        f"Search cells: {json.dumps(p53)}. P53 {'holds' if p53['holds'] else 'fails'}.",
        "| Source | n | params | flagged | sessions scoreable | requests in scoreable sessions |",
        "|---|---|---|---|---|---|",
    ]
    for c in cells:
        par = (
            f"cap {c['cap']}"
            if c["source"] == "price"
            else f"stagger {c['stagger_h']}"
            + (
                f", draw {c['count_cap']}, mult {c['session_mult']:g}"
                if c["source"] == "search"
                else ""
            )
        )
        f3 = lambda v: "n/a" if v is None else f"{v:.2f}"  # noqa: E731
        md.append(
            f"| {c['source']} | {c['n']} | {par} | {f3(c['flagged'])} | {f3(c['share_sessions_scoreable'])} | {f3(c['share_requests_in_scoreable'])} |"
        )
    (out_dir / "table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[:3]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
