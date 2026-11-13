#!/usr/bin/env python
"""V2, the content level (PROTOCOL v2.0 §5 and amendment B1): C1 topic-cluster JSD, C2 R3-style
MMD (high) and C2low (the same statistic, flagged when below the benign lower quantile), C3
within-unit diversity, and the lexical baselines B1 (benchmark membership) and B2 (template
reuse), on the prompts as sent, for benign identities and for one or more campaigns, including
the campaign under identity splitting. Reads prompt text: never part of the content-blind set.

Campaign spec: <label>[:<max_sessions>], e.g. pilot_baseline, c_real_v2:20, c_real_v2.
Benign source: the replay schedule (default) or --benign-prompts-file (heavy real users).
Writes results/aggregates/m4/<out-label>/{content.json,table.md,unit_stats.jsonl}.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from dev_harness.detectors.analysis import auc
from dev_harness.detectors.content import (
    b1_membership,
    b2_template_reuse,
    benchmark_index,
    c2_mmd_score,
    c3_diversity,
    median_bandwidth,
)
from dev_harness.detectors.stats import calibrate, fires, jsd
from dev_harness.paths import host_repo
from dev_harness.pool import read_jsonl
from dev_harness.prompts import chat_messages

MODEL, K, N_MATCH, N_SUB = "BAAI/bge-small-en-v1.5", 50, 30, 20
BUDGETS = (0.01, 0.001)
DETS = ("C1", "C2", "C2low", "C3", "B1", "B2")
DIRECTION = {d: "high" for d in DETS}
DIRECTION["C2low"] = "low"  # amendment B1 item 3, post-hoc
POST_HOC = ("C2low", "C3")


def embed(texts: list[str], device: str, cache: Path, model_name: str) -> np.ndarray:
    if cache.exists():
        e = np.load(cache)
        if len(e) == len(texts):
            return e
    import torch
    from transformers import AutoModel, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name).to(device).eval()
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
            h = model(**b).last_hidden_state[:, 0]
            out.append(torch.nn.functional.normalize(h, dim=-1).cpu().numpy())
    e = np.concatenate(out)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.save(cache, e)
    return e


def campaign_prompts(root: Path, spec: str) -> tuple[str, list[str], int]:
    """(name, prompts as sent in issue order, session size) for a campaign spec."""
    label, _, k = spec.partition(":")
    cdir = root / "results" / "raw" / "campaign" / label
    man = json.loads((cdir / "manifest.json").read_text())
    if "finished" not in man:
        raise RuntimeError(f"campaign {label} has not finished")
    if "prompt_file" in man["strata"]:
        pf = Path(man["strata"]["prompt_file"])
        if not pf.exists():  # manifest written on the node; remap its data root to ours, visibly
            node_root = Path("/home/ubuntu/data")
            if not pf.is_relative_to(node_root):
                raise FileNotFoundError(f"prompt file {pf} not found and not under {node_root}")
            pf = root / pf.relative_to(node_root)
            print(f"prompt file remapped from the node data root to {pf}", flush=True)
        with pf.open(encoding="utf-8") as fh:
            prompts = [json.loads(line)["messages"][0]["content"] for line in fh if line.strip()]
    else:
        pool = {it.id: it for it in read_jsonl(root / "pool" / "pool.jsonl")}
        prompts = [chat_messages(pool[i])[0]["content"] for i in man["ids"]]
    sess = man["session_size"]
    if k:
        prompts = prompts[: int(k) * sess]
    return (label + (f":{k}" if k else "")), prompts, sess


def c1_stat(labels: np.ndarray, pop_hist: dict, rng: np.random.Generator, n_match: int) -> float:
    if len(labels) < n_match:
        return math.nan
    js = []
    for _ in range(N_SUB):
        idx = rng.choice(len(labels), size=n_match, replace=False)
        h = Counter(labels[idx].tolist())
        js.append(jsd({k: v / n_match for k, v in h.items()}, pop_hist))
    return float(np.median(js))


def benign_prompts_from_file(path: Path) -> dict[str, list[str]]:
    """{identity: prompts} from a content-calibration file (build_content_calibration.py)."""
    out = {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                d = json.loads(line)
                out[d["identity"]] = d["prompts"]
    if not out:
        raise RuntimeError(f"{path}: empty")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--campaigns", required=True, help="comma-separated campaign specs")
    ap.add_argument("--out-label", required=True)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--n-list", default="1,10,100,1000")
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--model", default=MODEL, help="embedding model (B1 item 4)")
    ap.add_argument("--n-match", type=int, default=N_MATCH)
    ap.add_argument("--block", type=int, default=0, help="block size (0 = campaign session size)")
    ap.add_argument(
        "--control-files",
        default="",
        help="comma-separated name=prompts.jsonl: benign prompt files scored exactly like a "
        "campaign (controls), with blocks of --block or 100",
    )
    ap.add_argument(
        "--benign-prompts-file",
        default="",
        help="heavy-real-user calibration file (B1 item 2) instead of the replay schedule",
    )
    a = ap.parse_args()
    root = host_repo()
    n_match = a.n_match
    from dev_harness.benign import read_schedule

    if a.benign_prompts_file:
        by_ident = benign_prompts_from_file(Path(a.benign_prompts_file))
        benign_tag = Path(a.benign_prompts_file).parent.name
    else:
        by_ident = defaultdict(list)
        for r in read_schedule(root / "benign" / a.benign_label / "replay_schedule.jsonl"):
            by_ident[r.identity_id].append(r.user_content)
        benign_tag = a.benign_label
    benign_units = {i: v for i, v in by_ident.items() if len(v) >= n_match}
    if len(benign_units) < 100:
        raise RuntimeError(f"only {len(benign_units)} benign identities with >= {n_match} prompts")
    cache_dir = root / "results" / "aggregates" / "m4" / "_embeddings"
    mtag = "" if a.model == MODEL else "_" + a.model.replace("/", "_")
    b_texts, b_owner = [], []
    for i, v in benign_units.items():
        b_texts += v
        b_owner += [i] * len(v)
    b_emb = embed(b_texts, a.device, cache_dir / f"benign_{benign_tag}{mtag}.npy", a.model)
    b_owner = np.asarray(b_owner)
    rng = np.random.default_rng(0)
    sigma = median_bandwidth(b_emb, rng)
    from scipy.cluster.vq import kmeans2

    cent, b_lab = kmeans2(b_emb.astype(np.float64), K, minit="++", seed=0)
    pop_hist = {k: v / len(b_lab) for k, v in Counter(b_lab.tolist()).items()}
    pool_index = benchmark_index(it.prompt for it in read_jsonl(root / "pool" / "pool.jsonl"))

    def stats_for(prompts, emb, labels, pool, seed):
        r = np.random.default_rng(seed)
        c2 = c2_mmd_score(emb, pool, sigma, r, n_match, N_SUB)
        return {
            "C1": c1_stat(labels, pop_hist, r, n_match),
            "C2": c2,
            "C2low": c2,
            "C3": c3_diversity(emb, r, n_match, N_SUB),
            "B1": b1_membership(prompts, pool_index) if prompts else math.nan,
            "B2": b2_template_reuse(prompts),
        }

    unit_rows = []
    bvals: dict[str, list[float]] = defaultdict(list)
    for j, (ident, v) in enumerate(benign_units.items()):
        m = b_owner == ident
        s = stats_for(v, b_emb[m], b_lab[m], b_emb[~m], seed=j)
        unit_rows.append({"population": "benign", "unit": ident, "n_prompts": len(v), **s})
        for d in DETS:
            bvals[d].append(s[d])
        if j % 500 == 0:
            print(f"benign units {j}/{len(benign_units)}", flush=True)
    cal = {d: {str(b): calibrate(bvals[d], DIRECTION[d], b) for b in BUDGETS} for d in DETS}

    result = {
        "reads_content": True,
        "model": a.model,
        "benign_source": benign_tag,
        "k": K,
        "n_match": n_match,
        "block": a.block or "session size",
        "n_sub": N_SUB,
        "directions": DIRECTION,
        "post_hoc": POST_HOC,
        "sigma_median_heuristic": sigma,
        "n_benign_units": len(benign_units),
        "calibration": cal,
        "campaigns": {},
    }
    md = [
        f"M4 content level (benign `{benign_tag}`, model `{a.model}`, {len(benign_units)} benign "
        f"identities at matched n = {n_match}, block {a.block or 'session'}). C2low and C3 are "
        "post-hoc (amendment B1). Flagged = fraction of campaign units over the benign threshold; "
        "per-identity cells under identity splitting are n/a below matched n.\n",
        "| Campaign | Unit | n units (scoreable) | Detector | 1% threshold | Flagged 1% | Flagged 0.1% | Below res. 0.1% | Campaign median | AUC |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    hot = []
    specs: list = [("campaign", x.strip()) for x in a.campaigns.split(",") if x.strip()]
    specs += [("control", x.strip()) for x in a.control_files.split(",") if x.strip()]
    for kind, spec in specs:
        if kind == "campaign":
            name, prompts, sess = campaign_prompts(root, spec)
        else:
            cname, _, cpath = spec.partition("=")
            with Path(cpath).open(encoding="utf-8") as fh:
                prompts = [
                    json.loads(line)["messages"][0]["content"] for line in fh if line.strip()
                ]
            name, sess = f"control:{cname}", 100
        sess = a.block or sess
        c_emb = embed(
            prompts, a.device, cache_dir / f"campaign_{name.replace(':', '_')}{mtag}.npy", a.model
        )
        c_lab = np.argmax(c_emb @ cent.T.astype(np.float32), axis=1)
        pops: dict[str, list[dict]] = {}
        pops["identity"] = [stats_for(prompts, c_emb, c_lab, b_emb, 1)]
        pops[f"block{sess}"] = [
            stats_for(prompts[k : k + sess], c_emb[k : k + sess], c_lab[k : k + sess], b_emb, 2 + k)
            for k in range(0, len(prompts) - sess + 1, sess)
        ]
        for n in [int(x) for x in a.n_list.split(",")]:
            if n == 1:
                continue
            rows = []
            for seed in range(a.seeds):
                start = random.Random(seed).randrange(n)
                owner = np.array([(start + k) % n for k in range(len(prompts))])
                for i in range(n):
                    m = owner == i
                    idx = np.nonzero(m)[0]
                    rows.append(
                        stats_for([prompts[t] for t in idx], c_emb[m], c_lab[m], b_emb, 100 + seed)
                    )
            pops[f"identity_split_n{n}"] = rows
        out_c = {}
        for pop, rows in pops.items():
            for r in rows:
                unit_rows.append(
                    {"population": f"{name}:{pop}", "unit": pop, "n_prompts": None, **r}
                )
            out_c[pop] = {}
            for d in DETS:
                vals = [r[d] for r in rows]
                scored = [v for v in vals if not math.isnan(v)]
                fl = {str(b): [fires(v, cal[d][str(b)]) for v in scored] for b in BUDGETS}
                frac = {b: (sum(bool(x) for x in f) / len(f) if f else None) for b, f in fl.items()}
                au = auc(vals, bvals[d], DIRECTION[d])
                out_c[pop][d] = {
                    "n_units": len(vals),
                    "n_scoreable": len(scored),
                    "median": float(np.median(scored)) if scored else None,
                    "auc": au,
                    "flagged": frac,
                }
                if au is not None and au >= 0.95:
                    hot.append((name, pop, d, round(au, 4)))
                md.append(
                    f"| {name} | {pop} | {len(vals)} ({len(scored)}) | {d}{' (post-hoc)' if d in POST_HOC else ''} | "
                    f"{cal[d]['0.01']['threshold']:.4g} | "
                    f"{'n/a' if frac['0.01'] is None else format(frac['0.01'], '.2f')} | "
                    f"{'n/a' if frac['0.001'] is None else format(frac['0.001'], '.2f')} | "
                    f"{'yes' if cal[d]['0.001']['below_resolution'] else 'no'} | "
                    f"{'n/a' if not scored else format(np.median(scored), '.4g')} | "
                    f"{'n/a' if au is None else format(au, '.3f')} |"
                )
        result["campaigns"][name] = out_c
        print(f"campaign {name}: done", flush=True)

    out_dir = root / "results" / "aggregates" / "m4" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "content.json").write_text(json.dumps(result, indent=1))
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
    (out_dir / "table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    if hot:
        print("\nTOO-GOOD STOP RULE: AUC >= 0.95 for", hot)
    return 0


if __name__ == "__main__":
    sys.exit(main())
