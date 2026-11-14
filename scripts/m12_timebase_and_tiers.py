#!/usr/bin/env python
"""Amendment B13: two defender-side corrections.

(1) Time base. Benign cadence thresholds are computed on reply timestamps; here every lever cell
    is scored on completion times (scheduled time plus the record's own send-to-completion
    latency) under the three cadence thresholds, beside the scheduled-time scoring.
(2) API baseline by tier and by client: clients below the campaign size, the clients that own
    the client-days above the pooled rate threshold and the low-cadence windows, and by-client
    bootstrap intervals on the pooled quantiles.

Writes results/aggregates/m12/<out-label>/{timebase.json,tiers.json,table.md}.
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
from dev_harness.detectors.analysis import timeline_records
from dev_harness.detectors.coordination import identity_days
from dev_harness.levers import shape_rate, split_heterogeneous, split_identities
from dev_harness.paths import host_repo
from dev_harness.writer import calibration_records, read_records

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m4_coordination import timeline_abs  # noqa: E402
from m11_api_baseline import MIN_REQUESTS, SETS, WINDOW_S, load_client  # noqa: E402

NS = 1_000_000_000
MINS = (3, 5, 10)
CAMPAIGN = 2000


def cv_of(times: list[float]) -> float:
    g = np.diff(np.sort(np.asarray(times)))
    return float(g.std() / g.mean()) if len(g) >= 2 and g.mean() > 0 else math.nan


def score(recs: list, cal: dict) -> dict:
    """Per session: cadence CV on scheduled times and on completion times."""
    by: dict[str, list] = defaultdict(list)
    for r in recs:
        by[r.session_id].append(r)
    out = {}
    for base in ("scheduled", "completion"):
        for k in MINS:
            vals = []
            for s in by.values():
                if len(s) < k:
                    continue
                if base == "scheduled":
                    t = [x.t_sched_ns / NS for x in s]
                else:
                    t = [(x.t_sched_ns + (x.t_done_ns - x.t_send_ns)) / NS for x in s]
                v = cv_of(t)
                if not math.isnan(v):
                    vals.append(v)
            out[f"{base}:{k}"] = {
                "n": len(vals),
                "flagged": float(np.mean([bool(D.fires(v, cal[k])) for v in vals]))
                if vals
                else None,
                "cv_median": float(np.median(vals)) if vals else None,
            }
    return out


def timebase(root: Path, benign_label: str, campaign_label: str, cap: int) -> dict:
    tl = timeline_records(root / "benign" / benign_label / "timeline.jsonl")
    cal = {}
    for k in MINS:
        vals = [D.d3_cadence(s).value for s in D.by_session(tl).values() if len(s) >= k]
        cal[k] = D.calibrate(vals, "low", 0.01)
    del tl
    babs = timeline_abs(root / "benign" / benign_label / "timeline_abs.jsonl")
    rows_b = identity_days(babs)
    benign_counts = [row["requests"] for row in rows_b]
    benign_sess = [int(x) for row in rows_b for x in [row["session_len_median"]] if x >= 1]
    del babs, rows_b
    camp, _ = calibration_records(
        read_records(root / "results" / "raw" / "campaign" / campaign_label / "records.jsonl")
    )
    camp = [c for c in camp if int(c.session_id.rsplit(":s", 1)[1]) < 20]
    lat = np.array([(c.t_done_ns - c.t_send_ns) / NS for c in camp])
    interval = 3600.0 / (cap - 1)
    search = json.loads(
        (root / "results" / "aggregates" / "m4" / "v2_l9_search" / "search.json").read_text()
    )
    cells = []
    for n in (1, 10, 100):
        for capc in (26, 8, 2):
            cells.append(
                (
                    {"source": "price", "n": n, "cap": capc},
                    lambda s, n=n, capc=capc: shape_rate(split_identities(camp, n, s), capc, s),
                )
            )
    for n in (100, 1000):
        for S in (0, 6, 24, 72):
            cells.append(
                (
                    {"source": "table7", "n": n, "stagger_h": S},
                    lambda s, n=n, S=S: split_heterogeneous(
                        camp, n, s, benign_counts, benign_sess, S * 3600.0, interval
                    ),
                )
            )
    for c in search["cells"]:
        if c["clears"]:
            cells.append(
                (
                    {
                        "source": "search",
                        "n": c["n"],
                        "count_cap": c["count_cap"],
                        "session_mult": c["session_mult"],
                        "stagger_h": c["stagger_h"],
                    },
                    lambda s, c=c: split_heterogeneous(
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
                )
            )
    out_cells = []
    for meta, build in cells:
        per = [score(build(s), cal) for s in range(5)]
        summ = {}
        for key in per[0]:
            f = [p[key]["flagged"] for p in per if p[key]["flagged"] is not None]
            cvm = [p[key]["cv_median"] for p in per if p[key]["cv_median"] is not None]
            summ[key] = {
                "flagged": float(np.median(f)) if f else None,
                "cv_median": float(np.median(cvm)) if cvm else None,
                "n": per[0][key]["n"],
            }
        out_cells.append({**meta, "summary": summ})
    paced26 = [
        c
        for c in out_cells
        if c["source"] in ("table7", "search") or (c["source"] == "price" and c["cap"] == 26)
    ]
    strict = [c for c in out_cells if c["source"] == "price" and c["cap"] in (8, 2)]
    f26 = [
        c["summary"]["completion:10"]["flagged"]
        for c in paced26
        if c["summary"]["completion:10"]["flagged"] is not None
    ]
    fst = [
        c["summary"]["completion:10"]["flagged"]
        for c in strict
        if c["summary"]["completion:10"]["flagged"] is not None
    ]
    p57 = {
        "n_cells_26_interval": len(f26),
        "n_26_under_half": sum(1 for v in f26 if v < 0.5),
        "median_flagged_26": float(np.median(f26)),
        "n_strict": len(fst),
        "n_strict_ge_0.9": sum(1 for v in fst if v >= 0.9),
        "holds": all(v < 0.5 for v in f26) and all(v >= 0.9 for v in fst),
    }
    return {
        "thresholds": {str(k): cal[k]["threshold"] for k in MINS},
        "latency_s": {
            "median": float(np.median(lat)),
            "p10": float(np.percentile(lat, 10)),
            "p90": float(np.percentile(lat, 90)),
            "std": float(lat.std()),
        },
        "interval_s": interval,
        "cells": out_cells,
        "p57": p57,
    }


def tiers(root: Path, servegen_dir: str) -> dict:
    base = root / servegen_dir / "data"
    per_client = {}
    for name, rel in SETS.items():
        for f in sorted((base / rel).glob("chunk-*-trace.csv")):
            _, rate, cv = load_client(f)
            req = rate * WINDOW_S
            hourly = np.convolve(req, np.ones(6), mode="valid")
            per_day = 86400 // WINDOW_S
            day_max = [
                float(np.convolve(req[d0 : d0 + per_day], np.ones(6), mode="valid").max())
                for d0 in range(0, len(req) - per_day + 1, per_day)
                if req[d0 : d0 + per_day].sum() > 0
            ]
            act = req >= MIN_REQUESTS
            cva = cv[act]
            cva = cva[np.isfinite(cva)]
            per_client[(name, f.name)] = {"max": float(hourly.max()), "day_max": day_max, "cv": cva}
    out = {"tiers": {}}
    lang = [k for k in per_client if k[0] != "deepseek-r1"]
    all_day = [v for k in lang for v in per_client[k]["day_max"]]
    thr = D.calibrate(all_day, "high", 0.01)["threshold"]
    all_cv = np.concatenate([per_client[k]["cv"] for k in lang])
    for name in SETS:
        ks = [k for k in per_client if k[0] == name]
        mx = np.array([per_client[k]["max"] for k in ks])
        out["tiers"][name] = {
            "n_clients": len(ks),
            "share_busiest_hour_below_campaign": float(np.mean(mx < CAMPAIGN)),
            "busiest_hour": {str(p): float(np.percentile(mx, p)) for p in (10, 25, 50, 90)},
            "n_clients_any_window_below_0.305": int(
                sum(1 for k in ks if (per_client[k]["cv"] < 0.305).any())
            ),
            "n_clients_10pct_windows_below_0.305": int(
                sum(
                    1
                    for k in ks
                    if len(per_client[k]["cv"]) and (per_client[k]["cv"] < 0.305).mean() >= 0.10
                )
            ),
        }
    owners = [k for k in lang if any(v > thr for v in per_client[k]["day_max"])]
    low = sorted(((int((per_client[k]["cv"] < 0.305).sum()), k) for k in lang), reverse=True)
    n_low = int((all_cv < 0.305).sum())
    top5 = sum(c for c, _ in low[:5])
    rng = np.random.default_rng(0)
    bs_med, bs_p10, bs_thr, bs_cvq1, bs_share = [], [], [], [], []
    for _ in range(1000):
        pick = [lang[i] for i in rng.integers(0, len(lang), size=len(lang))]
        mx = np.array([per_client[k]["max"] for k in pick])
        bs_med.append(np.median(mx))
        bs_p10.append(np.percentile(mx, 10))
        dm = [v for k in pick for v in per_client[k]["day_max"]]
        bs_thr.append(D.calibrate(dm, "high", 0.01)["threshold"])
        cvs = np.concatenate([per_client[k]["cv"] for k in pick])
        bs_cvq1.append(np.percentile(cvs, 1))
        bs_share.append(float((cvs < 0.20).mean()))
    ci = lambda v: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]  # noqa: E731
    out["language_pooled"] = {
        "rate_threshold": thr,
        "n_clients_owning_exceedances": len(owners),
        "n_low_cadence_windows": n_low,
        "share_low_windows_in_top5_clients": top5 / n_low if n_low else None,
        "ci_busiest_hour_median": ci(bs_med),
        "ci_busiest_hour_p10": ci(bs_p10),
        "ci_rate_threshold": ci(bs_thr),
        "ci_cv_q1": ci(bs_cvq1),
        "ci_share_windows_below_0.20": ci(bs_share),
    }
    r1 = out["tiers"]["deepseek-r1"]
    out["p58"] = {
        "reasoning_share_below_campaign": r1["share_busiest_hour_below_campaign"],
        "n_owners": len(owners),
        "holds": r1["share_busiest_hour_below_campaign"] > 1 / 3 and len(owners) < 20,
    }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--campaign-label", default="c_real_v2")
    ap.add_argument("--servegen-dir", default="external/ServeGen")
    ap.add_argument("--out-label", required=True)
    ap.add_argument("--cap", type=int, default=26)
    a = ap.parse_args()
    root = host_repo()
    out_dir = root / "results" / "aggregates" / "m12" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    tr = tiers(root, a.servegen_dir)
    (out_dir / "tiers.json").write_text(json.dumps(tr, indent=1, default=float))
    print(
        "tiers:",
        json.dumps({k: v for k, v in tr.items() if k != "tiers"}, default=float)[:900],
        flush=True,
    )
    print("tiers detail:", json.dumps(tr["tiers"], default=float)[:900], flush=True)
    tb = timebase(root, a.benign_label, a.campaign_label, a.cap)
    (out_dir / "timebase.json").write_text(json.dumps(tb, indent=1, default=float))
    md = [
        f"Latency (s): {json.dumps(tb['latency_s'])}; pacing interval {tb['interval_s']:.0f} s. P57: {json.dumps(tb['p57'])}",
        "| Cell | n | setting | scheduled: CV, flagged min 10 | completion: CV, flagged min 5 / 10 |",
        "|---|---|---|---|---|",
    ]
    f = lambda v: "n/a" if v is None else f"{v:.2f}"  # noqa: E731
    for c in tb["cells"]:
        s = c["summary"]
        setting = f"cap {c['cap']}" if c["source"] == "price" else f"stagger {c['stagger_h']}"
        md.append(
            f"| {c['source']} | {c['n']} | {setting} | {f(s['scheduled:10']['cv_median'])}, {f(s['scheduled:10']['flagged'])} | {f(s['completion:10']['cv_median'])}, {f(s['completion:5']['flagged'])} / {f(s['completion:10']['flagged'])} |"
        )
    (out_dir / "table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[:24]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
