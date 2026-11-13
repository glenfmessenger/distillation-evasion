#!/usr/bin/env python
"""Amendment B6 items 4 and 6: sensitivity of the cross-account detectors.

Item 4 (benign volume): D10 and D11 recalibrated with the benign account population subsampled
to a fraction f (seeded draws), and the ten-account rate-capped and 100-account round-robin
cells re-scored on 50 placements under each.
Item 6 (D10 scale): the standardiser's deviation floor replaced by three alternatives; the
100-account split and the three B4 populations re-scored on the original five placements.
The registered variant must reproduce the registered thresholds and results.

Writes results/aggregates/m5/<out-label>/{sensitivity.json,table.md}.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from dev_harness.detectors import stats as D
from dev_harness.detectors.coordination import (
    birth_burst,
    births,
    features,
    identity_days,
    nearest_neighbour_radius,
    same_day_density,
    score_births,
    score_campaign,
)
from dev_harness.levers import shape_rate, split_identities
from dev_harness.paths import host_repo
from dev_harness.writer import calibration_records, read_records

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m4_coord_controls import batch_job, eval_fleet, organisation  # noqa: E402
from m4_coordination import timeline_abs  # noqa: E402

NS = 1_000_000_000


class Scaler:
    def __init__(self, x: np.ndarray, variant: str) -> None:
        self.med = np.median(x, axis=0)
        mad = np.median(np.abs(x - self.med), axis=0)
        self.mad = mad
        self.keep = np.ones(x.shape[1], dtype=bool)
        if variant == "registered":
            self.scale = np.maximum(mad, 1e-3)
        elif variant == "drop_constant":
            self.keep = mad > 0
            self.scale = np.where(self.keep, mad, 1.0)
        elif variant == "floor_1":
            self.scale = np.maximum(mad, 1.0)
        elif variant == "iqr":
            iqr = np.percentile(x, 75, axis=0) - np.percentile(x, 25, axis=0)
            self.scale = np.maximum(iqr / 1.349, 1e-3)
        else:
            raise ValueError(variant)

    def __call__(self, x: np.ndarray) -> np.ndarray:
        return ((x - self.med) / self.scale)[:, self.keep]


def _day_index(days: np.ndarray) -> dict[int, np.ndarray]:
    idx: dict[int, list[int]] = {}
    for i, d in enumerate(days):
        idx.setdefault(int(d), []).append(i)
    return {d: np.array(v) for d, v in idx.items()}


def score_campaign_restricted(zb, by_day, zc, dc, r) -> np.ndarray:
    """D10 for campaign rows among the benign rows of the same days only; equal to
    score_campaign restricted to those days (checked against it in m5_placements.py)."""
    out = np.zeros(len(zc), dtype=int)
    for d in np.unique(dc):
        mc = dc == d
        c = zc[mc]
        idx = by_day.get(int(d))
        a = np.concatenate([zb[idx], c]) if idx is not None else c
        d2 = np.maximum(
            np.sum(c * c, axis=1)[:, None] + np.sum(a * a, axis=1)[None, :] - 2.0 * (c @ a.T), 0.0
        )
        within = d2 <= r * r
        nb = len(a) - len(c)
        own = np.arange(len(c))
        within[own, nb + own] = False
        out[mc] = within.sum(axis=1)
    return out


def place(recs, seed, day_min, day_max):
    rng = np.random.default_rng(1000 + seed)
    t0 = int(rng.integers(day_min, day_max)) * 86400 * NS
    ts = [x.t_sched_ns if x.t_sched_ns is not None else x.t_send_ns for x in recs]
    base = min(ts)
    return [x.model_copy(update={"t_sched_ns": t - base + t0}) for x, t in zip(recs, ts)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--campaign-label", default="c_real_v2")
    ap.add_argument("--max-sessions", type=int, default=20)
    ap.add_argument("--out-label", required=True)
    ap.add_argument("--cap", type=int, default=26)
    ap.add_argument(
        "--fractions",
        default="0.1,0.25,0.5,1.0",
        help="fractions below one subsample accounts; integers above one overlay that many days",
    )
    ap.add_argument("--skip-scale", action="store_true", help="run the volume item only")
    ap.add_argument("--draws", type=int, default=5)
    ap.add_argument("--placements", type=int, default=50)
    a = ap.parse_args()
    root = host_repo()
    bdir = root / "benign" / a.benign_label
    man = json.loads((bdir / "manifest_abs.json").read_text())
    benign = timeline_abs(bdir / "timeline_abs.jsonl")
    rows_b = identity_days(benign)
    feat_b = np.stack([features(r) for r in rows_b])
    days_b = np.array([r["day"] for r in rows_b])
    acc_b = np.array([r["identity"] for r in rows_b])
    birth_map = births(benign)
    day_min, day_max = int(man["t_min_s"] // 86400), int(man["t_max_s"] // 86400)
    cdir = root / "results" / "raw" / "campaign" / a.campaign_label
    camp, _ = calibration_records(read_records(cdir / "records.jsonl"))
    camp = [c for c in camp if int(c.session_id.rsplit(":s", 1)[1]) < a.max_sessions]

    def cell(n, seed):
        return shape_rate(split_identities(camp, n, seed), a.cap, seed)

    # ---- item 4: benign volume -----------------------------------------------------------
    volume = []
    accounts = np.array(sorted(set(acc_b.tolist())))
    for f in [float(x) for x in a.fractions.split(",")]:
        for draw in range(1 if f >= 1.0 else a.draws):
            rng = np.random.default_rng(500 + draw)
            if f > 1.0:
                # B7 item 5: the timeline overlaid onto itself with calendar offsets, so that
                # f days' accounts fall on one day (f times the daily account volume)
                k = int(round(f))
                fb = np.concatenate([feat_b] * k)
                db = np.concatenate([days_b - j for j in range(k)])
                bt = np.concatenate(
                    [np.array(sorted(birth_map.values())) - j * 86400.0 for j in range(k)]
                )
                sc = Scaler(fb, "registered")
                zb = sc(fb)
                r = nearest_neighbour_radius(zb, db)
                dens_b = same_day_density(zb, db, r)
                by_day_f = _day_index(db)
                cal10 = D.calibrate(dens_b.astype(float).tolist(), "high", 0.01)
                bb = np.sort(bt)
                cal11 = D.calibrate(birth_burst(bb, 600.0).astype(float).tolist(), "high", 0.01)
                row = {
                    "f": f,
                    "draw": draw,
                    "n_accounts": k * len(accounts),
                    "n_identity_days": int(len(db)),
                    "radius": r,
                    "thr_d10": cal10["threshold"],
                    "thr_d11": cal11["threshold"],
                    "cells": {},
                }
                for n in (10, 100):
                    d10, d11, any10, any11 = [], [], [], []
                    for seed in range(a.placements):
                        recs = place(cell(n, seed), seed, day_min, day_max)
                        rows_c = identity_days(recs)
                        dens = score_campaign_restricted(
                            zb,
                            by_day_f,
                            sc(np.stack([features(x) for x in rows_c])),
                            np.array([x["day"] for x in rows_c]),
                            r,
                        )
                        v11 = score_births(bb, np.array(list(births(recs).values())), 600.0)
                        f10 = float(np.mean([D.fires(float(v), cal10) for v in dens]))
                        f11 = float(np.mean([D.fires(float(v), cal11) for v in v11]))
                        d10.append(f10)
                        d11.append(f11)
                        any10.append(f10 > 0)
                        any11.append(f11 > 0)
                    row["cells"][str(n)] = {
                        "d10_median": float(np.median(d10)),
                        "d11_median": float(np.median(d11)),
                        "p_any_d10": float(np.mean(any10)),
                        "p_any_d11": float(np.mean(any11)),
                    }
                volume.append(row)
                print(
                    f"overlay x{k}: thr D10 {cal10['threshold']:.0f} D11 {cal11['threshold']:.0f}; "
                    f"ten-account P(any D11) {row['cells']['10']['p_any_d11']:.2f}",
                    flush=True,
                )
                continue
            keep = (
                set(
                    rng.choice(accounts, size=int(round(f * len(accounts))), replace=False).tolist()
                )
                if f < 1.0
                else set(accounts.tolist())
            )
            m = np.array([x in keep for x in acc_b])
            sc = Scaler(feat_b[m], "registered")
            zb = sc(feat_b[m])
            db = days_b[m]
            r = nearest_neighbour_radius(zb, db)
            dens_b = same_day_density(zb, db, r)
            by_day_f = _day_index(db)
            cal10 = D.calibrate(dens_b.astype(float).tolist(), "high", 0.01)
            bb = np.array(sorted(t for i, t in birth_map.items() if i in keep))
            cal11 = D.calibrate(birth_burst(bb, 600.0).astype(float).tolist(), "high", 0.01)
            row = {
                "f": f,
                "draw": draw,
                "n_accounts": len(keep),
                "n_identity_days": int(m.sum()),
                "radius": r,
                "thr_d10": cal10["threshold"],
                "thr_d11": cal11["threshold"],
                "cells": {},
            }
            for n in (10, 100):
                d10, d11, any10, any11 = [], [], [], []
                for seed in range(a.placements):
                    recs = place(cell(n, seed), seed, day_min, day_max)
                    rows_c = identity_days(recs)
                    dens = score_campaign_restricted(
                        zb,
                        by_day_f,
                        sc(np.stack([features(x) for x in rows_c])),
                        np.array([x["day"] for x in rows_c]),
                        r,
                    )
                    v11 = score_births(bb, np.array(list(births(recs).values())), 600.0)
                    f10 = float(np.mean([D.fires(float(v), cal10) for v in dens]))
                    f11 = float(np.mean([D.fires(float(v), cal11) for v in v11]))
                    d10.append(f10)
                    d11.append(f11)
                    any10.append(f10 > 0)
                    any11.append(f11 > 0)
                row["cells"][str(n)] = {
                    "d10_median": float(np.median(d10)),
                    "d11_median": float(np.median(d11)),
                    "p_any_d10": float(np.mean(any10)),
                    "p_any_d11": float(np.mean(any11)),
                }
            volume.append(row)
            print(
                f"f={f} draw={draw}: thr D10 {cal10['threshold']:.0f} D11 {cal11['threshold']:.0f}; ten-account P(any D11) {row['cells']['10']['p_any_d11']:.2f}",
                flush=True,
            )
    q = [v for v in volume if v["f"] == 0.25]
    p33 = {
        "thr_d11_median_at_0.25": float(np.median([v["thr_d11"] for v in q])) if q else None,
        "ten_account_p_any_d11_median_at_0.25": float(
            np.median([v["cells"]["10"]["p_any_d11"] for v in q])
        )
        if q
        else None,
    }
    p33["holds"] = (
        bool(q)
        and p33["thr_d11_median_at_0.25"] <= 10
        and p33["ten_account_p_any_d11_median_at_0.25"] >= 0.5
    )

    # ---- item 6: D10 scale ---------------------------------------------------------------
    scale_rows = []
    for variant in [] if a.skip_scale else ("registered", "drop_constant", "floor_1", "iqr"):
        sc = Scaler(feat_b, variant)
        zb = sc(feat_b)
        r = nearest_neighbour_radius(zb, days_b)
        dens_b = same_day_density(zb, days_b, r)
        cal10 = D.calibrate(dens_b.astype(float).tolist(), "high", 0.01)
        row = {
            "variant": variant,
            "mad": sc.mad.tolist(),
            "features_kept": int(sc.keep.sum()),
            "radius": r,
            "thr_d10": cal10["threshold"],
            "n_exceed": cal10["n_exceed"],
            "cells": {},
        }

        def d10_frac(recs):
            rows_c = identity_days(recs)
            dens = score_campaign(
                zb,
                days_b,
                sc(np.stack([features(x) for x in rows_c])),
                np.array([x["day"] for x in rows_c]),
                r,
            )
            return float(np.mean([D.fires(float(v), cal10) for v in dens]))

        vals = [d10_frac(place(cell(100, s), s, day_min, day_max)) for s in range(5)]
        row["cells"]["roundrobin_100"] = {
            "median": float(np.median(vals)),
            "min": min(vals),
            "max": max(vals),
        }
        for name in ("organisation", "batch_job", "eval_fleet"):
            vals = []
            for s in range(5):
                rng = np.random.default_rng(2000 + s)
                t0 = float(rng.integers(day_min, day_max - 40)) * 86400
                recs = (
                    organisation(benign, rng, t0)
                    if name == "organisation"
                    else batch_job(rng, t0)
                    if name == "batch_job"
                    else eval_fleet(rng, t0, 0.39)
                )
                vals.append(d10_frac(recs))
            row["cells"][name] = {
                "median": float(np.median(vals)),
                "min": min(vals),
                "max": max(vals),
            }
        scale_rows.append(row)
        print(
            f"{variant}: r {r:.3f} thr {cal10['threshold']:.0f}; split100 {row['cells']['roundrobin_100']['median']:.2f}, batch {row['cells']['batch_job']['median']:.2f}, org {row['cells']['organisation']['median']:.2f}",
            flush=True,
        )
    reg = scale_rows[0] if scale_rows else None
    if reg is not None and reg["thr_d10"] != 35:
        raise RuntimeError(f"registered D10 threshold not reproduced: {reg['thr_d10']}")
    p36 = {
        v["variant"]: (
            v["cells"]["roundrobin_100"]["median"] >= 0.95
            and v["cells"]["batch_job"]["median"] >= 0.5
            and v["cells"]["organisation"]["median"] <= 0.10
        )
        for v in scale_rows
    }
    result = {
        "volume": volume,
        "p33": p33,
        "scale": scale_rows,
        "p36": p36,
        "feature_names": [
            "log_requests",
            "log_sessions",
            "session_len_median",
            "log_gap_median",
            "log_span",
            "start_sin",
            "start_cos",
            "single_turn_frac",
        ],
    }
    out_dir = root / "results" / "aggregates" / "m5" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "sensitivity.json").write_text(json.dumps(result, indent=1, default=float))
    md = [
        f"Benign volume sensitivity (B6 item 4): D10 and D11 recalibrated on a fraction f of benign accounts; {a.placements} placements per cell; medians over draws.\n",
        "| f | Accounts | D10 thr | D11 thr | Radius | 10 acc: D11 median, P(any D11) | 100 acc: D10 median, D11 median, P(any D10) |",
        "|---|---|---|---|---|---|---|",
    ]
    for f in sorted({v["f"] for v in volume}):
        vs = [v for v in volume if v["f"] == f]
        med = lambda k: float(np.median([x[k] for x in vs]))  # noqa: E731
        medc = lambda n, k: float(np.median([x["cells"][n][k] for x in vs]))  # noqa: E731
        md.append(
            f"| {f:g} | {vs[0]['n_accounts']} | {med('thr_d10'):.0f} | {med('thr_d11'):.0f} | {med('radius'):.3f} | "
            f"{medc('10', 'd11_median'):.2f}, {medc('10', 'p_any_d11'):.2f} | {medc('100', 'd10_median'):.2f}, {medc('100', 'd11_median'):.2f}, {medc('100', 'p_any_d10'):.2f} |"
        )
    if reg is not None:
        md += [
            "",
            f"P33: {json.dumps(p33)}",
            "",
            "D10 scale sensitivity (B6 item 6): MAD per feature "
            + ", ".join(f"{n} {v:.3g}" for n, v in zip(result["feature_names"], reg["mad"]))
            + ".",
            "| Variant | Features | Radius | Threshold | Exceed | Round-robin 100 | Organisation | Batch job | Eval fleet | P36 |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
    for v in scale_rows:
        c = v["cells"]
        fmt = lambda k: f"{c[k]['median']:.2f} [{c[k]['min']:.2f}, {c[k]['max']:.2f}]"  # noqa: E731
        md.append(
            f"| {v['variant']} | {v['features_kept']} | {v['radius']:.3f} | {v['thr_d10']:.0f} | {v['n_exceed']} | {fmt('roundrobin_100')} | {fmt('organisation')} | {fmt('batch_job')} | {fmt('eval_fleet')} | {'yes' if p36[v['variant']] else 'no'} |"
        )
    (out_dir / "table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
