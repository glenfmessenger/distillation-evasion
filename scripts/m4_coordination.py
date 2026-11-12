#!/usr/bin/env python
"""D10, the cross-identity coordination detector (PROTOCOL v2.0 amendment B2), calibrated on
every benign identity-day of the absolute timeline and scored on split campaigns placed at seeded
calendar days. Cells: round-robin split n ∈ {10, 100, 1000} × {unshaped, 26/h}; heterogeneous
split L8 at n ∈ {100, 1000} × stagger S ∈ {0, 1, 6, 24, 72} h; 5 re-schedulings each. Content-blind.

Writes results/aggregates/m4/<out-label>/{coordination.json,table.md}.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict

import numpy as np

from dev_harness.detectors import stats as D
from dev_harness.detectors.analysis import auc
from dev_harness.detectors.analysis import timeline_stats
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
from dev_harness.levers import price, shape_rate, split_heterogeneous, split_identities
from dev_harness.paths import host_repo
from dev_harness.records import RequestRecord
from dev_harness.writer import calibration_records, read_records

NS = 1_000_000_000
BUDGETS = (0.01, 0.001)


def timeline_abs(path) -> list[RequestRecord]:
    out = []
    with open(path) as fh:
        for line in fh:
            d = json.loads(line)
            t = int(d["t_abs_s"] * NS)
            out.append(
                RequestRecord(
                    run_id="timeline_abs",
                    identity_id=d["identity_id"],
                    session_id=d["session_id"],
                    request_index_in_session=d["request_index"],
                    arm="benign:real",
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
        raise RuntimeError(f"{path}: empty")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--campaign-label", required=True)
    ap.add_argument("--out-label", required=True)
    ap.add_argument("--max-sessions", type=int, default=0)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--cap", type=int, default=26, help="rate cap per hour for shaped cells (F49)")
    a = ap.parse_args()
    root = host_repo()
    bdir = root / "benign" / a.benign_label
    man = json.loads((bdir / "manifest_abs.json").read_text())
    benign = timeline_abs(bdir / "timeline_abs.jsonl")
    rows_b = identity_days(benign)
    zb_raw = np.stack([features(r) for r in rows_b])
    days_b = np.array([r["day"] for r in rows_b])
    std = Standardiser(zb_raw)
    zb = std(zb_raw)
    r = nearest_neighbour_radius(zb, days_b)
    dens_b = same_day_density(zb, days_b, r)
    cal = {str(b): D.calibrate(dens_b.astype(float).tolist(), "high", b) for b in BUDGETS}
    # D11 (amendment B3): account-birth burst at two windows, calibrated on every benign birth
    bb = np.array(sorted(births(benign).values()))
    cal11 = {}
    for w in (600, 3600):
        v = birth_burst(bb, float(w)).astype(float).tolist()
        cal11[str(w)] = {str(b): D.calibrate(v, "high", b) for b in BUDGETS}
    # D1, D2, D3, D9 on the same benign timeline, for the joint price
    bvals_t: dict[str, list[float]] = defaultdict(list)
    for st in timeline_stats(benign):
        bvals_t[st.detector_id].append(st.value)
    cal_t = {
        det: {str(b): D.calibrate(vals, D.DIRECTION[det], b) for b in BUDGETS}
        for det, vals in bvals_t.items()
    }
    benign_counts = [row["requests"] for row in rows_b]
    benign_session_lens = [int(x) for row in rows_b for x in [row["session_len_median"]] if x >= 1]
    print(
        f"benign identity-days {len(rows_b)}, r={r:.4f}, thresholds {cal['0.01']['threshold']} / {cal['0.001']['threshold']}",
        flush=True,
    )

    cdir = root / "results" / "raw" / "campaign" / a.campaign_label
    camp, _ = calibration_records(read_records(cdir / "records.jsonl"))
    if a.max_sessions:
        camp = [c for c in camp if int(c.session_id.rsplit(":s", 1)[1]) < a.max_sessions]
    gaps = sorted(
        g
        for sess in D.by_session(camp).values()
        for g in np.diff(
            sorted(x.t_sched_ns / NS if x.t_sched_ns else x.t_send_ns / NS for x in sess)
        )
    )
    native_interval = float(np.median(gaps)) if gaps else 1.0
    day_min = int(man["t_min_s"] // 86400)
    day_max = int(man["t_max_s"] // 86400)

    def place(recs, seed):
        rng = np.random.default_rng(1000 + seed)
        t0 = int(rng.integers(day_min, day_max)) * 86400 * NS
        # unshaped cells keep the campaign's client send times (t_sched_ns unset until shaped)
        ts = [x.t_sched_ns if x.t_sched_ns is not None else x.t_send_ns for x in recs]
        base = min(ts)
        return [x.model_copy(update={"t_sched_ns": t - base + t0}) for x, t in zip(recs, ts)]

    cells = []
    specs = [("roundrobin", n, shaped, None) for n in (10, 100, 1000) for shaped in (False, True)]
    specs += [("heterogeneous", n, True, S) for n in (100, 1000) for S in (0, 1, 6, 24, 72)]
    for kind, n, shaped, S in specs:
        per_seed = []
        for seed in range(a.seeds):
            if kind == "roundrobin":
                recs = split_identities(camp, n, seed)
                if shaped:
                    recs = shape_rate(recs, a.cap, seed)
            else:
                interval = 3600.0 / (a.cap - 1) if shaped else native_interval
                recs = split_heterogeneous(
                    camp, n, seed, benign_counts, benign_session_lens, S * 3600.0, interval
                )
            recs = place(recs, seed)
            rows_c = identity_days(recs)
            zc = std(np.stack([features(x) for x in rows_c]))
            dc = np.array([x["day"] for x in rows_c])
            dens = score_campaign(zb, days_b, zc, dc, r)
            flagged = {b: float(np.mean([D.fires(float(v), cal[b]) for v in dens])) for b in cal}
            cb = np.array(list(births(recs).values()))
            d11 = {}
            for w in (600, 3600):
                vals11 = score_births(bb, cb, float(w))
                d11[str(w)] = {
                    "median": float(np.median(vals11)),
                    "flagged": {
                        b: float(np.mean([D.fires(float(v), cal11[str(w)][b]) for v in vals11]))
                        for b in cal
                    },
                }
            others = {}
            cvals_t: dict[str, list[float]] = defaultdict(list)
            for st in timeline_stats(recs):
                cvals_t[st.detector_id].append(st.value)
            for det, vals in cvals_t.items():
                sc = [v for v in vals if not math.isnan(v)]
                others[det] = {
                    b: (float(np.mean([D.fires(v, cal_t[det][b]) for v in sc])) if sc else None)
                    for b in cal
                }
            joint_max = max(
                [flagged["0.01"], d11["600"]["flagged"]["0.01"]]
                + [v["0.01"] for v in others.values() if v["0.01"] is not None]
            )
            ids_flagged = defaultdict(bool)
            for row, v in zip(rows_c, dens):
                ids_flagged[row["identity"]] |= bool(D.fires(float(v), cal["0.01"]))
            per_seed.append(
                {
                    "seed": seed,
                    "n_identity_days": len(rows_c),
                    "median_density": float(np.median(dens)),
                    "auc": auc(dens.astype(float).tolist(), dens_b.astype(float).tolist(), "high"),
                    "flagged": flagged,
                    "frac_identities_any_day_flagged": float(np.mean(list(ids_flagged.values()))),
                    "d11": d11,
                    "timeline_detectors": others,
                    "joint_max_flagged_1pct": joint_max,
                    "price": price(recs),
                }
            )
        cells.append({"kind": kind, "n": n, "shaped": shaped, "stagger_h": S, "per_seed": per_seed})
        print(f"cell {kind} n={n} shaped={shaped} S={S}: done", flush=True)

    out_dir = root / "results" / "aggregates" / "m4" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "benign_label": a.benign_label,
        "campaign_label": a.campaign_label,
        "max_sessions": a.max_sessions,
        "n_benign_identity_days": len(rows_b),
        "n_benign_identities": len({row["identity"] for row in rows_b}),
        "radius": r,
        "calibration": cal,
        "calibration_d11": cal11,
        "calibration_timeline": cal_t,
        "benign_density_quantiles": {
            q: float(np.quantile(dens_b, q)) for q in (0.5, 0.9, 0.99, 0.999)
        },
        "native_interval_s": native_interval,
        "cap_per_hour": a.cap,
        "cells": cells,
    }
    (out_dir / "coordination.json").write_text(json.dumps(result, indent=1))
    md = [
        f"D10 coordination (benign `{a.benign_label}`, {len(rows_b)} benign identity-days, r = {r:.3f}; 1% threshold {cal['0.01']['threshold']:.0f} neighbours, 0.1% {cal['0.001']['threshold']:.0f}; campaign `{a.campaign_label}`, {a.seeds} re-schedulings). Flagged = fraction of campaign identity-days over the threshold, median [min, max]; identities = fraction of campaign identities with at least one flagged day.\n",
        "| Split | n | Shaped | Stagger h | Identity-days | Median density | Flagged 1% | Flagged 0.1% | Identities flagged | AUC | Wall-clock h | D11 10 min | D11 60 min | D1 | D2 | D3 | D9 | Joint max |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    hot = []
    for c in cells:
        s = c["per_seed"]
        f1 = sorted(x["flagged"]["0.01"] for x in s)
        f01 = sorted(x["flagged"]["0.001"] for x in s)
        idf = sorted(x["frac_identities_any_day_flagged"] for x in s)
        au = sorted(x["auc"] for x in s if x["auc"] is not None)
        wc = sorted(x["price"]["wall_clock_s"] / 3600 for x in s)
        m = lambda v: sorted(v)[len(v) // 2]  # noqa: E731 - median over re-schedulings
        if au and m(au) >= 0.95:
            hot.append((c["kind"], c["n"], c["shaped"], c["stagger_h"], round(m(au), 3)))
        md.append(
            f"| {c['kind']} | {c['n']} | {'yes' if c['shaped'] else 'no'} | {'' if c['stagger_h'] is None else c['stagger_h']} | "
            f"{s[0]['n_identity_days']} | {m([x['median_density'] for x in s]):.0f} | {m(f1):.2f} [{f1[0]:.2f}, {f1[-1]:.2f}] | "
            f"{m(f01):.2f} [{f01[0]:.2f}, {f01[-1]:.2f}] | {m(idf):.2f} | {m(au):.3f} | {m(wc):.1f} | "
            f"{m([x['d11']['600']['flagged']['0.01'] for x in s]):.2f} | "
            f"{m([x['d11']['3600']['flagged']['0.01'] for x in s]):.2f} | "
            + " | ".join(
                (
                    f"{m([x['timeline_detectors'][d]['0.01'] for x in s]):.2f}"
                    if all(x["timeline_detectors"].get(d, {}).get("0.01") is not None for x in s)
                    else "n/a"
                )
                for d in ("D1", "D2", "D3", "D9")
            )
            + f" | {m([x['joint_max_flagged_1pct'] for x in s]):.2f} |"
        )
    (out_dir / "table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    if hot:
        print("\nTOO-GOOD STOP RULE: AUC >= 0.95 in", hot)
    return 0


if __name__ == "__main__":
    sys.exit(main())
