#!/usr/bin/env python
"""Amendment B16: four defender-side re-analyses of recorded data.

(1) d10half   held-out profile detector with everything taken within the half.
(2) constructed  the labelled-campaign classifier applied to the constructed accounts' sessions.
(3) clientday  API tiers: share of client-days whose busiest hour is below the campaign's size.
(4) realonly  per-unit content thresholds on the 1,000 real calibration accounts.

Writes results/aggregates/m15/<out-label>/<part>.json.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from dev_harness.benign import read_schedule
from dev_harness.detectors import stats as D
from dev_harness.detectors.coordination import (
    Standardiser,
    features,
    identity_days,
    nearest_neighbour_radius,
    same_day_density,
)
from dev_harness.paths import host_repo
from dev_harness.writer import calibration_records, read_records

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m4_content import DETS, DIRECTION, N_MATCH  # noqa: E402
from m4_coordination import timeline_abs  # noqa: E402
from m6_thresholds import relabel  # noqa: E402
from m11_api_baseline import SETS, WINDOW_S, load_client  # noqa: E402
from m13_pattern import BUDGET, SPLITS, Fit, logistic, matrix  # noqa: E402

CAMPAIGN = 2000
CONSTRUCTED = {
    "b:eval:": "evaluation harness",
    "b:batc:": "batch summarisation",
    "b:agen:": "agent loop",
}


def d10half(root: Path, label: str) -> dict:
    rows = identity_days(timeline_abs(root / "benign" / label / "timeline_abs.jsonl"))
    feat = np.stack([features(r) for r in rows])
    days = np.array([r["day"] for r in rows])
    acc = np.array([r["identity"] for r in rows])
    accs = sorted(set(acc.tolist()))
    thr, fpr, rad = [], [], []
    for seed in range(SPLITS):
        perm = np.random.default_rng(seed).permutation(len(accs))
        half = {accs[i] for i in perm[: len(accs) // 2]}
        ma = np.array([a in half for a in acc])
        std = Standardiser(feat[ma])
        za, zb = std(feat[ma]), std(feat[~ma])
        r = nearest_neighbour_radius(za, days[ma])
        cal = D.calibrate(same_day_density(za, days[ma], r).astype(float).tolist(), "high", BUDGET)
        dens_b = same_day_density(zb, days[~ma], r).astype(float)
        thr.append(cal["threshold"])
        rad.append(r)
        fpr.append(float(np.mean([bool(D.fires(v, cal)) for v in dens_b])))
    out = {
        "threshold_min": min(thr),
        "threshold_max": max(thr),
        "threshold_median": float(np.median(thr)),
        "heldout_fpr_mean": float(np.mean(fpr)),
        "heldout_fpr_min": min(fpr),
        "heldout_fpr_max": max(fpr),
        "radius_median": float(np.median(rad)),
    }
    out["p66"] = {
        "holds": 15 <= out["threshold_min"]
        and out["threshold_max"] <= 25
        and abs(out["heldout_fpr_mean"] - BUDGET) <= 0.005
    }
    return out


def constructed(root: Path, label: str) -> dict:
    replay, _ = calibration_records(
        read_records(root / "results" / "raw" / "benign" / label / "records.jsonl")
    )
    ref = D.BenignReference.fit(replay)
    sizes = [len(v) for v in D.by_session(replay).values() if len(v) >= D.MIN_SCOREABLE]
    xb, owners = matrix(replay, ref)
    owners = np.asarray(owners)
    kind = np.asarray(
        [next((v for k, v in CONSTRUCTED.items() if o.startswith(k)), "real") for o in owners]
    )
    real = kind == "real"
    recs, _ = calibration_records(
        read_records(root / "results" / "raw" / "campaign" / "c_real_v2" / "records.jsonl")
    )
    recs = [r for r in recs if int(r.session_id.rsplit(":s", 1)[1]) < 20]
    xt, _ = matrix(relabel(recs, "benign-sized", sizes), ref)
    accs = sorted(set(owners[real].tolist()))
    res = defaultdict(list)
    for seed in range(SPLITS):
        perm = np.random.default_rng(seed).permutation(len(accs))
        half = {accs[i] for i in perm[: len(accs) // 2]}
        ma = np.asarray([o in half for o in owners]) & real
        fit = Fit(xb[ma])
        za = fit.z(xb[ma])
        w = logistic(np.vstack([za, fit.z(xt)]), np.r_[np.zeros(len(za)), np.ones(len(xt))])
        sc = lambda x: np.hstack([fit.z(x), np.ones((len(x), 1))]) @ w  # noqa: E731
        cal = D.calibrate(sc(xb[ma]).tolist(), "high", BUDGET)
        res["heldout_real"].append(
            float(np.mean([bool(D.fires(v, cal)) for v in sc(xb[real & ~ma])]))
        )
        for k in CONSTRUCTED.values():
            m = kind == k
            if m.any():
                res[k].append(float(np.mean([bool(D.fires(v, cal)) for v in sc(xb[m])])))
    out = {
        "n_sessions": {k: int((kind == k).sum()) for k in ["real", *CONSTRUCTED.values()]},
        "n_accounts": {
            k: len(set(owners[kind == k].tolist())) for k in ["real", *CONSTRUCTED.values()]
        },
        "flagged": {
            k: {"median": float(np.median(v)), "min": min(v), "max": max(v)} for k, v in res.items()
        },
    }
    b = out["flagged"].get("batch summarisation")
    out["p67"] = {
        "batch_median": b["median"] if b else None,
        "holds": bool(b and b["median"] >= 0.5),
    }
    return out


def clientday(root: Path, servegen_dir: str) -> dict:
    base = root / servegen_dir / "data"
    out: dict = {"tiers": {}}
    pooled = []
    per_day = 86400 // WINDOW_S
    for name, rel in SETS.items():
        files = sorted((base / rel).glob("chunk-*-trace.csv"))
        if not files:
            raise FileNotFoundError(base / rel)
        dm = []
        for f in files:
            _, rate, _ = load_client(f)
            req = rate * WINDOW_S
            for d0 in range(0, len(req) - per_day + 1, per_day):
                seg = req[d0 : d0 + per_day]
                if seg.sum() > 0:
                    dm.append(float(np.convolve(seg, np.ones(6), mode="valid").max()))
        out["tiers"][name] = {
            "n_client_days": len(dm),
            "share_below_campaign": float(np.mean(np.asarray(dm) < CAMPAIGN)),
            "median_busiest_hour": float(np.median(dm)),
        }
        if name != "deepseek-r1":
            pooled += dm
    out["language_pooled"] = {
        "n_client_days": len(pooled),
        "share_below_campaign": float(np.mean(np.asarray(pooled) < CAMPAIGN)),
        "median_busiest_hour": float(np.median(pooled)),
    }
    out["p68"] = {"holds": out["language_pooled"]["share_below_campaign"] < 0.10}
    return out


def _get(row: dict, det: str) -> float:
    """Per-unit value; the low-side statistic shares the discrepancy value; older files lack C3."""
    v = row.get("C2" if det == "C2low" and "C2low" not in row else det)
    return math.nan if v is None else float(v)


def reasoning(root: Path, servegen_dir: str) -> dict:
    """B18 (2): the reasoning tier's own order-statistic thresholds on its client-days."""
    base = root / servegen_dir / "data" / SETS["deepseek-r1"]
    files = sorted(base.glob("chunk-*-trace.csv"))
    if not files:
        raise FileNotFoundError(base)
    dm = []
    for f in files:
        _, rate, _ = load_client(f)
        dm.append(float(np.convolve(rate * WINDOW_S, np.ones(6), mode="valid").max()))
    out = {
        "n_client_days": len(dm),
        "share_above_campaign": float(np.mean(np.asarray(dm) > CAMPAIGN)),
    }
    for b in (0.01, 0.10):
        c = D.calibrate(dm, "high", b)
        out[str(b)] = {
            "threshold": c["threshold"],
            "n_exceed": c["n_exceed"],
            "below_resolution": c["below_resolution"],
        }
    out["p72"] = {
        "holds": out["0.01"]["threshold"] > CAMPAIGN
        and out["0.1"]["threshold"] > CAMPAIGN
        and out["0.01"]["below_resolution"]
    }
    return out


