#!/usr/bin/env python
"""Amendment B6 item 1: held-out calibration and the any-detector benign rate.

For every detector the benign units are split at random into two halves by account (20 seeded
splits). The threshold is set on one half at the 1% budget and the false-alarm rate measured on
the other with an exact Clopper-Pearson 95% interval; the unevaded campaigns' flagged fractions
are recomputed under each held-out threshold. The pooled benign reference (D4, D6, D8) is refit
on the calibration half. Content detectors use the committed per-unit statistics (their
reference pool is the full benign set, stated in the output). Also: the per-account rate at
which benign traffic trips any content-blind detector at the registered thresholds.

Writes results/aggregates/m5/<out-label>/{heldout.json,table.md}.
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
from dev_harness.detectors.analysis import TIMELINE_DETECTORS, timeline_records, timeline_stats
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
from dev_harness.writer import calibration_records, read_records

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m4_coordination import timeline_abs  # noqa: E402

REPLAY_DETS = ("D4", "D5", "D6", "D7", "D8", "D8b")
CONTENT_DIR = {"C1": "high", "C2": "high", "C2low": "low", "C3": "high", "B1": "high", "B2": "high"}
BUDGET = 0.01


def cp_interval(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    lo = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
    return lo, hi


def halves(accounts: list[str], seed: int) -> tuple[set[str], set[str]]:
    acc = np.array(sorted(accounts))
    perm = np.random.default_rng(seed).permutation(len(acc))
    h = len(acc) // 2
    return set(acc[perm[:h]].tolist()), set(acc[perm[h:]].tolist())


def heldout_fpr(vals_a: list[float], vals_b: list[float], direction: str) -> dict:
    cal = D.calibrate(vals_a, direction, BUDGET)
    scored = [v for v in vals_b if not math.isnan(v)]
    k = int(sum(bool(D.fires(v, cal)) for v in scored))
    lo, hi = cp_interval(k, len(scored))
    return {
        "threshold": cal["threshold"],
        "n_cal": cal["n_benign"],
        "n_exceed_cal": cal["n_exceed"],
        "n_test": len(scored),
        "k_test": k,
        "fpr": k / len(scored) if scored else None,
        "ci": [lo, hi],
    }


def flagged_frac(vals: list[float], cal: dict) -> float | None:
    scored = [v for v in vals if not math.isnan(v)]
    if not scored:
        return None
    return float(np.mean([bool(D.fires(v, cal)) for v in scored]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--campaigns", default="pilot_baseline,c_real_v2:20,c_real_v2_s1,c_instr_v2")
    ap.add_argument("--content-unit-stats", required=True, help="committed unit_stats.jsonl")
    ap.add_argument("--out-label", required=True)
    ap.add_argument("--splits", type=int, default=20)
    a = ap.parse_args()
    root = host_repo()

    # ---- benign statistics -------------------------------------------------------------
    tl = timeline_records(root / "benign" / a.benign_label / "timeline.jsonl")
    tl_stats = timeline_stats(tl)
    tl_vals: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for s in tl_stats:
        tl_vals[s.detector_id].append((s.identity_id, s.value))
    tl_accounts = sorted({s.identity_id for s in tl_stats})
    replay, _ = calibration_records(
        read_records(root / "results" / "raw" / "benign" / a.benign_label / "records.jsonl")
    )
    replay_by_acc: dict[str, list] = defaultdict(list)
    for r in replay:
        replay_by_acc[r.identity_id].append(r)
    replay_accounts = sorted(replay_by_acc)
    babs = timeline_abs(root / "benign" / a.benign_label / "timeline_abs.jsonl")
    rows_b = identity_days(babs)
    feat_b = np.stack([features(r) for r in rows_b])
    days_b = np.array([r["day"] for r in rows_b])
    acc_rows = np.array([r["identity"] for r in rows_b])
    birth_map = births(babs)
    birth_acc = np.array(sorted(birth_map))
    birth_t = np.array([birth_map[i] for i in birth_acc])
    content_rows = [json.loads(line) for line in open(a.content_unit_stats, encoding="utf-8")]
    content_benign = [r for r in content_rows if r["population"] == "benign"]
    content_dets = [d for d in CONTENT_DIR if d in content_benign[0]]

    # ---- campaigns (declared sessions, as Table II) -------------------------------------
    camps: dict[str, list] = {}
    for spec in a.campaigns.split(","):
        label, _, k = spec.partition(":")
        recs, _ = calibration_records(
            read_records(root / "results" / "raw" / "campaign" / label / "records.jsonl")
        )
        if k:
            recs = [r for r in recs if int(r.session_id.rsplit(":s", 1)[1]) < int(k)]
        camps[spec] = recs
    camp_tl_stats = {name: timeline_stats(recs) for name, recs in camps.items()}

    # ---- registered (in-sample) calibration for reference -------------------------------
    ref_all = D.BenignReference.fit(replay)
    replay_stats_all = [
        s for s in D.all_statistics(replay, ref_all) if s.detector_id in REPLAY_DETS
    ]
    registered: dict[str, dict] = {}
    for det, pairs in tl_vals.items():
        registered[det] = D.calibrate([v for _, v in pairs], D.DIRECTION[det], BUDGET)
    rv: dict[str, list[float]] = defaultdict(list)
    for s in replay_stats_all:
        rv[s.detector_id].append(s.value)
    for det, vals in rv.items():
        registered[det] = D.calibrate(vals, D.DIRECTION[det], BUDGET)
    std_all = Standardiser(feat_b)
    z_all = std_all(feat_b)
    r_all = nearest_neighbour_radius(z_all, days_b)
    dens_all = same_day_density(z_all, days_b, r_all)
    registered["D10"] = D.calibrate(dens_all.astype(float).tolist(), "high", BUDGET)
    burst_all = birth_burst(birth_t, 600.0)
    registered["D11"] = D.calibrate(burst_all.astype(float).tolist(), "high", BUDGET)
    for det in content_dets:
        registered[det] = D.calibrate(
            [r[det] if r[det] is not None else math.nan for r in content_benign],
            CONTENT_DIR[det],
            BUDGET,
        )
    camp_registered: dict[str, dict[str, float | None]] = defaultdict(dict)
    for name, recs in camps.items():
        cv: dict[str, list[float]] = defaultdict(list)
        for s in camp_tl_stats[name]:
            cv[s.detector_id].append(s.value)
        for s in D.all_statistics(recs, ref_all):
            if s.detector_id in REPLAY_DETS:
                cv[s.detector_id].append(s.value)
        for det, vals in cv.items():
            camp_registered[name][det] = flagged_frac(vals, registered[det])

    # ---- held-out splits ---------------------------------------------------------------
    per_split: list[dict] = []
    for seed in range(a.splits):
        out: dict = {"seed": seed, "detectors": {}, "campaigns": defaultdict(dict)}
        A, B = halves(tl_accounts, seed)
        for det, pairs in tl_vals.items():
            va = [v for i, v in pairs if i in A]
            vb = [v for i, v in pairs if i in B]
            out["detectors"][det] = heldout_fpr(va, vb, D.DIRECTION[det])
            cal = D.calibrate(va, D.DIRECTION[det], BUDGET)
            for name in camps:
                vals = [s.value for s in camp_tl_stats[name] if s.detector_id == det]
                out["campaigns"][name][det] = flagged_frac(vals, cal)
        Ar, Br = halves(replay_accounts, seed)
        rec_a = [r for acc in Ar for r in replay_by_acc[acc]]
        rec_b = [r for acc in Br for r in replay_by_acc[acc]]
        ref_a = D.BenignReference.fit(rec_a)
        sa: dict[str, list[float]] = defaultdict(list)
        sb: dict[str, list[float]] = defaultdict(list)
        for s in D.all_statistics(rec_a, ref_a):
            if s.detector_id in REPLAY_DETS:
                sa[s.detector_id].append(s.value)
        for s in D.all_statistics(rec_b, ref_a):
            if s.detector_id in REPLAY_DETS:
                sb[s.detector_id].append(s.value)
        camp_stats_a = {
            name: [s for s in D.all_statistics(recs, ref_a) if s.detector_id in REPLAY_DETS]
            for name, recs in camps.items()
        }
        for det in REPLAY_DETS:
            out["detectors"][det] = heldout_fpr(sa[det], sb[det], D.DIRECTION[det])
            cal = D.calibrate(sa[det], D.DIRECTION[det], BUDGET)
            for name in camps:
                vals = [s.value for s in camp_stats_a[name] if s.detector_id == det]
                out["campaigns"][name][det] = flagged_frac(vals, cal)
        # D10: standardiser and radius from half A; density over the whole population
        Ad, Bd = halves(sorted(set(acc_rows.tolist())), seed)
        ma = np.array([i in Ad for i in acc_rows])
        std_a = Standardiser(feat_b[ma])
        z = std_a(feat_b)
        r_a = nearest_neighbour_radius(z[ma], days_b[ma])
        dens = same_day_density(z, days_b, r_a).astype(float)
        out["detectors"]["D10"] = heldout_fpr(dens[ma].tolist(), dens[~ma].tolist(), "high")
        out["detectors"]["D10"]["radius"] = r_a
        Ab, Bb = halves(birth_acc.tolist(), seed)
        mb = np.array([i in Ab for i in birth_acc])
        bur = burst_all.astype(float)
        out["detectors"]["D11"] = heldout_fpr(bur[mb].tolist(), bur[~mb].tolist(), "high")
        # content: committed per-unit values, split by unit
        Ac, Bc = halves([r["unit"] for r in content_benign], seed)
        for det in content_dets:
            va = [
                r[det] if r[det] is not None else math.nan
                for r in content_benign
                if r["unit"] in Ac
            ]
            vb = [
                r[det] if r[det] is not None else math.nan
                for r in content_benign
                if r["unit"] in Bc
            ]
            out["detectors"][det] = heldout_fpr(va, vb, CONTENT_DIR[det])
            cal = D.calibrate(va, CONTENT_DIR[det], BUDGET)
            for pop in sorted(
                {r["population"] for r in content_rows if r["population"] != "benign"}
            ):
                if not (pop.endswith(":identity") or pop.endswith(":block100")):
                    continue
                vals = [
                    r[det] if r[det] is not None else math.nan
                    for r in content_rows
                    if r["population"] == pop
                ]
                out["campaigns"][pop][det] = flagged_frac(vals, cal)
        per_split.append(out)
        print(f"split {seed}: done", flush=True)

    # ---- summaries ---------------------------------------------------------------------
    dets = list(per_split[0]["detectors"])
    summary = {}
    for det in dets:
        f = [
            s["detectors"][det]["fpr"] for s in per_split if s["detectors"][det]["fpr"] is not None
        ]
        thr = [s["detectors"][det]["threshold"] for s in per_split]
        mid = sorted(per_split, key=lambda s: s["detectors"][det]["fpr"] or 0)[len(per_split) // 2]
        summary[det] = {
            "registered_threshold": registered[det]["threshold"],
            "registered_n_exceed": registered[det]["n_exceed"],
            "registered_below_resolution": registered[det]["below_resolution"],
            "registered_realised_fpr": registered[det]["n_exceed"] / registered[det]["n_benign"],
            "heldout_fpr_mean": float(np.mean(f)) if f else None,
            "heldout_fpr_min": float(min(f)) if f else None,
            "heldout_fpr_max": float(max(f)) if f else None,
            "median_split_ci": mid["detectors"][det]["ci"],
            "median_split_k_n": [mid["detectors"][det]["k_test"], mid["detectors"][det]["n_test"]],
            "threshold_min": float(min(thr)),
            "threshold_max": float(max(thr)),
            "p25_mean_in_band": (0.005 <= float(np.mean(f)) <= 0.015) if f else None,
        }
    camp_summary: dict[str, dict] = defaultdict(dict)
    names = sorted({n for s in per_split for n in s["campaigns"]})
    for name in names:
        for det in dets:
            vals = [s["campaigns"][name].get(det) for s in per_split if name in s["campaigns"]]
            vals = [v for v in vals if v is not None]
            if not vals:
                continue
            if det in CONTENT_DIR:
                pop_vals = [
                    r[det] if r[det] is not None else math.nan
                    for r in content_rows
                    if r["population"] == name
                ]
                reg = flagged_frac(pop_vals, registered[det]) if pop_vals else None
            else:
                reg = camp_registered.get(name, {}).get(det)
            med = float(np.median(vals))
            camp_summary[name][det] = {
                "registered": reg,
                "heldout_median": med,
                "heldout_min": float(min(vals)),
                "heldout_max": float(max(vals)),
                "p26_within_0.05": (abs(med - reg) <= 0.05) if reg is not None else None,
            }

    # ---- any-detector benign rate at the registered thresholds -------------------------
    def fires_reg(det: str, v: float) -> bool:
        return bool(D.fires(v, registered[det]))

    tl_hits: dict[str, set[str]] = defaultdict(set)
    for s in tl_stats:
        if not math.isnan(s.value) and fires_reg(s.detector_id, s.value):
            tl_hits[s.identity_id].add(s.detector_id)
    n_tl = len(tl_accounts)
    any_tl = {
        "n_accounts": n_tl,
        "any": len(tl_hits) / n_tl,
        "by_detector": {
            det: sum(det in h for h in tl_hits.values()) / n_tl for det in TIMELINE_DETECTORS
        },
        "n_detectors_hist": {
            str(k): sum(len(h) == k for h in tl_hits.values()) / n_tl for k in (1, 2, 3, 4)
        },
    }
    rp_hits: dict[str, set[str]] = {acc: set(tl_hits.get(acc, set())) for acc in replay_accounts}
    for s in replay_stats_all:
        if not math.isnan(s.value) and fires_reg(s.detector_id, s.value):
            rp_hits[s.identity_id].add(s.detector_id)
    n_rp = len(replay_accounts)
    any_rp_pattern = sum(bool(h) for h in rp_hits.values()) / n_rp
    abs_of = {acc: acc.replace("b:conv:", "b:real:", 1) for acc in replay_accounts}
    d10_flag_acc: set[str] = set()
    for row, v in zip(rows_b, dens_all):
        if fires_reg("D10", float(v)):
            d10_flag_acc.add(row["identity"])
    d11_flag_acc = {i for i, v in zip(birth_acc, burst_all) if fires_reg("D11", float(v))}
    for acc in replay_accounts:
        if abs_of[acc] in d10_flag_acc:
            rp_hits[acc].add("D10")
        if abs_of[acc] in d11_flag_acc:
            rp_hits[acc].add("D11")
    n_mapped = sum(abs_of[acc] in birth_map for acc in replay_accounts)
    any_rp = {
        "n_accounts": n_rp,
        "n_mapped_to_abs_timeline": n_mapped,
        "any_pattern_volume": any_rp_pattern,
        "any_incl_cross_account": sum(bool(h) for h in rp_hits.values()) / n_rp,
        "by_detector": {
            det: sum(det in h for h in rp_hits.values()) / n_rp
            for det in list(TIMELINE_DETECTORS) + list(REPLAY_DETS) + ["D10", "D11"]
        },
        "mean_sessions_per_account": float(
            np.mean([len({r.session_id for r in v}) for v in replay_by_acc.values()])
        ),
    }
    p27 = {
        "timeline_in_band": 0.02 <= any_tl["any"] <= 0.10,
        "replay_in_band": 0.05 <= any_rp["any_incl_cross_account"] <= 0.30,
    }

    result = {
        "splits": a.splits,
        "budget": BUDGET,
        "content_note": "content per-unit statistics are the committed values; their reference pool is the full benign set, only the threshold is held out",
        "detectors": summary,
        "campaigns": camp_summary,
        "any_detector": {"timeline_accounts": any_tl, "replayed_accounts": any_rp, "p27": p27},
        "per_split": per_split,
    }
    out_dir = root / "results" / "aggregates" / "m5" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "heldout.json").write_text(json.dumps(result, indent=1, default=float))
    md = [
        f"Held-out calibration ({a.splits} seeded half splits by account, 1% budget). Registered = in-sample threshold on all benign units.\n",
        "| Detector | Registered thr | Realised in-sample | Held-out FPR mean [min, max] | Median-split k/n and exact 95% CI | Held-out thr range | P25 band |",
        "|---|---|---|---|---|---|---|",
    ]
    for det, s in summary.items():
        md.append(
            f"| {det}{'†' if s['registered_below_resolution'] else ''} | {s['registered_threshold']:.4g} | {s['registered_realised_fpr']:.2%} | "
            f"{s['heldout_fpr_mean']:.2%} [{s['heldout_fpr_min']:.2%}, {s['heldout_fpr_max']:.2%}] | "
            f"{s['median_split_k_n'][0]}/{s['median_split_k_n'][1]} [{s['median_split_ci'][0]:.2%}, {s['median_split_ci'][1]:.2%}] | "
            f"[{s['threshold_min']:.4g}, {s['threshold_max']:.4g}] | {'yes' if s['p25_mean_in_band'] else 'no'} |"
        )
    md += [
        "",
        "| Campaign | Detector | Registered flagged | Held-out median [min, max] | Within 0.05 |",
        "|---|---|---|---|---|",
    ]
    for name, dd in camp_summary.items():
        for det, s in dd.items():
            md.append(
                f"| {name} | {det} | {'n/a' if s['registered'] is None else format(s['registered'], '.2f')} | "
                f"{s['heldout_median']:.2f} [{s['heldout_min']:.2f}, {s['heldout_max']:.2f}] | "
                f"{'n/a' if s['p26_within_0.05'] is None else ('yes' if s['p26_within_0.05'] else 'no')} |"
            )
    md += [
        "",
        f"Any-detector benign rate at the registered 1% thresholds: timeline accounts (D1, D2, D3, D9) {any_tl['any']:.2%} of {n_tl}; "
        f"replayed accounts {any_rp['any_pattern_volume']:.2%} over the ten pattern and volume detectors and {any_rp['any_incl_cross_account']:.2%} with D10 and D11, of {n_rp} "
        f"(mean {any_rp['mean_sessions_per_account']:.1f} sessions per account).",
        "By detector (timeline): "
        + ", ".join(f"{d} {v:.2%}" for d, v in any_tl["by_detector"].items()),
        "By detector (replayed): "
        + ", ".join(f"{d} {v:.2%}" for d, v in any_rp["by_detector"].items()),
    ]
    (out_dir / "table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
