#!/usr/bin/env python
"""Amendment B14 (D)(i), step 2: content statistics on natural shared-address units.

Every address with two or more replayed real accounts and at least 30 prompts between them is
one unit (address_groups.json, from m13_address_groups.py). The unit's merged prompt stream,
ordered by each account's own relative time, is scored by the per-unit content statistics
against the registered thresholds (those recomputed and checked by m5_pooled_control.py), with
the unit's accounts excluded from the reference draws. Fewer than 20 units: reported untested.

Writes results/aggregates/m13/<out-label>/{address_units.json,address_units_table.md}.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.cluster.vq import kmeans2
from scipy.stats import beta

from dev_harness.benign import read_schedule
from dev_harness.detectors.content import (
    b1_membership,
    b2_template_reuse,
    benchmark_index,
    c2_mmd_score,
    c3_diversity,
)
from dev_harness.detectors.stats import fires
from dev_harness.paths import host_repo
from dev_harness.pool import read_jsonl

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m4_content import DETS, K, N_MATCH, N_SUB, c1_stat  # noqa: E402

MIN_UNITS = 20


def cp(k: int, n: int) -> list[float]:
    lo = 0.0 if k == 0 else float(beta.ppf(0.025, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(0.975, k + 1, n - k))
    return [lo, hi]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--calibration", required=True, help="pooled.json of m5_pooled_control.py")
    ap.add_argument("--out-label", required=True)
    a = ap.parse_args()
    root = host_repo()
    sched = read_schedule(root / "benign" / a.benign_label / "replay_schedule.jsonl")
    by_ident: dict[str, list] = {}
    for r in sched:
        by_ident.setdefault(r.identity_id, []).append(r)
    cache = root / "results" / "aggregates" / "m4" / "_embeddings"
    e_all = np.load(cache / f"benign_{a.benign_label}_all.npy")
    owners = np.asarray([i for i, v in by_ident.items() for _ in v])
    times = np.asarray([x.t_sched_s for v in by_ident.values() for x in v])
    texts = [x.user_content for v in by_ident.values() for x in v]
    if len(e_all) != len(owners):
        raise RuntimeError(f"embedding cache {len(e_all)} rows, schedule {len(owners)} prompts")
    big = {i for i, v in by_ident.items() if len(v) >= N_MATCH}
    m30 = np.asarray([o in big for o in owners])
    b_emb = np.load(cache / f"benign_{a.benign_label}.npy")
    if len(b_emb) != int(m30.sum()) or not np.allclose(b_emb[:200], e_all[m30][:200], atol=1e-4):
        raise RuntimeError("the two embedding caches do not line up")
    own30 = owners[m30]
    calj = json.loads(Path(a.calibration).read_text())
    cal, sigma = calj["calibration"], calj["sigma"]
    cent, b_lab = kmeans2(b_emb.astype(np.float64), K, minit="++", seed=0)
    pop_hist = {k: v / len(b_lab) for k, v in Counter(b_lab.tolist()).items()}
    pool_index = benchmark_index(it.prompt for it in read_jsonl(root / "pool" / "pool.jsonl"))
    groups = json.loads((root / "benign" / a.benign_label / "address_groups.json").read_text())[
        "groups"
    ]
    key_to_ident = {i.split(":", 2)[2]: i for i in by_ident if i.startswith(("b:conv:", "b:code:"))}
    n_multi = sum(1 for v in groups.values() if len(v) >= 2)
    rows = []
    for g, (_, keys) in enumerate(sorted(groups.items())):
        if len(keys) < 2:
            continue
        members = [key_to_ident[k] for k in keys]
        idx = np.nonzero(np.isin(owners, members))[0]
        if len(idx) < N_MATCH:
            continue
        idx = idx[np.argsort(times[idx], kind="stable")]
        emb = e_all[idx]
        d2 = ((emb[:, None, :].astype(np.float64) - cent[None, :, :]) ** 2).sum(axis=2)
        lab = d2.argmin(axis=1)
        pool = b_emb[~np.isin(own30, members)]
        prompts = [texts[i] for i in idx]
        r = np.random.default_rng(30_000 + g)
        c2 = c2_mmd_score(emb, pool, sigma, r, N_MATCH, N_SUB)
        s = {
            "C1": c1_stat(lab, pop_hist, r, N_MATCH),
            "C2": c2,
            "C2low": c2,
            "C3": c3_diversity(emb, r, N_MATCH, N_SUB),
            "B1": b1_membership(prompts, pool_index),
            "B2": b2_template_reuse(prompts),
        }
        rows.append(
            {
                "n_accounts": len(members),
                "n_prompts": len(idx),
                "n_accounts_ge_30": sum(1 for m in members if m in big),
                "largest_account_share": max(len(by_ident[m]) for m in members) / len(idx),
                **s,
            }
        )
    out: dict = {
        "n_addresses": len(groups),
        "n_addresses_multi_account": n_multi,
        "n_units": len(rows),
        "untested": len(rows) < MIN_UNITS,
        "units": rows,
        "detectors": {},
    }
    for d in DETS:
        v = [r[d] for r in rows if not math.isnan(r[d])]
        k = sum(bool(fires(x, cal[d])) for x in v)
        out["detectors"][d] = {
            "threshold": cal[d]["threshold"],
            "n_scoreable": len(v),
            "n_flagged": k,
            "flagged": k / len(v) if v else None,
            "ci95": cp(k, len(v)) if v else None,
            "median": float(np.median(v)) if v else None,
        }
    if rows:
        out["size"] = {
            "accounts_median": float(np.median([r["n_accounts"] for r in rows])),
            "accounts_max": max(r["n_accounts"] for r in rows),
            "prompts_median": float(np.median([r["n_prompts"] for r in rows])),
            "largest_account_share_median": float(
                np.median([r["largest_account_share"] for r in rows])
            ),
        }
    f = out["detectors"]["C2low"]["flagged"]
    out["p62"] = {
        "flagged_C2low": f,
        "outcome": "untested" if out["untested"] else ("held" if f < 0.10 else "failed"),
    }
    out_dir = root / "results" / "aggregates" / "m13" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "address_units.json").write_text(json.dumps(out, indent=1, default=float))
    md = [
        f"Natural shared-address units: {len(groups)} addresses among the replayed real accounts, {n_multi} with two or more accounts, {len(rows)} with at least {N_MATCH} prompts between them. Sizes: {json.dumps(out.get('size'))}. P62 {out['p62']['outcome']}.",
        "",
        "| Detector | Threshold | Scoreable | Flagged | 95% CI | Median |",
        "|---|---|---|---|---|---|",
    ]
    for d, r in out["detectors"].items():
        if r["flagged"] is None:
            md.append(f"| {d} | {r['threshold']:.4g} | 0 | n/a | n/a | n/a |")
        else:
            md.append(
                f"| {d} | {r['threshold']:.4g} | {r['n_scoreable']} | {r['flagged']:.2f} ({r['n_flagged']}) | {r['ci95'][0]:.2f} to {r['ci95'][1]:.2f} | {r['median']:.4g} |"
            )
    (out_dir / "address_units_table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