def realonly(root: Path, label: str) -> dict:
    sched = read_schedule(root / "benign" / label / "replay_schedule.jsonl")
    n: dict[str, int] = defaultdict(int)
    for r in sched:
        n[r.identity_id] += 1
    units = [i for i, k in n.items() if k >= N_MATCH]
    real = np.asarray([i.startswith(("b:conv:", "b:code:")) for i in units])
    if len(units) != 1061 or int(real.sum()) != 1000:
        raise RuntimeError(f"{len(units)} calibration accounts, {int(real.sum())} real")
    agg = root / "results" / "aggregates"
    sources = {
        "all": agg / "m4" / "v2_content_all",
        "s1": agg / "m4" / "v2_content_s1",
        "instr": agg / "m4" / "v2_content_instr",
        "ctrl": agg / "m4" / "v2_content_ctrl",
        "oasst": agg / "m4" / "v2_content_oasst",
        "no_robots": agg / "m4" / "v2_content_no_robots",
        "pooled_real_only": agg / "m5" / "b14_real_only",
        "small_merges": agg / "m5" / "b15_small_merges",
    }
    out: dict = {
        "n_all": len(units),
        "n_real": int(real.sum()),
        "calibration": {},
        "populations": {},
    }
    first = True
    max_change = 0.0
    for src, path in sources.items():
        pops: dict[str, list[dict]] = defaultdict(list)
        with (path / "unit_stats.jsonl").open() as fh:
            for line in fh:
                d = json.loads(line)
                pops[d["population"]].append(d)
        ben = pops.pop("benign")
        if len(ben) != len(units):
            raise RuntimeError(f"{src}: {len(ben)} benign units")
        val = lambda rows, det: [  # noqa: E731
            _get(r, det) for r in rows
        ]
        dets = [d for d in DETS if not all(math.isnan(x) for x in val(ben, d))]
        ca = {d: D.calibrate(val(ben, d), DIRECTION[d], BUDGET) for d in dets}
        cr = {
            d: D.calibrate([v for v, m in zip(val(ben, d), real) if m], DIRECTION[d], BUDGET)
            for d in dets
        }
        out.setdefault("calibration_by_source", {})[src] = {
            d: {
                "threshold_all": ca[d]["threshold"],
                "threshold_real": cr[d]["threshold"],
                "n_exceed_real": cr[d]["n_exceed"],
                "below_resolution_real": cr[d]["below_resolution"],
            }
            for d in dets
        }
        if first:
            first = False
            for d in dets:
                out["calibration"][d] = {
                    "threshold_all": ca[d]["threshold"],
                    "threshold_real": cr[d]["threshold"],
                    "n_exceed_real": cr[d]["n_exceed"],
                    "below_resolution_real": cr[d]["below_resolution"],
                    "realised_real": cr[d]["n_exceed"] / int(real.sum()),
                }
        for pop, rows in pops.items():
            if "split_n" in pop:
                continue
            key = f"{src}:{pop}"
            out["populations"][key] = {}
            for d in dets:
                v = [x for x in val(rows, d) if not math.isnan(x)]
                fa = float(np.mean([bool(D.fires(x, ca[d])) for x in v])) if v else None
                fr = float(np.mean([bool(D.fires(x, cr[d])) for x in v])) if v else None
                out["populations"][key][d] = {"n": len(v), "all": fa, "real": fr}
                if d != "B1" and fa is not None:
                    max_change = max(max_change, abs(fa - fr))
    out["max_change_excluding_B1"] = max_change
    out["p69"] = {"max_change": max_change, "holds": max_change <= 0.05}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "part", choices=["d10half", "constructed", "clientday", "realonly", "reasoning"]
    )
    ap.add_argument("--benign-label", default="m3_v1")
    ap.add_argument("--servegen-dir", default="external/ServeGen")
    ap.add_argument("--out-label", required=True)
    a = ap.parse_args()
    root = host_repo()
    res = {
        "d10half": lambda: d10half(root, a.benign_label),
        "constructed": lambda: constructed(root, a.benign_label),
        "clientday": lambda: clientday(root, a.servegen_dir),
        "realonly": lambda: realonly(root, a.benign_label),
        "reasoning": lambda: reasoning(root, a.servegen_dir),
    }[a.part]()
    out_dir = root / "results" / "aggregates" / "m15" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{a.part}.json").write_text(json.dumps(res, indent=1, default=float))
    show = {k: v for k, v in res.items() if k not in ("populations",)}
    print(json.dumps(show, indent=1, default=float)[:2500])
    return 0


if __name__ == "__main__":
    sys.exit(main())
