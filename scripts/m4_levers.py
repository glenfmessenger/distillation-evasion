#!/usr/bin/env python
"""V1 price and the full ladder of content-blind detectors under the volume levers (PROTOCOL
v2.0 §6, §7). For a recorded campaign: cells (n identities) × (rate cap at benign quantile q),
each as 5 seeded re-schedulings; every D1 to D9 statistic computed on the re-scheduled records
against the same benign calibration as M3; detection located per re-scheduling first and pooled
as median and range (charter 3.5). No teacher calls.

Writes results/aggregates/m4/<out-label>/{levers.json,table.md}. Usage:
m4_levers.py --benign-label m3_v1 --campaign-label c_real_v2 --out-label v2_c_real --max-sessions 20
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import defaultdict

import numpy as np

from dev_harness.detectors import stats as D
from dev_harness.detectors.analysis import (
    TIMELINE_DETECTORS,
    summarise,
    timeline_records,
    timeline_stats,
)
from dev_harness.levers import price, shape_rate, split_identities
from dev_harness.paths import host_repo
from dev_harness.writer import calibration_records, read_records

_SESS = re.compile(r":s(\d+)$")


def session_index(session_id: str) -> int:
    m = _SESS.search(session_id)
    if not m:
        raise ValueError(f"session id without index: {session_id}")
    return int(m.group(1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--campaign-label", required=True)
    ap.add_argument("--out-label", required=True)
    ap.add_argument("--max-sessions", type=int, default=0, help="keep sessions 0..k-1 (0 = all)")
    ap.add_argument("--n-list", default="1,10,100,1000")
    ap.add_argument("--q-list", default="0.99,0.9,0.5")
    ap.add_argument("--seeds", type=int, default=5)
    a = ap.parse_args()
    root = host_repo()
    bdir = root / "results" / "raw" / "benign" / a.benign_label
    if not (bdir / "manifest.json").exists():
        raise RuntimeError("benign replay has no manifest")
    benign, _ = calibration_records(read_records(bdir / "records.jsonl"))
    cdir = root / "results" / "raw" / "campaign" / a.campaign_label
    if not (cdir / "manifest.json").exists() or "finished" not in json.loads(
        (cdir / "manifest.json").read_text()
    ):
        raise RuntimeError(f"campaign {a.campaign_label} has not finished")
    camp, n_inflight = calibration_records(read_records(cdir / "records.jsonl"))
    if a.max_sessions:
        camp = [r for r in camp if session_index(r.session_id) < a.max_sessions]
    if not camp:
        raise RuntimeError("no campaign records after the session filter")
    ref = D.BenignReference.fit(benign)
    bvals: dict[str, list[float]] = defaultdict(list)
    for s in D.all_statistics(benign, ref):
        if s.detector_id not in TIMELINE_DETECTORS:
            bvals[s.detector_id].append(s.value)
    for s in timeline_stats(timeline_records(root / "benign" / a.benign_label / "timeline.jsonl")):
        bvals[s.detector_id].append(s.value)
    d1_benign = np.asarray([v for v in bvals["D1"] if not math.isnan(v)])
    caps = {q: max(1, int(math.floor(np.quantile(d1_benign, q)))) for q in _floats(a.q_list)}

    cells = []
    for n in _ints(a.n_list):
        for q, cap in [(None, 0)] + list(caps.items()):
            per_seed = []
            for seed in range(a.seeds):
                recs = split_identities(camp, n, seed)
                if cap:
                    recs = shape_rate(recs, cap, seed)
                cvals: dict[str, list[float]] = defaultdict(list)
                for s in D.all_statistics(recs, ref):
                    cvals[s.detector_id].append(s.value)
                dets = {det: summarise(det, bvals[det], cvals[det]) for det in sorted(cvals)}
                per_seed.append({"seed": seed, "price": price(recs), "detectors": dets})
            cells.append({"n": n, "q": q, "cap_per_hour": cap, "per_seed": per_seed})
            print(f"cell n={n} q={q} cap={cap}: done", flush=True)

    out_dir = root / "results" / "aggregates" / "m4" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "benign_label": a.benign_label,
        "campaign_label": a.campaign_label,
        "max_sessions": a.max_sessions,
        "n_campaign_records": len(camp),
        "n_campaign_in_flight_excluded": n_inflight,
        "n_benign_replay_records": len(benign),
        "rate_caps": {str(q): c for q, c in caps.items()},
        "cells": cells,
    }
    (out_dir / "levers.json").write_text(json.dumps(result, indent=1))
    md = [
        f"M4 lever table (benign `{a.benign_label}`, campaign `{a.campaign_label}`, sessions kept "
        f"{a.max_sessions or 'all'}, {len(camp)} records, {a.seeds} re-schedulings per cell). "
        "Flagged = fraction of campaign units flagged at the 1% budget, median over re-schedulings "
        "[min, max]; AUC median. Price: identities, scheduled wall-clock in hours.\n",
        "| n | q | cap/h | identities | wall-clock h | "
        + " | ".join(f"{d} flagged" for d in sorted(bvals))
        + " |",
        "|" + "---|" * (5 + len(bvals)),
    ]
    hot = []
    for c in cells:
        p0 = c["per_seed"][0]["price"]
        row = [
            str(c["n"]),
            "none" if c["q"] is None else f"{c['q']:g}",
            str(c["cap_per_hour"]),
            str(p0["identities"]),
            f"{np.median([s['price']['wall_clock_s'] for s in c['per_seed']]) / 3600:.1f}",
        ]
        for det in sorted(bvals):
            fr, aucs = [], []
            for s in c["per_seed"]:
                d = s["detectors"].get(det)
                if d is None:
                    continue
                f = d["budgets"]["0.01"]["frac_flagged"]
                fr.append(math.nan if f is None else f)
                if d["auc"] is not None:
                    aucs.append(d["auc"])
                    if d["auc"] >= 0.95:
                        hot.append((c["n"], c["q"], det, s["seed"], round(d["auc"], 4)))
            fr = [x for x in fr if not math.isnan(x)]
            below = bool(
                c["per_seed"][0]["detectors"]
                .get(det, {})
                .get("budgets", {})
                .get("0.01", {})
                .get("below_resolution", False)
            )
            if not fr:
                row.append("n/a")
            else:
                row.append(
                    f"{np.median(fr):.2f} [{min(fr):.2f}, {max(fr):.2f}]"
                    + (f" auc {np.median(aucs):.2f}" if aucs else "")
                    + (" (below res.)" if below else "")
                )
        md.append("| " + " | ".join(row) + " |")
    (out_dir / "table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    if hot:
        print("\nTOO-GOOD STOP RULE: AUC >= 0.95 in", hot[:20], "..." if len(hot) > 20 else "")
    return 0


def _ints(s: str) -> list[int]:
    return [int(x) for x in s.split(",") if x.strip()]


def _floats(s: str) -> list[float]:
    return [float(x) for x in s.split(",") if x.strip()]


if __name__ == "__main__":
    sys.exit(main())
