#!/usr/bin/env python
"""Amendment B4 item 1: benign coordinated populations scored by D10 and D11 at the registered
thresholds. Three constructed populations, built from real identity-days and placed on the
absolute timeline exactly as campaigns are (5 placements). No teacher calls. Writes
results/aggregates/m4/<out-label>/{controls.json,table.md}.
"""

from __future__ import annotations

import argparse
import json
import sys

import numpy as np

from dev_harness.detectors import stats as D
from dev_harness.detectors.coordination import (
    Standardiser,
    birth_burst,
    births,
    features,
    identity_days,
    nearest_neighbour_radius,
    same_day_density,
    score_births,
    score_campaign,
)
from dev_harness.paths import host_repo
from dev_harness.records import RequestRecord

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from m4_coordination import timeline_abs  # noqa: E402

NS = 1_000_000_000
BUDGETS = (0.01, 0.001)


def _rec(ident: str, sess: str, idx: int, t_s: float, turns: int = 1) -> RequestRecord:
    t = int(t_s * NS)
    return RequestRecord(
        run_id="control",
        identity_id=ident,
        session_id=sess,
        request_index_in_session=idx,
        arm="benign:constructed",
        t_send_ns=t,
        t_sched_ns=t,
        t_first_byte_ns=t,
        t_done_ns=t,
        prompt_tokens=None,
        generated_tokens=None,
        total_tokens=None,
        reasoning_tokens=None,
        cached_prompt_tokens=None,
        turn_count=turns,
        finish_reason=None,
        http_status=None,
        in_flight=False,
    )


