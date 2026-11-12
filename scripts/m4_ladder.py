#!/usr/bin/env python
"""The visibility ladder (PROTOCOL v2.0 §7): one table, campaign × level × detector, from the
committed per-level outputs. Unevaded cells come from m3_analyse (V0, V1) and m4_content (V2);
the cheapest V1-evading cell comes from m4_levers. Every number is read from a JSON on disk; a
missing file is an error, never a blank.

Usage: m4_ladder.py --out docs/evidence/m4/ladder.md
  --campaign "C-bench=m3_v1_pilot,v2_c_bench_levers,pilot_baseline"
  --campaign "C-real=v2_c_real,v2_c_real_levers,c_real_v2:20" --content-label v2_content_all
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dev_harness.paths import host_repo

LEVELS = {
    "V0 pattern": ["D3", "D4", "D5", "D6", "D7", "D8", "D8b", "D9"],
    "V1 volume": ["D1", "D2"],
    "V2 content": ["C1", "C2", "B1", "B2"],
    "V2 content (post-hoc, B1)": ["C2low", "C3"],
}


def load(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text())


def fmt(x, nd=2):
    return "n/a" if x is None else f"{x:.{nd}f}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", action="append", required=True)
    ap.add_argument("--content-label", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    root = host_repo() / "results" / "aggregates"
    content = load(root / "m4" / a.content_label / "content.json")
    lines = [
        "| Campaign | Level | Detector | Unit | Flagged at 1% | AUC | Note |",
        "|---|---|---|---|---|---|---|",
    ]
    price_lines = [
        "",
        "| Campaign, criterion | Cell with D1 and D2 at 0 flagged in all re-schedulings | Identities | Wall-clock h | Other detectors firing |",
        "|---|---|---|---|---|",
    ]
    for spec in a.campaign:
        name, _, rest = spec.partition("=")
        m3_label, lev_label, c_label = [x.strip() for x in rest.split(",")]
        m3 = load(root / "m3" / m3_label / "detectors.json")
        lev = load(root / "m4" / lev_label / "levers.json")
        cont = content["campaigns"][c_label]
        for level, dets in LEVELS.items():
            for det in dets:
                if level.startswith("V2 content"):
                    for unit in ("identity", "block100"):
                        r = cont[unit].get(det)
                        if r is None:
                            continue
                        note = (
                            "below resolution at 0.1%"
                            if content["calibration"][det]["0.001"]["below_resolution"]
                            else ""
                        )
                        lines.append(
                            f"| {name} | {level} | {det} | {unit} | {fmt(r['flagged']['0.01'])} | {fmt(r['auc'], 3)} | {note} |"
                        )
                else:
                    d = m3["detectors"].get(det)
                    if d is None:
                        continue
                    for pop, unit in (
                        ("campaign", d["grain"]),
                        ("campaign_split", d["grain"] + " (split view)"),
                    ):
                        if pop not in d["populations"]:
                            continue
                        r = d["populations"][pop]
                        b = r["budgets"]["0.01"]
                        note = "below resolution" if b["below_resolution"] else ""
                        lines.append(
                            f"| {name} | {level} | {det} | {unit} | {fmt(b['frac_flagged'])} | {fmt(r['auc'], 3)} | {note} |"
                        )
        clear = []
        for c in lev["cells"]:
            ok = all(
                s["detectors"]["D1"]["budgets"]["0.01"]["frac_flagged"] == 0
                and s["detectors"]["D2"]["budgets"]["0.01"]["frac_flagged"] == 0
                for s in c["per_seed"]
            )
            if not ok:
                continue
            wc = (
                sorted(s["price"]["wall_clock_s"] for s in c["per_seed"])[len(c["per_seed"]) // 2]
                / 3600
            )
            others = sorted(
                {
                    det
                    for s in c["per_seed"]
                    for det, v in s["detectors"].items()
                    if det not in ("D1", "D2") and (v["budgets"]["0.01"]["frac_flagged"] or 0) > 0.1
                }
            )
            clear.append((c, wc, others))
        if not clear:
            price_lines.append(f"| {name} | none in the sweep | | | |")
            continue
        for label, key in (
            ("fewest identities", lambda t: (t[0]["n"], t[1])),
            ("least wall-clock", lambda t: (t[1], t[0]["n"])),
        ):
            c, wc, others = min(clear, key=key)
            price_lines.append(
                f"| {name}, {label} | n = {c['n']}, cap = {c['cap_per_hour'] or 'none'} per hour "
                f"(q = {c['q'] if c['q'] is not None else 'none'}) | {c['n']} | {wc:.1f} | {', '.join(others) or 'none'} |"
            )
    out = Path(a.out)
    out.write_text("\n".join(lines + price_lines) + "\n")
    print("\n".join(lines + price_lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
