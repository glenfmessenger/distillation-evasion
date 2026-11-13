#!/usr/bin/env python
"""Amendment B9 diagnostic: what the per-account discrepancy statistic measures at matched
count. For benign accounts and for the campaigns' 100-prompt blocks: the mean within-unit kernel
value, the mean unit-to-pool kernel value and the mean pool-to-pool kernel value, from the cached
embeddings and the primary bandwidth. The unbiased discrepancy is k_unit + k_pool - 2 k_cross.

Writes docs/evidence/m8/kernel.json and kernel_table.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from dev_harness.benign import read_schedule
from dev_harness.detectors.content import _sqdist
from dev_harness.paths import host_repo

ROOT = Path(__file__).resolve().parents[1]


def kmean(a: np.ndarray, b: np.ndarray, sigma: float, same: bool) -> float:
    k = np.exp(-_sqdist(a, b) / (2.0 * sigma * sigma))
    if same:
        n = len(a)
        return float((k.sum() - np.trace(k)) / (n * (n - 1)))
    return float(k.mean())


def main() -> int:
    root = host_repo()
    cache = root / "results" / "aggregates" / "m4" / "_embeddings"
    content = json.loads((ROOT / "docs" / "evidence" / "m4" / "content_instr.json").read_text())
    sigma = content["sigma_median_heuristic"]
    sched = read_schedule(root / "benign" / "m3_v1" / "replay_schedule.jsonl")
    by_ident: dict[str, list[str]] = {}
    for r in sched:
        by_ident.setdefault(r.identity_id, []).append(r.user_content)
    units = {i: v for i, v in by_ident.items() if len(v) >= 30}
    b = np.load(cache / "benign_m3_v1.npy")
    owners = np.asarray([i for i, v in units.items() for _ in v])
    rng = np.random.default_rng(0)
    pool_idx = rng.choice(len(b), size=2000, replace=False)
    pool = b[pool_idx]
    k_pool = kmean(pool, pool, sigma, True)
    out = {"sigma": sigma, "k_pool_pool": k_pool, "units": {}}
    # benign accounts: 200 at random, matched count 30
    idents = list(units)
    pick = rng.choice(len(idents), size=200, replace=False)
    ku, kc = [], []
    for j in pick:
        m = np.nonzero(owners == idents[j])[0]
        sub = b[rng.choice(m, size=30, replace=False)]
        ku.append(kmean(sub, sub, sigma, True))
        kc.append(
            kmean(
                sub,
                b[~np.isin(np.arange(len(b)), m)][
                    rng.choice(len(b) - len(m), size=2000, replace=False)
                ],
                sigma,
                False,
            )
        )
    out["units"]["benign accounts"] = {
        "k_within": float(np.median(ku)),
        "k_cross": float(np.median(kc)),
        "n": len(pick),
    }
    for name, fn in (
        ("C-bench", "campaign_pilot_baseline.npy"),
        ("C-real", "campaign_c_real_v2_20.npy"),
        ("C-instr", "campaign_c_instr_v2.npy"),
    ):
        c = np.load(cache / fn)
        ku, kc = [], []
        for k0 in range(0, len(c) - 100 + 1, 100):
            blk = c[k0 : k0 + 100]
            sub = blk[rng.choice(100, size=30, replace=False)]
            ku.append(kmean(sub, sub, sigma, True))
            kc.append(kmean(sub, pool, sigma, False))
        out["units"][name] = {
            "k_within": float(np.median(ku)),
            "k_cross": float(np.median(kc)),
            "n": len(ku),
        }
    for name, u in out["units"].items():
        u["mmd2_approx"] = u["k_within"] + k_pool - 2 * u["k_cross"]
    out_dir = ROOT / "docs" / "evidence" / "m8"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "kernel.json").write_text(json.dumps(out, indent=1))
    md = [
        f"Kernel diagnostic (sigma {sigma:.4f}; pool-to-pool mean kernel {k_pool:.4f}): median over units of the mean within-unit kernel and the mean unit-to-pool kernel at matched count 30; the discrepancy is k_within + k_pool - 2 k_cross.",
        "| Units | n | k_within | k_cross | discrepancy |",
        "|---|---|---|---|---|",
    ]
    for name, u in out["units"].items():
        md.append(
            f"| {name} | {u['n']} | {u['k_within']:.4f} | {u['k_cross']:.4f} | {u['mmd2_approx']:.4f} |"
        )
    (out_dir / "kernel_table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
