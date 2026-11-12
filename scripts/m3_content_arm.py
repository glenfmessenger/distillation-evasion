#!/usr/bin/env python
"""C1, the content-reading comparison arm (PROTOCOL §5, decision 3). NOT a content-blind detector:
it reads prompt text. Reported in its own table as an upper bound on coverage detectability.

Statistic, per identity at matched n = 30 requests: JSD between the identity's histogram over
k = 50 topic clusters and the benign population's; median over 20 seeded subsamples. Clusters are
k-means on BAAI/bge-small-en-v1.5 embeddings of BENIGN prompts only. Secondary: mean pairwise
cosine distance among the identity's 30 prompts.

Benign units: replayed identities with >= 30 requests (prompts from the replay schedule, first
user message of each request). Campaign units: the campaign identity, and each 100-request session
viewed as its own identity. Writes results/aggregates/m3/<out-label>/content_arm.json and
content_arm_stats.jsonl. Usage: m3_content_arm.py --benign-label B --campaign-label C --out-label L
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict

import numpy as np
import torch
from scipy.cluster.vq import kmeans2
from transformers import AutoModel, AutoTokenizer

from dev_harness.benign import read_schedule
from dev_harness.detectors.stats import calibrate, fires, jsd
from dev_harness.paths import host_repo
from dev_harness.pool import read_jsonl

MODEL, K, N_MATCH, N_SUB = "BAAI/bge-small-en-v1.5", 50, 30, 20


def embed(texts: list[str], device: str) -> np.ndarray:
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModel.from_pretrained(MODEL).to(device).eval()
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
            e = model(**b).last_hidden_state[:, 0]
            out.append(torch.nn.functional.normalize(e, dim=-1).cpu().numpy())
            if (i // 256) % 20 == 0:
                print(f"embedded {i + len(texts[i : i + 256])}/{len(texts)}", flush=True)
    return np.concatenate(out)


def unit_stats(
    labels: np.ndarray, emb: np.ndarray, pop_hist: dict, seed: int
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    js, div = [], []
    for _ in range(N_SUB):
        idx = rng.choice(len(labels), size=N_MATCH, replace=False)
        h = Counter(labels[idx].tolist())
        js.append(jsd({k: v / N_MATCH for k, v in h.items()}, pop_hist))
        e = emb[idx]
        sim = e @ e.T
        div.append(float(1.0 - (sim.sum() - N_MATCH) / (N_MATCH * (N_MATCH - 1))))
    return float(np.median(js)), float(np.median(div))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--campaign-label", required=True)
    ap.add_argument("--out-label", required=True)
    ap.add_argument("--device", default="cpu")
    a = ap.parse_args()
    root = host_repo()
    by_ident: dict[str, list[str]] = defaultdict(list)
    for r in read_schedule(root / "benign" / a.benign_label / "replay_schedule.jsonl"):
        by_ident[r.identity_id].append(r.user_content)
    benign_units = {i: v for i, v in by_ident.items() if len(v) >= N_MATCH}
    if len(benign_units) < 100:
        raise RuntimeError(f"only {len(benign_units)} benign identities with >= {N_MATCH} prompts")
    cdir = root / "results" / "raw" / "campaign" / a.campaign_label
    ids = json.loads((cdir / "manifest.json").read_text())
    pool = {it.id: it.prompt for it in read_jsonl(root / "pool" / "pool.jsonl")}
    camp_prompts = [pool[i] for i in ids["ids"]]
    sess = ids["session_size"]
    camp_units = {"campaign:identity": camp_prompts}
    camp_units.update(
        {
            f"campaign:s{k}": camp_prompts[k * sess : (k + 1) * sess]
            for k in range(len(camp_prompts) // sess)
        }
    )

    names, texts, spans = [], [], {}
    for name, v in list(benign_units.items()) + list(camp_units.items()):
        spans[name] = (len(texts), len(texts) + len(v))
        texts.extend(v)
        names.append(name)
    emb = embed(texts, a.device)
    n_benign = spans[list(benign_units)[-1]][1]
    np.random.seed(0)
    cent, lab_b = kmeans2(emb[:n_benign].astype(np.float64), K, minit="++", seed=0)
    labels = np.concatenate([lab_b, np.argmax(emb[n_benign:] @ cent.T.astype(np.float32), axis=1)])
    pop = Counter(lab_b.tolist())
    pop_hist = {k: v / n_benign for k, v in pop.items()}

    out_dir = root / "results" / "aggregates" / "m3" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    vals = {}
    with (out_dir / "content_arm_stats.jsonl").open("w") as fh:
        for j, name in enumerate(names):
            s, e = spans[name]
            c1, c1b = unit_stats(labels[s:e], emb[s:e], pop_hist, seed=j)
            vals[name] = (c1, c1b)
            fh.write(
                json.dumps(
                    {
                        "unit": name,
                        "population": "campaign" if name.startswith("campaign:") else "benign",
                        "n_prompts": e - s,
                        "c1_topic_jsd": c1,
                        "c1b_mean_cos_dist": c1b,
                    }
                )
                + "\n"
            )
    res = {
        "reads_content": True,
        "model": MODEL,
        "k": K,
        "n_match": N_MATCH,
        "n_benign_units": len(benign_units),
        "n_prompts_embedded": len(texts),
        "statistics": {},
    }
    for idx, (stat, direction) in enumerate(
        (("c1_topic_jsd", "high"), ("c1b_mean_cos_dist", "low"))
    ):
        b = [vals[n][idx] for n in benign_units]
        ident = vals["campaign:identity"][idx]
        split = [vals[n][idx] for n in camp_units if n != "campaign:identity"]
        st = {
            "direction": direction,
            "benign_median": float(np.median(b)),
            "campaign_identity": ident,
            "campaign_split_median": float(np.median(split)),
            "budgets": {},
        }
        for bud in (0.01, 0.001):
            cal = calibrate(b, direction, bud)
            st["budgets"][str(bud)] = {
                **cal,
                "identity_flagged": bool(fires(ident, cal)),
                "split_frac_flagged": sum(bool(fires(v, cal)) for v in split) / len(split),
            }
        gt = sum((v > x) if direction == "high" else (v < x) for v in split for x in b)
        st["auc_split_vs_benign"] = gt / (len(split) * len(b))
        res["statistics"][stat] = st
        if math.isnan(ident):
            raise RuntimeError("campaign statistic is NaN")
    (out_dir / "content_arm.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
