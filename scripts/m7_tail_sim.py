#!/usr/bin/env python
"""Amendment B8 items 5 and 6.

Item 5: the benign account-days above the D10 threshold described against the median
account-day; the any-detector rate on timeline accounts recomputed with D10 and D11 included.
Item 6: fifty real heavy accounts, as in the organisation control, with their first requests
collapsed into one ten-minute window, fifty placements, scored by D10 and D11.

Writes results/aggregates/m7/<out-label>/{tail_sim.json,table.md}.
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
from dev_harness.detectors.analysis import timeline_records, timeline_stats
from dev_harness.detectors.coordination import (
    Standardiser,
    birth_burst,
    births,
    features,
    identity_days,
    nearest_neighbour_radius,
    same_day_density,
    score_births,
    score_campaign,
)
from dev_harness.paths import host_repo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m4_coordination import timeline_abs  # noqa: E402

NS = 1_000_000_000


def q(v, ps=(10, 50, 90)) -> dict:
    v = np.asarray(v, dtype=float)
    return {str(p): float(np.percentile(v, p)) for p in ps} if v.size else {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--out-label", required=True)
    ap.add_argument("--placements", type=int, default=50)
    a = ap.parse_args()
    root = host_repo()
    bdir = root / "benign" / a.benign_label
    man = json.loads((bdir / "manifest_abs.json").read_text())
    benign = timeline_abs(bdir / "timeline_abs.jsonl")
    rows_b = identity_days(benign)
    feat_b = np.stack([features(r) for r in rows_b])
    days_b = np.array([r["day"] for r in rows_b])
    std = Standardiser(feat_b)
    zb = std(feat_b)
    r = nearest_neighbour_radius(zb, days_b)
    dens_b = same_day_density(zb, days_b, r)
    cal10 = D.calibrate(dens_b.astype(float).tolist(), "high", 0.01)
    if cal10["threshold"] != 35:
        raise RuntimeError("registered D10 threshold not reproduced")
    birth_map = births(benign)
    bb_acc = np.array(sorted(birth_map))
    bb = np.array([birth_map[i] for i in bb_acc])
    cal11 = D.calibrate(birth_burst(bb, 600.0).astype(float).tolist(), "high", 0.01)

    # ---- item 5(a): what D10 flags among benign account-days
    over = np.array([bool(D.fires(float(v), cal10)) for v in dens_b])
    keys = (
        "requests",
        "sessions",
        "session_len_median",
        "start_hour",
        "single_turn_frac",
        "span_s",
    )
    tail = {k: q([rows_b[i][k] for i in np.nonzero(over)[0]]) for k in keys}
    allq = {k: q([row[k] for row in rows_b]) for k in keys}
    modal = (
        sum(
            1
            for i in np.nonzero(over)[0]
            if rows_b[i]["requests"] == 1 and rows_b[i]["sessions"] == 1
        )
        / over.sum()
    )
    modal_all = sum(1 for row in rows_b if row["requests"] == 1 and row["sessions"] == 1) / len(
        rows_b
    )
    # per-account: distinct accounts among flagged account-days, and their days
    acc_over = defaultdict(int)
    for i in np.nonzero(over)[0]:
        acc_over[rows_b[i]["identity"]] += 1
    item5a = {
        "n_flagged_account_days": int(over.sum()),
        "n_flagged_accounts": len(acc_over),
        "share_single_request_single_session": modal,
        "share_single_request_single_session_all": modal_all,
        "flagged_quantiles": tail,
        "all_quantiles": allq,
    }

    # ---- item 5(b): any-detector rate on timeline accounts with D10 and D11
    tl = timeline_records(root / "benign" / a.benign_label / "timeline.jsonl")
    hits: dict[str, set[str]] = defaultdict(set)
    bvals: dict[str, list[float]] = defaultdict(list)
    stats = timeline_stats(tl)
    for s in stats:
        bvals[s.detector_id].append(s.value)
    cal_t = {det: D.calibrate(v, D.DIRECTION[det], 0.01) for det, v in bvals.items()}
    for s in stats:
        if not math.isnan(s.value) and D.fires(s.value, cal_t[s.detector_id]):
            hits[s.identity_id].add(s.detector_id)
    conv_of = lambda acc: acc.replace("b:real:", "b:conv:", 1)  # noqa: E731
    n_tl = len({s.identity_id for s in stats})
    mapped10 = 0
    for i in np.nonzero(over)[0]:
        acc = conv_of(rows_b[i]["identity"])
        hits[acc].add("D10")
        mapped10 += 1
    for acc, v in zip(bb_acc, birth_burst(bb, 600.0)):
        if D.fires(float(v), cal11):
            hits[conv_of(acc)].add("D11")
    tl_accounts = {s.identity_id for s in stats}
    any6 = sum(1 for acc in tl_accounts if hits.get(acc)) / n_tl
    any4 = sum(1 for acc in tl_accounts if (hits.get(acc) or set()) - {"D10", "D11"}) / n_tl
    by_det = {
        det: sum(1 for acc in tl_accounts if det in hits.get(acc, set())) / n_tl
        for det in ("D1", "D2", "D3", "D9", "D10", "D11")
    }
    unmapped = sum(1 for acc in hits if acc not in tl_accounts)
    item5b = {
        "n_timeline_accounts": n_tl,
        "any_four": any4,
        "any_six": any6,
        "by_detector": by_det,
        "n_abs_accounts_not_in_timeline": unmapped,
        "p48_holds": any6 <= 0.035,
    }

    # ---- item 6: real profiles, simultaneous creation
    by: dict[str, list] = defaultdict(list)
    for rec in benign:
        by[rec.identity_id].append(rec)
    heavy = [i for i, v in by.items() if len(v) >= 30]
    day_min, day_max = int(man["t_min_s"] // 86400), int(man["t_max_s"] // 86400) - 40
    d10s, d11s = [], []
    for seed in range(a.placements):
        rng = np.random.default_rng(3000 + seed)
        t0 = float(rng.integers(day_min, day_max)) * 86400 + 9 * 3600
        pick = rng.choice(len(heavy), size=50, replace=False)
        recs = []
        for k in pick:
            rs = sorted(by[heavy[k]], key=lambda x: x.t_sched_ns)
            base = rs[0].t_sched_ns / NS
            start = t0 + rng.uniform(0, 600)  # all fifty first requests within ten minutes
            for x in rs:
                recs.append(
                    x.model_copy(
                        update={
                            "identity_id": f"sim:{heavy[k]}",
                            "session_id": f"sim:{heavy[k]}:{x.session_id.rsplit(':', 1)[-1]}",
                            "t_sched_ns": int((start + (x.t_sched_ns / NS - base)) * NS),
                        }
                    )
                )
        rows_c = identity_days(recs)
        dens = score_campaign(
            zb,
            days_b,
            std(np.stack([features(x) for x in rows_c])),
            np.array([x["day"] for x in rows_c]),
            r,
        )
        v11 = score_births(bb, np.array(list(births(recs).values())), 600.0)
        d10s.append(float(np.mean([D.fires(float(v), cal10) for v in dens])))
        d11s.append(float(np.mean([D.fires(float(v), cal11) for v in v11])))
    item6 = {
        "placements": a.placements,
        "d10_median": float(np.median(d10s)),
        "d10_max": max(d10s),
        "d11_median": float(np.median(d11s)),
        "d11_min": min(d11s),
        "p49_holds": float(np.median(d11s)) >= 0.9 and float(np.median(d10s)) <= 0.10,
    }

    out = {"d10_tail": item5a, "timeline_any": item5b, "simultaneous_creation": item6}
    out_dir = root / "results" / "aggregates" / "m7" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "tail_sim.json").write_text(json.dumps(out, indent=1, default=float))
    md = [
        f"D10 benign tail: {item5a['n_flagged_account_days']} flagged account-days from {item5a['n_flagged_accounts']} accounts; single-request single-session share {modal:.2%} (all account-days {modal_all:.2%}); flagged quantiles {json.dumps(tail)}; all {json.dumps(allq)}.",
        f"Timeline any-detector: four detectors {any4:.2%}, six (with D10, D11) {any6:.2%}; by detector {json.dumps({k: round(v, 4) for k, v in by_det.items()})}; P48 {'holds' if item5b['p48_holds'] else 'fails'}.",
        f"Simultaneous creation, real profiles ({a.placements} placements): D10 median {item6['d10_median']:.2f} (max {item6['d10_max']:.2f}), D11 median {item6['d11_median']:.2f} (min {item6['d11_min']:.2f}); P49 {'holds' if item6['p49_holds'] else 'fails'}.",
    ]
    (out_dir / "table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
