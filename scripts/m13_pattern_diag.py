#!/usr/bin/env python
"""Post-hoc diagnostic for amendment B14 (B): which statistics carry the upper bound.

The logistic upper bound trained on one ordinary-prompt campaign and tested on the other seed,
with each statistic left out in turn and with each statistic alone; 20 account splits. Labelled
post hoc: run after the B14 result, to check whether the bound rests on an artefact of how the
campaigns were issued.

Writes results/aggregates/m13/<out-label>/pattern_diag.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from dev_harness.detectors import stats as D
from dev_harness.paths import host_repo
from dev_harness.writer import calibration_records, read_records

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m13_pattern import BUDGET, FEATS, SPLITS, Fit, logistic, matrix  # noqa: E402
from m6_thresholds import relabel  # noqa: E402

TRAIN, TEST = "c_real_v2", "c_real_v2_s1"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--out-label", required=True)
    a = ap.parse_args()
    root = host_repo()
    replay, _ = calibration_records(
        read_records(root / "results" / "raw" / "benign" / a.benign_label / "records.jsonl")
    )
    ref = D.BenignReference.fit(replay)
    sizes = [len(v) for v in D.by_session(replay).values() if len(v) >= D.MIN_SCOREABLE]
    xb, owners = matrix(replay, ref)
    owners = np.asarray(owners)
    xs = {}
    for label in (TRAIN, TEST):
        recs, _ = calibration_records(
            read_records(root / "results" / "raw" / "campaign" / label / "records.jsonl")
        )
        if label == TRAIN:
            recs = [r for r in recs if int(r.session_id.rsplit(":s", 1)[1]) < 20]
        xs[label], _ = matrix(relabel(recs, "benign-sized", sizes), ref)
    accs = sorted(set(owners.tolist()))
    sets = {"all": list(range(len(FEATS)))}
    for j, f in enumerate(FEATS):
        sets[f"without {f}"] = [k for k in range(len(FEATS)) if k != j]
        sets[f"only {f}"] = [j]
    res = {k: {"fpr": [], "flagged": [], "w": []} for k in sets}
    for seed in range(SPLITS):
        perm = np.random.default_rng(seed).permutation(len(accs))
        half = {accs[i] for i in perm[: len(accs) // 2]}
        ma = np.asarray([o in half for o in owners])
        fit = Fit(xb[ma])
        za, zh, zt, zs = fit.z(xb[ma]), fit.z(xb[~ma]), fit.z(xs[TRAIN]), fit.z(xs[TEST])
        for name, cols in sets.items():
            w = logistic(
                np.vstack([za[:, cols], zt[:, cols]]), np.r_[np.zeros(len(za)), np.ones(len(zt))]
            )
            sc = lambda z, w=w, cols=cols: np.hstack([z[:, cols], np.ones((len(z), 1))]) @ w  # noqa: E731
            cal = D.calibrate(sc(za).tolist(), "high", BUDGET)
            res[name]["fpr"].append(float(np.mean([bool(D.fires(v, cal)) for v in sc(zh)])))
            res[name]["flagged"].append(float(np.mean([bool(D.fires(v, cal)) for v in sc(zs)])))
            res[name]["w"].append(w[:-1].tolist())
    out = {
        "train": TRAIN,
        "test": TEST,
        "features": list(FEATS),
        "sets": {
            k: {
                "heldout_fpr_mean": float(np.mean(v["fpr"])),
                "flagged_median": float(np.median(v["flagged"])),
                "weights_median": np.median(np.asarray(v["w"]), axis=0).tolist(),
            }
            for k, v in res.items()
        },
        "campaign_medians": {f: float(np.nanmedian(xs[TEST][:, j])) for j, f in enumerate(FEATS)},
        "benign_medians": {f: float(np.nanmedian(xb[:, j])) for j, f in enumerate(FEATS)},
    }
    out_dir = root / "results" / "aggregates" / "m13" / a.out_label
    (out_dir / "pattern_diag.json").write_text(json.dumps(out, indent=1))
    for k, v in out["sets"].items():
        print(
            f"{k}: flagged {v['flagged_median']:.2f}, held-out FPR {v['heldout_fpr_mean']:.4f}, w {np.round(v['weights_median'], 2).tolist()}"
        )
    print("campaign medians", out["campaign_medians"])
    print("benign medians", out["benign_medians"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
