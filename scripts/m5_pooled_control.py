#!/usr/bin/env python
"""Amendment B6 item 3(b): the pooled-account content control.

Synthetic accounts are formed by merging the prompt streams of m real replayed accounts (drawn
without replacement, interleaved by each account's own relative time) and scored by every
content statistic at matched count 30 and in blocks of 100 against the primary calibration
(replay accounts with at least 30 prompts, bge-small, cached embeddings), with the constituent
accounts excluded from the reference pool. The calibration is recomputed here with the same
code as m4_content.py and compared with the committed thresholds.

Writes results/aggregates/m5/<out-label>/{pooled.json,table.md,unit_stats.jsonl}.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from dev_harness.benign import read_schedule
from dev_harness.detectors.analysis import auc
from dev_harness.detectors.content import (
    b1_membership,
    b2_template_reuse,
    benchmark_index,
    c2_mmd_score,
    c3_diversity,
    median_bandwidth,
)
from dev_harness.detectors.stats import calibrate, fires
from dev_harness.paths import host_repo
from dev_harness.pool import read_jsonl

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m4_content import DETS, DIRECTION, K, MODEL, N_MATCH, N_SUB, POST_HOC, c1_stat  # noqa: E402

BUDGET = 0.01


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--out-label", required=True)
    ap.add_argument("--m-list", default="5,20,100")
    ap.add_argument("--groups", type=int, default=100)
    ap.add_argument("--committed", default="", help="committed content.json to compare thresholds")
    a = ap.parse_args()
    root = host_repo()
    sched = read_schedule(root / "benign" / a.benign_label / "replay_schedule.jsonl")
    by_ident: dict[str, list] = defaultdict(list)
    for r in sched:
        by_ident[r.identity_id].append(r)
    units = {i: v for i, v in by_ident.items() if len(v) >= N_MATCH}
    cache = root / "results" / "aggregates" / "m4" / "_embeddings" / f"benign_{a.benign_label}.npy"
    b_emb = np.load(cache)
    b_texts, b_owner, b_time = [], [], []
    for i, v in units.items():
        b_texts += [x.user_content for x in v]
        b_owner += [i] * len(v)
        b_time += [x.t_sched_s for x in v]
    if len(b_emb) != len(b_texts):
        raise RuntimeError(f"embedding cache {len(b_emb)} rows, schedule {len(b_texts)} prompts")
    b_owner, b_time = np.asarray(b_owner), np.asarray(b_time)
    rng = np.random.default_rng(0)
    sigma = median_bandwidth(b_emb, rng)
    from scipy.cluster.vq import kmeans2

    cent, b_lab = kmeans2(b_emb.astype(np.float64), K, minit="++", seed=0)
    pop_hist = {k: v / len(b_lab) for k, v in Counter(b_lab.tolist()).items()}
    pool_index = benchmark_index(it.prompt for it in read_jsonl(root / "pool" / "pool.jsonl"))

    def stats_for(prompts, emb, labels, pool, seed):
        r = np.random.default_rng(seed)
        c2 = c2_mmd_score(emb, pool, sigma, r, N_MATCH, N_SUB)
        return {
            "C1": c1_stat(labels, pop_hist, r, N_MATCH),
            "C2": c2,
            "C2low": c2,
            "C3": c3_diversity(emb, r, N_MATCH, N_SUB),
            "B1": b1_membership(prompts, pool_index) if prompts else math.nan,
            "B2": b2_template_reuse(prompts),
        }

    bvals: dict[str, list[float]] = defaultdict(list)
    unit_rows = []
    for j, (ident, v) in enumerate(units.items()):
        m = b_owner == ident
        s = stats_for([x.user_content for x in v], b_emb[m], b_lab[m], b_emb[~m], seed=j)
        unit_rows.append({"population": "benign", "unit": f"benign-{j:04d}", **s})
        for d in DETS:
            bvals[d].append(s[d])
    cal = {d: calibrate(bvals[d], DIRECTION[d], BUDGET) for d in DETS}
    compare = {}
    if a.committed:
        com = json.loads(Path(a.committed).read_text())["calibration"]
        for d in DETS:
            if d in com:
                compare[d] = {
                    "committed": com[d]["0.01"]["threshold"],
                    "recomputed": cal[d]["threshold"],
                    "match": math.isclose(
                        com[d]["0.01"]["threshold"], cal[d]["threshold"], rel_tol=1e-6, abs_tol=1e-9
                    ),
                }
        print("threshold comparison:", json.dumps(compare), flush=True)

    ident_list = list(units)
    perm = np.random.default_rng(1).permutation(len(ident_list))
    result = {
        "model": MODEL,
        "n_benign_units": len(units),
        "sigma": sigma,
        "calibration": {d: cal[d] for d in DETS},
        "threshold_comparison": compare,
        "controls": {},
    }
    md = [
        f"Pooled-account control (B6 item 3b): {len(units)} replayed accounts with >= {N_MATCH} prompts; synthetic accounts merge m real accounts; primary calibration recomputed (thresholds {'match' if compare and all(c['match'] for c in compare.values()) else 'see comparison'} the committed values).\n",
        "| m | Groups | Unit | n units | Detector | Threshold | Flagged 1% | Median | AUC |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for m in [int(x) for x in a.m_list.split(",")]:
        n_groups = min(a.groups, len(ident_list) // m)
        pops: dict[str, list[dict]] = {"identity": [], "block100": []}
        for g in range(n_groups):
            members = {ident_list[perm[g * m + k]] for k in range(m)}
            mask = np.isin(b_owner, list(members))
            idx = np.nonzero(mask)[0]
            idx = idx[np.argsort(b_time[idx], kind="stable")]
            prompts = [b_texts[i] for i in idx]
            emb, lab = b_emb[idx], b_lab[idx]
            pool = b_emb[~mask]
            pops["identity"].append(stats_for(prompts, emb, lab, pool, 10_000 + g))
            for k in range(0, len(prompts) - 100 + 1, 100):
                pops["block100"].append(
                    stats_for(
                        prompts[k : k + 100],
                        emb[k : k + 100],
                        lab[k : k + 100],
                        pool,
                        20_000 + g * 1000 + k,
                    )
                )
        name = f"control:pooled_m{m}"
        out_c: dict = {"n_groups": n_groups}
        for pop, rows in pops.items():
            for r in rows:
                unit_rows.append({"population": f"{name}:{pop}", "unit": pop, **r})
            out_c[pop] = {}
            for d in DETS:
                vals = [r[d] for r in rows]
                scored = [v for v in vals if not math.isnan(v)]
                fl = [fires(v, cal[d]) for v in scored]
                frac = sum(bool(x) for x in fl) / len(fl) if fl else None
                au = auc(vals, bvals[d], DIRECTION[d])
                out_c[pop][d] = {
                    "n_units": len(vals),
                    "n_scoreable": len(scored),
                    "flagged": frac,
                    "median": float(np.median(scored)) if scored else None,
                    "auc": au,
                }
                md.append(
                    f"| {m} | {n_groups} | {pop} | {len(vals)} | {d}{' (post-hoc)' if d in POST_HOC else ''} | {cal[d]['threshold']:.4g} | "
                    f"{'n/a' if frac is None else format(frac, '.2f')} | {'n/a' if not scored else format(np.median(scored), '.4g')} | {'n/a' if au is None else format(au, '.3f')} |"
                )
        result["controls"][name] = out_c
        print(f"{name}: done", flush=True)
    p32 = {}
    for m in (20, 100):
        c = result["controls"].get(f"control:pooled_m{m}")
        if c:
            p32[str(m)] = {
                "C2low_identity_flagged": c["identity"]["C2low"]["flagged"],
                "others_at_most_0.10": all(
                    (c["identity"][d]["flagged"] or 0) <= 0.10
                    for d in ("C1", "C2", "C3", "B1", "B2")
                ),
            }
    result["p32"] = p32
    out_dir = root / "results" / "aggregates" / "m5" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "pooled.json").write_text(json.dumps(result, indent=1, default=float))
    with (out_dir / "unit_stats.jsonl").open("w") as fh:
        for r in unit_rows:
            fh.write(
                json.dumps(
                    {
                        k: (None if isinstance(v, float) and math.isnan(v) else v)
                        for k, v in r.items()
                    }
                )
                + "\n"
            )
    md += ["", f"P32: {json.dumps(p32)}"]
    (out_dir / "table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
