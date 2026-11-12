#!/usr/bin/env python
"""C2 in R3's own evaluation design (arXiv:2606.05725; LabRAI/mmd-llm-mea-detection), as a check
on the per-identity calibration of m4_content.py: benign real-user prompts split 80/20 into a
reference pool and a held-out stream; null = unbiased RBF MMD^2 between two disjoint draws of
`batch` prompts from the reference pool (1,000 draws); a test window of `batch` prompts is scored
as the mean MMD^2 against 20 reference draws; thresholds at R3's 95th percentile and at our 1%
and 0.1% budgets. Windows: pure campaign windows, held-out benign windows (empirical FPR), and
mixed windows at campaign fractions 0.05, 0.1, 0.25, 0.5. Reads prompt text (V2 only).

Writes results/aggregates/m4/<out-label>/r3batch.json and table.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from dev_harness.detectors.content import median_bandwidth, mmd2_unbiased
from dev_harness.paths import host_repo


def _embed_control(texts: list[str], device: str, cache: Path) -> np.ndarray:
    """bge-small CLS embeddings, unit-normalised, cached (same recipe as m4_content.embed)."""
    if cache.exists() and len(np.load(cache)) == len(texts):
        return np.load(cache)
    import torch
    from transformers import AutoModel, AutoTokenizer

    name = "BAAI/bge-small-en-v1.5"
    tok = AutoTokenizer.from_pretrained(name)
    model = AutoModel.from_pretrained(name).to(device).eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(texts), 256):
            b = tok(
                texts[i : i + 256],
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            ).to(device)
            out.append(
                torch.nn.functional.normalize(model(**b).last_hidden_state[:, 0], dim=-1)
                .cpu()
                .numpy()
            )
    e = np.concatenate(out)
    np.save(cache, e)
    return e


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--campaigns", required=True, help="specs as in m4_content.py")
    ap.add_argument("--content-label", required=True, help="m4_content out-label (embedding cache)")
    ap.add_argument("--out-label", required=True)
    ap.add_argument("--batch", type=int, default=1500)
    ap.add_argument("--null-samples", type=int, default=1000)
    ap.add_argument("--windows", type=int, default=50)
    ap.add_argument("--reference-repeats", type=int, default=20)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--fractions", default="0.05,0.1,0.25,0.5")
    ap.add_argument(
        "--control-files",
        default="",
        help="comma-separated name=prompts.jsonl: benign prompt files scored as pure windows "
        "(controls), embedded with the same model",
    )
    ap.add_argument("--device", default="cpu")
    ap.add_argument(
        "--all-replay-prompts",
        action="store_true",
        help="B4 item 5 (P22): reference and held-out pools drawn by request over every replayed "
        "identity, light users included, embedded here (cache benign_<label>_all.npy)",
    )
    ap.add_argument(
        "--first-turns-only",
        action="store_true",
        help="restrict the reference, null and held-out pools to first user turns (turn-matched)",
    )
    a = ap.parse_args()
    root = host_repo()
    cache = root / "results" / "aggregates" / "m4" / "_embeddings"
    from dev_harness.benign import read_schedule

    sched = read_schedule(root / "benign" / a.benign_label / "replay_schedule.jsonl")
    # the embedding cache holds benign identities with >= 30 prompts in schedule order; rebuild
    # the same text list to index it, keeping real users only (b:conv:*)
    by_ident: dict[str, list[str]] = {}
    for r in sched:
        by_ident.setdefault(r.identity_id, []).append(r.user_content)
    if a.all_replay_prompts:
        units = dict(by_ident)
        texts_all = [x for v in units.values() for x in v]
        b_all = _embed_control(texts_all, a.device, cache / f"benign_{a.benign_label}_all.npy")
    else:
        units = {i: v for i, v in by_ident.items() if len(v) >= 30}
        b_all = np.load(cache / f"benign_{a.benign_label}.npy")
    owners = np.asarray([i for i, v in units.items() for _ in v])
    turn0: dict[str, list[bool]] = {}
    for r in sched:
        turn0.setdefault(r.identity_id, []).append(r.turn_index == 0)
    first = np.asarray([t for i in units for t in turn0[i]])
    if len(first) != len(b_all):
        raise RuntimeError("turn index list does not match the embedding cache")
    if len(owners) != len(b_all):
        raise RuntimeError("embedding cache does not match the schedule")
    real = np.asarray([o.startswith("b:conv:") for o in owners])
    b, b_first = b_all[real], first[real]
    if a.first_turns_only:
        b, b_first = b[b_first], b_first[b_first]
    rng = np.random.default_rng(a.seed)
    perm = rng.permutation(len(b))
    n_ref = int(0.8 * len(b))
    ref, held = b[perm[:n_ref]], b[perm[n_ref:]]
    held_first = held[b_first[perm[n_ref:]]]  # control: held-out benign FIRST turns only
    B = a.batch
    if len(ref) < 2 * B or len(held) < B:
        raise RuntimeError(f"pools too small for batch {B}: ref {len(ref)}, held {len(held)}")
    sigma = median_bandwidth(ref, rng)
    null = []
    for _ in range(a.null_samples):
        idx = rng.choice(len(ref), size=2 * B, replace=False)
        null.append(mmd2_unbiased(ref[idx[:B]], ref[idx[B:]], sigma))
    null = np.asarray(null)
    thr = {
        "r3_p95": float(np.percentile(null, 95)),
        "fpr_0.01": float(np.percentile(null, 99)),
        "fpr_0.001": float(np.percentile(null, 99.9)),
    }

    def score(window: np.ndarray) -> float:
        vals = []
        for _ in range(a.reference_repeats):
            r = ref[rng.choice(len(ref), size=len(window), replace=False)]
            vals.append(mmd2_unbiased(window, r, sigma))
        return float(np.mean(vals))

    def rate(scores, t):
        return float(np.mean(np.asarray(scores) > t))

    result = {
        "batch": B,
        "first_turns_only": a.first_turns_only,
        "all_replay_prompts": a.all_replay_prompts,
        "n_benign_identities_in_pools": len(units),
        "sigma": sigma,
        "n_reference": len(ref),
        "n_heldout": len(held),
        "null_samples": a.null_samples,
        "thresholds": thr,
        "null_quantiles": {q: float(np.percentile(null, q)) for q in (50, 90, 95, 99, 99.9)},
        "benign_heldout": {},
        "campaigns": {},
    }
    held_scores = [
        score(held[rng.choice(len(held), size=B, replace=False)]) for _ in range(a.windows)
    ]
    result["benign_heldout"] = {
        "median": float(np.median(held_scores)),
        "flagged": {k: rate(held_scores, t) for k, t in thr.items()},
    }
    if len(held_first) < B:
        raise RuntimeError(f"held-out first-turn pool too small: {len(held_first)} < {B}")
    hf_scores = [
        score(held_first[rng.choice(len(held_first), size=B, replace=False)])
        for _ in range(a.windows)
    ]
    result["benign_heldout_first_turns"] = {
        "n_pool": int(len(held_first)),
        "median": float(np.median(hf_scores)),
        "flagged": {k: rate(hf_scores, t) for k, t in thr.items()},
    }
    md = [
        f"R3 batch design ({'first-turn-matched pools; ' if a.first_turns_only else ''}{'request-weighted pools over all replayed identities; ' if a.all_replay_prompts else ''}batch {B}, {a.null_samples} null draws, {a.windows} windows per condition, sigma {sigma:.4f}). "
        f"Thresholds: R3 95th {thr['r3_p95']:.4g}; 1% {thr['fpr_0.01']:.4g}; 0.1% {thr['fpr_0.001']:.4g}.\n",
        "| Window | Median MMD² | Flagged at R3 95th | at 1% | at 0.1% |",
        "|---|---|---|---|---|",
        f"| benign held-out | {np.median(held_scores):.4g} | {rate(held_scores, thr['r3_p95']):.2f} | {rate(held_scores, thr['fpr_0.01']):.2f} | {rate(held_scores, thr['fpr_0.001']):.2f} |",
        f"| benign held-out, first turns only (control, pool {len(held_first)}) | {np.median(hf_scores):.4g} | {rate(hf_scores, thr['r3_p95']):.2f} | {rate(hf_scores, thr['fpr_0.01']):.2f} | {rate(hf_scores, thr['fpr_0.001']):.2f} |",
    ]
    for item in [x for x in a.control_files.split(",") if x.strip()]:
        cname, _, cpath = item.partition("=")
        with Path(cpath).open(encoding="utf-8") as fh:
            ctexts = [json.loads(line)["messages"][0]["content"] for line in fh if line.strip()]
        c = _embed_control(ctexts, a.device, cache / f"control_{cname}.npy")
        if len(c) < B:
            raise RuntimeError(f"control {cname} has {len(c)} prompts, fewer than batch {B}")
        cs = [score(c[rng.choice(len(c), size=B, replace=False)]) for _ in range(a.windows)]
        result.setdefault("controls", {})[cname] = {
            "n_prompts": len(c),
            "median": float(np.median(cs)),
            "flagged": {k: rate(cs, t) for k, t in thr.items()},
        }
        md.append(
            f"| control {cname} (benign prompt file, pure window) | {np.median(cs):.4g} | "
            f"{rate(cs, thr['r3_p95']):.2f} | {rate(cs, thr['fpr_0.01']):.2f} | {rate(cs, thr['fpr_0.001']):.2f} |"
        )
    for spec in a.campaigns.split(","):
        name = spec.strip()
        c = np.load(cache / f"campaign_{name.replace(':', '_')}.npy")
        if len(c) < B:
            raise RuntimeError(f"campaign {name} has {len(c)} prompts, fewer than batch {B}")
        out = {}
        pure = [score(c[rng.choice(len(c), size=B, replace=False)]) for _ in range(a.windows)]
        out["pure"] = {
            "median": float(np.median(pure)),
            "flagged": {k: rate(pure, t) for k, t in thr.items()},
        }
        md.append(
            f"| {name} pure campaign | {np.median(pure):.4g} | {rate(pure, thr['r3_p95']):.2f} | {rate(pure, thr['fpr_0.01']):.2f} | {rate(pure, thr['fpr_0.001']):.2f} |"
        )
        for f in [float(x) for x in a.fractions.split(",") if x.strip()]:
            k = int(round(f * B))
            mixed = []
            for _ in range(a.windows):
                w = np.concatenate(
                    [
                        c[rng.choice(len(c), size=k, replace=False)],
                        held[rng.choice(len(held), size=B - k, replace=False)],
                    ]
                )
                mixed.append(score(w))
            out[f"mixed_{f}"] = {
                "median": float(np.median(mixed)),
                "flagged": {kk: rate(mixed, t) for kk, t in thr.items()},
            }
            md.append(
                f"| {name} mixed, campaign share {f:g} | {np.median(mixed):.4g} | {rate(mixed, thr['r3_p95']):.2f} | {rate(mixed, thr['fpr_0.01']):.2f} | {rate(mixed, thr['fpr_0.001']):.2f} |"
            )
        result["campaigns"][name] = out
        print(f"{name}: done", flush=True)
    out_dir = root / "results" / "aggregates" / "m4" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "r3batch.json").write_text(json.dumps(result, indent=1))
    (out_dir / "table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
