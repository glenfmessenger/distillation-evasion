#!/usr/bin/env python
"""Amendment B8 item 1: which detector produces the flags in the headline cells and in the
constructed organisation, on every placement day, from the existing all-day evidence.

Reads docs/evidence/m5/placements.json and docs/evidence/m6/scale_cells.json (no run);
writes docs/evidence/m7/decompose.json and decompose_table.md.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "docs" / "evidence"


def decompose(per: list[dict]) -> dict:
    """Per detector: share of days on which it is non-zero, on which it is the largest, and on
    which it is the only non-zero one; plus the share of days with any flag."""
    dets = sorted({d for p in per for d in p["flagged"]})
    nz, top, only = Counter(), Counter(), Counter()
    n_any = 0
    for p in per:
        fl = p["flagged"]
        nonzero = [d for d in dets if fl.get(d, 0.0) > 0.0]
        if not nonzero:
            continue
        n_any += 1
        for d in nonzero:
            nz[d] += 1
        mx = max(fl.get(d, 0.0) for d in dets)
        for d in dets:
            if fl.get(d, 0.0) == mx:
                top[d] += 1
        if len(nonzero) == 1:
            only[nonzero[0]] += 1
    n = len(per)
    return {
        "days": n,
        "days_any": n_any,
        "p_any": n_any / n,
        "by_detector": {
            d: {
                "nonzero_share_of_flagged_days": (nz[d] / n_any) if n_any else 0.0,
                "largest_share_of_flagged_days": (top[d] / n_any) if n_any else 0.0,
                "only_share_of_flagged_days": (only[d] / n_any) if n_any else 0.0,
            }
            for d in dets
        },
    }


def main() -> int:
    pl = json.loads((EV / "m5" / "placements.json").read_text())
    sc = json.loads((EV / "m6" / "scale_cells.json").read_text())
    out = {}
    for c in pl["cells"]:
        if c["source"] == "table5" and c["kind"] == "roundrobin" and c["n"] in (10, 100):
            out[f"round-robin {c['n']}"] = decompose(c["per"])
        if (
            c["source"] == "search"
            and c["n"] == 50
            and c["count_cap"] == 26
            and c["session_mult"] == 10
            and c["stagger_h"] == 6
        ):
            out["search 50, stagger 6 h"] = decompose(c["per"])
        if (
            c["source"] == "search"
            and c["n"] == 100
            and c["count_cap"] == 26
            and c["session_mult"] == 10
            and c["stagger_h"] == 6
        ):
            out["search 100, stagger 6 h"] = decompose(c["per"])
    for d in sc["all_days"]:
        if d.get("name") and d["variant"] == "registered":
            out[d["name"].replace("_", " ")] = decompose(d["per"])
    fifty = out["search 50, stagger 6 h"]["by_detector"]
    cross = fifty.get("D10", {}).get("nonzero_share_of_flagged_days", 0.0) + fifty.get(
        "D11", {}
    ).get("nonzero_share_of_flagged_days", 0.0)
    per_account = max(
        v["nonzero_share_of_flagged_days"] for k, v in fifty.items() if k not in ("D10", "D11")
    )
    out["p43"] = {
        "per_account_max_share": per_account,
        "cross_account_share": cross,
        "holds": per_account > 0.5 and per_account > cross,
    }
    m7 = EV / "m7"
    m7.mkdir(exist_ok=True)
    (m7 / "decompose.json").write_text(json.dumps(out, indent=1))
    md = [
        "Flag decomposition on all placement days (B8 item 1): for each cell, the share of flagged days on which each detector is non-zero / the largest / the only one.",
        "| Cell | Days with any flag | "
        + " | ".join(f"{d}" for d in ("D1", "D2", "D3", "D9", "D10", "D11"))
        + " |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name, r in out.items():
        if name == "p43":
            continue
        cells = []
        for d in ("D1", "D2", "D3", "D9", "D10", "D11"):
            v = r["by_detector"].get(d)
            cells.append(
                "--"
                if v is None
                else f"{v['nonzero_share_of_flagged_days']:.2f}/{v['largest_share_of_flagged_days']:.2f}/{v['only_share_of_flagged_days']:.2f}"
            )
        md.append(
            f"| {name} | {r['p_any']:.2f} ({r['days_any']} of {r['days']}) | "
            + " | ".join(cells)
            + " |"
        )
    md.append(f"\nP43: {json.dumps(out['p43'])}")
    (m7 / "decompose_table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
