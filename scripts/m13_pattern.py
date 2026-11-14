#!/usr/bin/env python
"""Amendment B14 (B): pattern statistics on comparable sessions.

Units: benign replay sessions with at least ten completed records, and each campaign cut into
sessions of benign sizes (the B5 rule, at least ten records). (i) Each statistic with a
two-sided threshold at a 1% total budget. (ii) A joint score fitted on benign sessions only
(squared Mahalanobis distance on the standardised statistics). (iii) An upper bound: a logistic
regression trained on benign sessions and one campaign, tested on the others. (ii) and (iii) are
fitted on one half of the benign accounts and their false-alarm rate measured on the other, 20
splits. Length reference distributions are those of the full replay, as registered.

Writes results/aggregates/m13/<out-label>/{pattern.json,pattern_table.md}.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from dev_harness.detectors import stats as D
from dev_harness.detectors.analysis import auc
from dev_harness.paths import host_repo
from dev_harness.writer import calibration_records, read_records

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m6_thresholds import CAMPAIGNS, d5_no_truncation, relabel  # noqa: E402

FEATS = ("D3", "D4", "D5nt", "D6", "D7", "D9")
MIN_K = 10
SPLITS = 20
BUDGET = 0.01
RIDGE = 1e-6


def feats(sess: list, ref: D.BenignReference) -> list[float]:
    return [
        D.d3_cadence(sess).value,
        D.d4_output_shape(sess, ref).value,
        d5_no_truncation(sess),
        D.d6_prompt_shape(sess, ref).value,
        D.d7_cache_share(sess).value,
        D.d9_single_turn(sess).value,
    ]


def matrix(recs: list, ref: D.BenignReference) -> tuple[np.ndarray, list[str]]:
    rows, owners = [], []
    for s in D.by_session(recs).values():
        if len(s) >= MIN_K:
            rows.append(feats(s, ref))
            owners.append(s[0].identity_id)
    return np.asarray(rows, dtype=float), owners


class Fit:
    """Imputation, standardisation and inverse covariance from benign rows only."""

    def __init__(self, x: np.ndarray) -> None:
        self.med = np.nanmedian(x, axis=0)
        z = self.fill(x)
        self.mu, self.sd = z.mean(axis=0), z.std(axis=0)
        self.sd[self.sd == 0] = 1.0
        zz = (z - self.mu) / self.sd
        self.prec = np.linalg.inv(np.cov(zz, rowvar=False) + RIDGE * np.eye(x.shape[1]))

    def fill(self, x: np.ndarray) -> np.ndarray:
        return np.where(np.isnan(x), self.med, x)

    def z(self, x: np.ndarray) -> np.ndarray:
        return (self.fill(x) - self.mu) / self.sd

    def d2(self, x: np.ndarray) -> np.ndarray:
        z = self.z(x)
        return np.einsum("ij,jk,ik->i", z, self.prec, z)


def logistic(x: np.ndarray, y: np.ndarray, l2: float = 1.0, iters: int = 50) -> np.ndarray:
    """Class-balanced L2 logistic regression by Newton steps; returns weights with intercept."""
    xa = np.hstack([x, np.ones((len(x), 1))])
    w = np.zeros(xa.shape[1])
    sw = np.where(y == 1, 0.5 / max(y.sum(), 1), 0.5 / max((1 - y).sum(), 1)) * len(y)
    reg = l2 * np.eye(xa.shape[1])
    reg[-1, -1] = 0.0
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-np.clip(xa @ w, -30, 30)))
        g = xa.T @ (sw * (p - y)) + reg @ w
        h = (xa * (sw * p * (1 - p))[:, None]).T @ xa + reg + 1e-9 * np.eye(xa.shape[1])
        step = np.linalg.solve(h, g)
        w -= step
        if np.abs(step).max() < 1e-8:
            break
    return w


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
    benign_sizes = [len(v) for v in D.by_session(replay).values() if len(v) >= D.MIN_SCOREABLE]
    xb, owners = matrix(replay, ref)
    owners = np.asarray(owners)
    if len(xb) < 1000:
        raise RuntimeError(f"only {len(xb)} benign sessions of at least {MIN_K} records")
    camps = {}
    for spec in CAMPAIGNS:
        label, _, k = spec.partition(":")
        recs, _ = calibration_records(
            read_records(root / "results" / "raw" / "campaign" / label / "records.jsonl")
        )
        if k:
            recs = [r for r in recs if int(r.session_id.rsplit(":s", 1)[1]) < int(k)]
        xc, _ = matrix(relabel(recs, "benign-sized", benign_sizes), ref)
        if len(xc) == 0:
            raise RuntimeError(f"{spec}: no size-matched sessions of at least {MIN_K} records")
        camps[spec] = xc
    out: dict = {
        "n_benign_sessions": len(xb),
        "n_benign_accounts": len(set(owners.tolist())),
        "n_campaign_sessions": {k: len(v) for k, v in camps.items()},
        "missing_share_benign": {f: float(np.isnan(xb[:, j]).mean()) for j, f in enumerate(FEATS)},
    }
    # ---- (i) two-sided per statistic, in sample
    two = {}
    for j, f in enumerate(FEATS):
        b = xb[:, j]
        b = b[~np.isnan(b)]
        lo = D.calibrate(b.tolist(), "low", BUDGET / 2)
        hi = D.calibrate(b.tolist(), "high", BUDGET / 2)
        n_ex = lo["n_exceed"] + hi["n_exceed"]
        row = {
            "low": lo["threshold"],
            "high": hi["threshold"],
            "n_benign": len(b),
            "n_exceed": n_ex,
            "below_resolution": n_ex < 10,
            "realised": n_ex / len(b),
            "campaigns": {},
        }
        for spec, xc in camps.items():
            c = xc[:, j]
            c = c[~np.isnan(c)]
            fl = [bool(D.fires(v, lo)) or bool(D.fires(v, hi)) for v in c]
            row["campaigns"][spec] = {
                "n": len(c),
                "flagged": float(np.mean(fl)) if len(c) else None,
                "flagged_low": float(np.mean([bool(D.fires(v, lo)) for v in c]))
                if len(c)
                else None,
                "auc_high": auc(c.tolist(), b.tolist(), "high") if len(c) else None,
                "median": float(np.median(c)) if len(c) else None,
            }
        row["benign_median"] = float(np.median(b))
        two[f] = row
    out["two_sided"] = two
    # ---- (ii) and (iii), held out by account
    accs = sorted(set(owners.tolist()))
    joint = {"fpr": [], "campaigns": {k: [] for k in camps}}
    oracle = {tr: {"fpr": [], "campaigns": {k: [] for k in camps}} for tr in camps}
    for seed in range(SPLITS):
        perm = np.random.default_rng(seed).permutation(len(accs))
        half = {accs[i] for i in perm[: len(accs) // 2]}
        ma = np.asarray([o in half for o in owners])
        fit = Fit(xb[ma])
        cal = D.calibrate(fit.d2(xb[ma]).tolist(), "high", BUDGET)
        joint["fpr"].append(float(np.mean([bool(D.fires(v, cal)) for v in fit.d2(xb[~ma])])))
        for spec, xc in camps.items():
            joint["campaigns"][spec].append(
                float(np.mean([bool(D.fires(v, cal)) for v in fit.d2(xc)]))
            )
        za, zh = fit.z(xb[ma]), fit.z(xb[~ma])
        for tr, xt in camps.items():
            zt = fit.z(xt)
            w = logistic(np.vstack([za, zt]), np.r_[np.zeros(len(za)), np.ones(len(zt))])
            sc = lambda z: np.hstack([z, np.ones((len(z), 1))]) @ w  # noqa: E731
            calo = D.calibrate(sc(za).tolist(), "high", BUDGET)
            oracle[tr]["fpr"].append(float(np.mean([bool(D.fires(v, calo)) for v in sc(zh)])))
            for spec, xc in camps.items():
                oracle[tr]["campaigns"][spec].append(
                    float(np.mean([bool(D.fires(v, calo)) for v in sc(fit.z(xc))]))
                )

    def summ(d: dict) -> dict:
        return {
            "heldout_fpr_mean": float(np.mean(d["fpr"])),
            "heldout_fpr_min": float(np.min(d["fpr"])),
            "heldout_fpr_max": float(np.max(d["fpr"])),
            "campaigns": {
                k: {"median": float(np.median(v)), "min": float(np.min(v)), "max": float(np.max(v))}
                for k, v in d["campaigns"].items()
            },
        }

    out["joint"] = summ(joint)
    out["oracle"] = {tr: summ(d) for tr, d in oracle.items()}
    j = out["joint"]
    ordinary = ("c_real_v2:20", "c_real_v2_s1", "c_instr_v2")
    out["p60"] = {
        "heldout_fpr_mean": j["heldout_fpr_mean"],
        "bench": j["campaigns"]["pilot_baseline"]["median"],
        "others": {k: j["campaigns"][k]["median"] for k in ordinary},
    }
    out["p60"]["holds"] = (
        abs(j["heldout_fpr_mean"] - BUDGET) <= 0.005
        and out["p60"]["bench"] > 0.10
        and all(v <= 0.10 for v in out["p60"]["others"].values())
    )
    out["stop_rule_triggered"] = any(
        j["campaigns"][k]["median"] > 0.5 for k in ("c_real_v2:20", "c_real_v2_s1")
    )
    out_dir = root / "results" / "aggregates" / "m13" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "pattern.json").write_text(json.dumps(out, indent=1, default=float))
    md = [
        f"Pattern statistics on comparable sessions: {len(xb)} benign sessions of at least {MIN_K} records from {out['n_benign_accounts']} accounts; campaign sessions cut to benign sizes: {json.dumps(out['n_campaign_sessions'])}. P60 {'holds' if out['p60']['holds'] else 'fails'}; stop rule {'TRIGGERED' if out['stop_rule_triggered'] else 'not triggered'}.",
        "",
        "(i) Two-sided thresholds at 1% total (in sample). Flagged fraction, either side (low side alone).",
        "| Statistic | Low | High | Benign exceed | " + " | ".join(camps) + " |",
        "|---|---|---|---|" + "---|" * len(camps),
    ]
    for f, r in two.items():
        md.append(
            f"| {f} | {r['low']:.3g} | {r['high']:.3g} | {r['n_exceed']}{' (below res.)' if r['below_resolution'] else ''} | "
            + " | ".join(
                "n/a"
                if r["campaigns"][s]["flagged"] is None
                else f"{r['campaigns'][s]['flagged']:.2f} ({r['campaigns'][s]['flagged_low']:.2f}); AUC {r['campaigns'][s]['auc_high']:.2f}"
                for s in camps
            )
            + " |"
        )
    md += [
        "",
        "(ii) Benign-fit joint score and (iii) upper bound, held out over 20 account splits: median flagged [min, max].",
        "| Score | Held-out FPR mean [min, max] | " + " | ".join(camps) + " |",
        "|---|---|" + "---|" * len(camps),
    ]

    def line(name: str, s: dict) -> str:
        return (
            f"| {name} | {s['heldout_fpr_mean']:.4f} [{s['heldout_fpr_min']:.4f}, {s['heldout_fpr_max']:.4f}] | "
            + " | ".join(
                f"{s['campaigns'][k]['median']:.2f} [{s['campaigns'][k]['min']:.2f}, {s['campaigns'][k]['max']:.2f}]"
                for k in camps
            )
            + " |"
        )

    md.append(line("joint (benign only)", out["joint"]))
    for tr, s in out["oracle"].items():
        md.append(line(f"upper bound, trained on {tr}", s))
    (out_dir / "pattern_table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
