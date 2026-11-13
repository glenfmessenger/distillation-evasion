#!/usr/bin/env python
"""Amendment B12: a second benign baseline from public production API traffic.

Reads the per-client traces released with ServeGen (one CSV per client: window start in seconds,
request rate per second, coefficient of variation of inter-arrival times, fitted distribution
and its parameters; ten-minute windows). Computes the hourly-rate statistic per client and per
client-day and the distribution of per-window cadence variation. Raises on a malformed file.

Writes results/aggregates/m11/<out-label>/{api_baseline.json,table.md}.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

from dev_harness.detectors import stats as D
from dev_harness.paths import host_repo

WINDOW_S = 600
SETS = {
    "m-large": "language/m-large",
    "m-mid": "language/m-mid",
    "m-small": "language/m-small",
    "deepseek-r1": "reason/deepseek-r1",
}
CHAT_D1_THRESHOLD = 26
CHAT_CADENCE_THRESHOLD = 0.305
LEVER_CADENCE = 0.20
MIN_REQUESTS = 10
CAMPAIGN = 2000


def load_client(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ts, rate, cv = [], [], []
    with path.open() as fh:
        for line in fh:
            parts = line.strip().split(",")
            if len(parts) != 6:
                raise ValueError(f"{path}: expected 6 columns, got {len(parts)}")
            ts.append(int(parts[0]))
            rate.append(float(parts[1]))
            cv.append(float(parts[2]))
    t = np.asarray(ts)
    if len(t) < 2 or not np.all(np.diff(t) == WINDOW_S):
        raise ValueError(f"{path}: windows are not contiguous {WINDOW_S}-second steps")
    return t, np.asarray(rate), np.asarray(cv)


def q(v, ps) -> dict:
    v = np.asarray(v, dtype=float)
    return {str(p): float(np.percentile(v, p)) for p in ps}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--servegen-dir", required=True, help="path under the data root")
    ap.add_argument("--out-label", required=True)
    a = ap.parse_args()
    root = host_repo()
    base = root / a.servegen_dir / "data"
    if not base.is_dir():
        raise FileNotFoundError(base)
    out: dict = {"window_s": WINDOW_S, "sets": {}}
    pooled_client_max, pooled_day_max, pooled_cv, pooled_client_cv_median = [], [], [], []
    for name, rel in SETS.items():
        files = sorted((base / rel).glob("chunk-*-trace.csv"))
        if not files:
            raise FileNotFoundError(f"no client traces under {base / rel}")
        client_max, day_max, cvs, cv_median, spans = [], [], [], [], []
        for f in files:
            t, rate, cv = load_client(f)
            req = rate * WINDOW_S
            hourly = np.convolve(req, np.ones(6), mode="valid")  # six consecutive windows
            client_max.append(float(hourly.max()))
            per_day = 86400 // WINDOW_S
            for d0 in range(0, len(req) - per_day + 1, per_day):
                seg = req[d0 : d0 + per_day]
                if seg.sum() > 0:
                    day_max.append(float(np.convolve(seg, np.ones(6), mode="valid").max()))
            active = req >= MIN_REQUESTS
            cv_a = cv[active]
            cv_a = cv_a[np.isfinite(cv_a)]
            cvs.extend(cv_a.tolist())
            if len(cv_a):
                cv_median.append(float(np.median(cv_a)))
            spans.append(len(t) * WINDOW_S / 86400)
        cal_day = D.calibrate(day_max, "high", 0.01)
        s = {
            "n_clients": len(files),
            "days": float(np.median(spans)),
            "n_client_days": len(day_max),
            "client_max_hourly": q(client_max, (10, 50, 90, 99)),
            "share_clients_over_chat_threshold": float(
                np.mean(np.asarray(client_max) > CHAT_D1_THRESHOLD)
            ),
            "client_day_threshold_1pct": cal_day["threshold"],
            "client_day_n_exceed": cal_day["n_exceed"],
            "n_active_windows": len(cvs),
            "cv_quantiles": q(cvs, (1, 5, 25, 50, 75, 95)) if cvs else {},
            "share_windows_below_chat_cadence": float(
                np.mean(np.asarray(cvs) < CHAT_CADENCE_THRESHOLD)
            )
            if cvs
            else None,
            "share_windows_below_lever_cadence": float(np.mean(np.asarray(cvs) < LEVER_CADENCE))
            if cvs
            else None,
            "share_clients_median_below_chat_cadence": float(
                np.mean(np.asarray(cv_median) < CHAT_CADENCE_THRESHOLD)
            )
            if cv_median
            else None,
            "n_clients_with_active_windows": len(cv_median),
        }
        out["sets"][name] = s
        if name != "deepseek-r1":
            pooled_client_max += client_max
            pooled_day_max += day_max
            pooled_cv += cvs
            pooled_client_cv_median += cv_median
        print(
            f"{name}: {len(files)} clients, {len(day_max)} client-days, {len(cvs)} active windows",
            flush=True,
        )
    cal = D.calibrate(pooled_day_max, "high", 0.01)
    cal_cv = D.calibrate(pooled_cv, "low", 0.01)
    thr = cal["threshold"]
    pooled = {
        "n_clients": len(pooled_client_max),
        "n_client_days": len(pooled_day_max),
        "client_max_hourly": q(pooled_client_max, (10, 50, 90, 99)),
        "share_clients_over_chat_threshold": float(
            np.mean(np.asarray(pooled_client_max) > CHAT_D1_THRESHOLD)
        ),
        "client_day_threshold_1pct": thr,
        "client_day_n_exceed": cal["n_exceed"],
        "below_resolution": cal["below_resolution"],
        "hours_one_account_at_api_threshold": CAMPAIGN / thr if thr > 0 else math.inf,
        "campaign_in_one_hour_flagged": bool(CAMPAIGN > thr),
        "n_active_windows": len(pooled_cv),
        "cv_quantiles": q(pooled_cv, (1, 5, 25, 50, 75, 95)),
        "cadence_threshold_1pct_low": cal_cv["threshold"],
        "share_windows_below_chat_cadence": float(
            np.mean(np.asarray(pooled_cv) < CHAT_CADENCE_THRESHOLD)
        ),
        "share_windows_below_lever_cadence": float(np.mean(np.asarray(pooled_cv) < LEVER_CADENCE)),
        "share_clients_median_below_chat_cadence": float(
            np.mean(np.asarray(pooled_client_cv_median) < CHAT_CADENCE_THRESHOLD)
        ),
        "share_clients_median_below_lever_cadence": float(
            np.mean(np.asarray(pooled_client_cv_median) < LEVER_CADENCE)
        ),
        "lever_cadence_flagged_at_api_threshold": bool(LEVER_CADENCE < cal_cv["threshold"]),
    }
    out["language_pooled"] = pooled
    out["p55"] = {
        "share_clients_over_26": pooled["share_clients_over_chat_threshold"],
        "client_day_threshold": thr,
        "holds": pooled["share_clients_over_chat_threshold"] > 0.5 and thr >= 2000,
    }
    out["p56"] = {
        "share_windows_below_0.305": pooled["share_windows_below_chat_cadence"],
        "cv_q1": pooled["cv_quantiles"]["1"],
        "holds": pooled["share_windows_below_chat_cadence"] < 0.05
        and pooled["cv_quantiles"]["1"] > 0.05,
    }
    out_dir = root / "results" / "aggregates" / "m11" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "api_baseline.json").write_text(json.dumps(out, indent=1, default=float))
    md = [
        f"API baseline (ServeGen per-client traces, ten-minute windows). Language tiers pooled: {pooled['n_clients']} clients, {pooled['n_client_days']} client-days, {pooled['n_active_windows']} windows with >= {MIN_REQUESTS} requests.",
        f"Hourly rate: per-client busiest hour quantiles {json.dumps({k: round(v) for k, v in pooled['client_max_hourly'].items()})}; share of clients over the chat threshold of 26: {pooled['share_clients_over_chat_threshold']:.2%}; 1% client-day threshold {thr:,.0f} requests an hour ({cal['n_exceed']} exceedances); one account would need {pooled['hours_one_account_at_api_threshold']:.2f} h for {CAMPAIGN} requests; campaign in one hour flagged: {pooled['campaign_in_one_hour_flagged']}. P55 {'holds' if out['p55']['holds'] else 'fails'}.",
        f"Cadence: CV quantiles over active windows {json.dumps({k: round(v, 3) for k, v in pooled['cv_quantiles'].items()})}; 1% low-side threshold {cal_cv['threshold']:.3f}; share of windows below 0.305: {pooled['share_windows_below_chat_cadence']:.2%}, below 0.20: {pooled['share_windows_below_lever_cadence']:.2%}; share of clients whose median is below 0.305: {pooled['share_clients_median_below_chat_cadence']:.2%}, below 0.20: {pooled['share_clients_median_below_lever_cadence']:.2%}. P56 {'holds' if out['p56']['holds'] else 'fails'}.",
        "",
        "| Set | Clients | Client-days | Busiest hour p50 / p90 / p99 | Over 26 | 1% client-day thr | Active windows | CV p1 / p5 / p50 | Below 0.305 | Below 0.20 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for name, s in out["sets"].items():
        c, v = s["client_max_hourly"], s["cv_quantiles"]
        md.append(
            f"| {name} | {s['n_clients']} | {s['n_client_days']} | {c['50']:,.0f} / {c['90']:,.0f} / {c['99']:,.0f} | {s['share_clients_over_chat_threshold']:.2f} | {s['client_day_threshold_1pct']:,.0f} | {s['n_active_windows']} | "
            + (f"{v['1']:.2f} / {v['5']:.2f} / {v['50']:.2f}" if v else "n/a")
            + f" | {s['share_windows_below_chat_cadence']:.3f} | {s['share_windows_below_lever_cadence']:.3f} |"
        )
    (out_dir / "table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
