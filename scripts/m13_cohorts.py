#!/usr/bin/env python
"""Amendment B14 (C): benign cohorts formed as a defender would form them.

Cohorts of 10 and of 50 benign accounts first seen in the same six-hour window of the absolute
timeline, each account scored on the six content-blind timeline and cross-account detectors at
the registered thresholds over the 48 hours from its first request (for the profile detector:
the calendar day of the first request and the next). Reported: the share of cohorts with at
least one account flagged. A sensitivity excludes windows in the first 30 days, where accounts
that existed before the corpus begins appear as new.

Writes results/aggregates/m13/<out-label>/{cohorts.json,cohorts_table.md}.
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
from dev_harness.detectors.analysis import timeline_stats
from dev_harness.detectors.coordination import (
    Standardiser,
    birth_burst,
    births,
    features,
    identity_days,
    nearest_neighbour_radius,
    same_day_density,
)
from dev_harness.paths import host_repo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m4_coordination import timeline_abs  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
NS = 1_000_000_000
HORIZON_S = 48 * 3600.0
WINDOW_S = 6 * 3600.0
DRAWS = 1000
REGISTERED = {"D1": 26.0, "D2": 48.0, "D3": 0.0226, "D10": 35.0, "D11": 15.0}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--out-label", required=True)
    a = ap.parse_args()
    root = host_repo()
    babs = timeline_abs(root / "benign" / a.benign_label / "timeline_abs.jsonl")
    bm = births(babs)
    # thresholds from the whole history, checked against the registered values
    bvals: dict[str, list[float]] = defaultdict(list)
    for s in timeline_stats(babs):
        bvals[s.detector_id].append(s.value)
    cal = {det: D.calibrate(v, D.DIRECTION[det], 0.01) for det, v in bvals.items()}
    del bvals
    rows_b = identity_days(babs)
    feat_b = np.stack([features(r) for r in rows_b])
    days_b = np.array([r["day"] for r in rows_b])
    zb = Standardiser(feat_b)(feat_b)
    dens = same_day_density(zb, days_b, nearest_neighbour_radius(zb, days_b))
    cal["D10"] = D.calibrate(dens.astype(float).tolist(), "high", 0.01)
    accs = np.array(sorted(bm))
    bt = np.array([bm[i] for i in accs])
    bur = birth_burst(bt, 600.0)
    cal["D11"] = D.calibrate(bur.astype(float).tolist(), "high", 0.01)
    for det, want in REGISTERED.items():
        if not math.isclose(cal[det]["threshold"], want, rel_tol=0.02, abs_tol=2e-4):
            raise RuntimeError(
                f"{det}: threshold {cal[det]['threshold']} is not the registered {want}"
            )
    # flags within the horizon
    early = [r for r in babs if r.t_sched_ns / NS < bm[r.identity_id] + HORIZON_S]
    share_early = len(early) / len(babs)
    del babs
    hit: dict[str, set[str]] = defaultdict(set)
    for s in timeline_stats(early):
        if not math.isnan(s.value) and D.fires(s.value, cal[s.detector_id]):
            hit[s.detector_id].add(s.identity_id)
    del early
    for row, v in zip(rows_b, dens):
        d0 = int(bm[row["identity"]] // 86400)
        if row["day"] in (d0, d0 + 1) and D.fires(float(v), cal["D10"]):
            hit["D10"].add(row["identity"])
    for acc, v in zip(accs, bur):
        if D.fires(float(v), cal["D11"]):
            hit["D11"].add(acc)
    anyhit = set().union(*hit.values())
    flag = np.array([x in anyhit for x in accs])
    t0 = bt.min()
    win = ((bt - t0) // WINDOW_S).astype(int)
    by_win: dict[int, np.ndarray] = {}
    for w in np.unique(win):
        by_win[int(w)] = np.nonzero(win == w)[0]
    rng = np.random.default_rng(0)
    out: dict = {
        "n_accounts": len(accs),
        "share_requests_within_horizon": share_early,
        "per_account_any_six_48h": float(flag.mean()),
        "per_account_by_detector": {d: len(v) / len(accs) for d, v in sorted(hit.items())},
        "n_windows": len(by_win),
        "cohorts": {},
    }
    for label, skip in (("all_windows", 0), ("excluding_first_30_days", 120)):
        out["cohorts"][label] = {}
        for g in (10, 50):
            elig = [w for w, idx in by_win.items() if len(idx) >= g and w >= skip]
            if len(elig) < 20:
                raise RuntimeError(f"only {len(elig)} windows with {g} first appearances")
            anyf, nfl = [], []
            for _ in range(DRAWS):
                idx = by_win[int(rng.choice(elig))]
                pick = rng.choice(idx, size=g, replace=False)
                anyf.append(bool(flag[pick].any()))
                nfl.append(int(flag[pick].sum()))
            pa = float(np.mean([flag[by_win[w]].mean() for w in elig]))
            out["cohorts"][label][str(g)] = {
                "n_eligible_windows": len(elig),
                "p_any": float(np.mean(anyf)),
                "flagged_per_cohort_median": float(np.median(nfl)),
                "flagged_per_cohort_p95": float(np.percentile(nfl, 95)),
                "mean_window_flag_rate": pa,
                "expected_independent": 1 - (1 - float(flag.mean())) ** g,
            }
    pl = json.loads((ROOT / "docs" / "evidence" / "m5" / "placements.json").read_text())
    rel = [
        c
        for c in pl["cells"]
        if c["source"] == "search"
        and c["summary_all"]["clears"]
        and c["summary_all"]["p_over_0.10"] <= 0.10
    ]
    fifty = min(rel, key=lambda c: c["summary_all"]["wall_clock_h_median"])
    ten = [
        c
        for c in pl["cells"]
        if c["source"] == "table5" and c["kind"] == "roundrobin" and c["n"] == 10
    ]
    if fifty["n"] != 50 or len(ten) != 1:
        raise RuntimeError("recorded headline cells not found")
    out["cells"] = {
        "50": fifty["summary_all"]["p_any_unit_flagged"],
        "10": ten[0]["summary_all"]["p_any_unit_flagged"],
    }
    p = out["cohorts"]["all_windows"]["50"]["p_any"]
    out["p61"] = {
        "p_any_50": p,
        "cell_50": out["cells"]["50"],
        "holds": out["cells"]["50"] <= p < 0.82,
    }
    out_dir = root / "results" / "aggregates" / "m13" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "cohorts.json").write_text(json.dumps(out, indent=1, default=float))
    md = [
        f"Benign cohorts first seen in the same six-hour window, scored over 48 h from first request ({share_early:.1%} of requests fall inside the horizon). Per-account any-of-six rate {flag.mean():.4f}; by detector {json.dumps({k: round(v, 4) for k, v in out['per_account_by_detector'].items()})}. P61 {'holds' if out['p61']['holds'] else 'fails'}.",
        "",
        "| Windows | Cohort size | Eligible windows | P(any account flagged) | Independent expectation | Flagged per cohort, median (p95) | Recorded cell P(any) |",
        "|---|---|---|---|---|---|---|",
    ]
    for label, d in out["cohorts"].items():
        for g, r in d.items():
            md.append(
                f"| {label} | {g} | {r['n_eligible_windows']} | {r['p_any']:.3f} | {r['expected_independent']:.3f} | {r['flagged_per_cohort_median']:.0f} ({r['flagged_per_cohort_p95']:.0f}) | {out['cells'][g]:.2f} |"
            )
    (out_dir / "cohorts_table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