def organisation(
    benign: list[RequestRecord], rng: np.random.Generator, t0: float
) -> list[RequestRecord]:
    """50 real heavy identities keep their own records; births re-timed uniformly over 30 days
    from t0 and activity shifted so that each identity's day starts in business hours."""
    by: dict[str, list[RequestRecord]] = {}
    for r in benign:
        by.setdefault(r.identity_id, []).append(r)
    heavy = [i for i, v in by.items() if len(v) >= 30]
    pick = rng.choice(len(heavy), size=50, replace=False)
    out = []
    for k in pick:
        recs = sorted(by[heavy[k]], key=lambda x: x.t_sched_ns)
        base = recs[0].t_sched_ns / NS
        start = t0 + rng.uniform(0, 30 * 86400)
        start = (start // 86400) * 86400 + 9 * 3600 + rng.uniform(0, 3600)  # 09:00 to 10:00
        for r in recs:
            out.append(
                r.model_copy(
                    update={
                        "identity_id": f"org:{heavy[k]}",
                        "session_id": f"org:{heavy[k]}:{r.session_id.rsplit(':', 1)[-1]}",
                        "t_sched_ns": int((start + (r.t_sched_ns / NS - base)) * NS),
                    }
                )
            )
    return out


def batch_job(rng: np.random.Generator, t0: float) -> list[RequestRecord]:
    """50 keys born within a minute, each 40 requests per day at 90 s with jitter, one session a day, 10 days."""
    out = []
    for key in range(50):
        birth = t0 + rng.uniform(0, 60)
        for day in range(10):
            t = birth + day * 86400
            for i in range(40):
                out.append(_rec(f"batch:k{key}", f"batch:k{key}:d{day}", i, t))
                t += 90.0 + rng.uniform(0, 30)
    return out


def eval_fleet(rng: np.random.Generator, t0: float, native_gap: float) -> list[RequestRecord]:
    """20 keys born within a minute, each one burst of 200 requests at native pace, weekly for 4 weeks."""
    out = []
    for key in range(20):
        birth = t0 + rng.uniform(0, 60)
        for week in range(4):
            t = birth + week * 7 * 86400
            for i in range(200):
                out.append(_rec(f"eval:k{key}", f"eval:k{key}:w{week}", i, t))
                t += native_gap + rng.uniform(0, native_gap)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-label", required=True)
    ap.add_argument("--out-label", required=True)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument(
        "--native-gap",
        type=float,
        default=0.39,
        help="campaign native inter-request gap, s (F49 c_real)",
    )
    a = ap.parse_args()
    root = host_repo()
    bdir = root / "benign" / a.benign_label
    man = json.loads((bdir / "manifest_abs.json").read_text())
    benign = timeline_abs(bdir / "timeline_abs.jsonl")
    rows_b = identity_days(benign)
    zb_raw = np.stack([features(r) for r in rows_b])
    days_b = np.array([r["day"] for r in rows_b])
    std = Standardiser(zb_raw)
    zb = std(zb_raw)
    r = nearest_neighbour_radius(zb, days_b)
    dens_b = same_day_density(zb, days_b, r)
    cal = {str(b): D.calibrate(dens_b.astype(float).tolist(), "high", b) for b in BUDGETS}
    bb = np.array(sorted(births(benign).values()))
    cal11 = {
        str(b): D.calibrate(birth_burst(bb, 600.0).astype(float).tolist(), "high", b)
        for b in BUDGETS
    }
    day_min, day_max = int(man["t_min_s"] // 86400), int(man["t_max_s"] // 86400) - 40
    results = {}
    md = [
        f"Benign coordinated populations (B4 item 1) against D10 (threshold {cal['0.01']['threshold']:.0f} / {cal['0.001']['threshold']:.0f}) and D11 at 10 min (threshold {cal11['0.01']['threshold']:.0f} / {cal11['0.001']['threshold']:.0f}); {a.seeds} placements.\n",
        "| Population | Identities | Identity-days | D10 flagged 1% | D10 flagged 0.1% | D11 flagged 1% | D11 flagged 0.1% |",
        "|---|---|---|---|---|---|---|",
    ]
    for name in ("organisation", "batch_job", "eval_fleet"):
        per = []
        for seed in range(a.seeds):
            rng = np.random.default_rng(2000 + seed)
            t0 = float(rng.integers(day_min, day_max)) * 86400
            if name == "organisation":
                recs = organisation(benign, rng, t0)
            elif name == "batch_job":
                recs = batch_job(rng, t0)
            else:
                recs = eval_fleet(rng, t0, a.native_gap)
            rows_c = identity_days(recs)
            zc = std(np.stack([features(x) for x in rows_c]))
            dc = np.array([x["day"] for x in rows_c])
            dens = score_campaign(zb, days_b, zc, dc, r)
            cb = np.array(list(births(recs).values()))
            v11 = score_births(bb, cb, 600.0)
            per.append(
                {
                    "seed": seed,
                    "identities": len(set(x.identity_id for x in recs)),
                    "identity_days": len(rows_c),
                    "d10": {
                        b: float(np.mean([D.fires(float(v), cal[b]) for v in dens])) for b in cal
                    },
                    "d11": {
                        b: float(np.mean([D.fires(float(v), cal11[b]) for v in v11])) for b in cal11
                    },
                    "d10_median_density": float(np.median(dens)),
                }
            )
        results[name] = per
        m = lambda v: sorted(v)[len(v) // 2]  # noqa: E731
        md.append(
            f"| {name} | {per[0]['identities']} | {per[0]['identity_days']} | "
            f"{m([p['d10']['0.01'] for p in per]):.2f} [{min(p['d10']['0.01'] for p in per):.2f}, {max(p['d10']['0.01'] for p in per):.2f}] | "
            f"{m([p['d10']['0.001'] for p in per]):.2f} | "
            f"{m([p['d11']['0.01'] for p in per]):.2f} [{min(p['d11']['0.01'] for p in per):.2f}, {max(p['d11']['0.01'] for p in per):.2f}] | "
            f"{m([p['d11']['0.001'] for p in per]):.2f} |"
        )
        print(f"{name}: done", flush=True)
    out_dir = root / "results" / "aggregates" / "m4" / a.out_label
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "controls.json").write_text(
        json.dumps(
            {"calibration_d10": cal, "calibration_d11": cal11, "radius": r, "populations": results},
            indent=1,
        )
    )
    (out_dir / "table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
