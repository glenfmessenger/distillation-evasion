#!/usr/bin/env python
"""Paper figures from committed evidence (docs/evidence). Fails on a missing source.

Figure 1: the visibility ladder as a heatmap (campaign × detector, fraction flagged at 1%, with
the AUC printed in each cell). Figure 2: the price surface (identities × wall-clock) with the
volume-level law and the cross-identity detectors' cells. Palette: the dataviz reference set,
validated (blue #2a78d6, orange #eb6834, aqua #1baf7a; sequential ramp in one hue).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "docs" / "evidence"
OUT = ROOT / "paper" / "figures"
BLUE, ORANGE, AQUA, INK, MUTED, GRID = (
    "#2a78d6",
    "#eb6834",
    "#1baf7a",
    "#0b0b0b",
    "#52514e",
    "#e6e5e1",
)
CAMPAIGNS = [
    ("C-bench", EV / "m3" / "m3_v1_pilot.json", "pilot_baseline"),
    ("C-real s0", EV / "m4" / "m3_c_real.json", "c_real_v2:20"),
    ("C-real s1", EV / "m4" / "m3_c_real_s1.json", "c_real_v2_s1"),
    ("C-instr", EV / "m4" / "m3_c_instr.json", "c_instr_v2"),
]
ROWS = (
    [("V0", d) for d in ("D3", "D4", "D5", "D6", "D7", "D8", "D9")]
    + [("V1", d) for d in ("D1", "D2")]
    + [("V2", d) for d in ("C1", "C2", "B1", "B2")]
)


def load(p: Path) -> dict:
    if not p.exists():
        raise FileNotFoundError(p)
    return json.loads(p.read_text())


def fig_ladder() -> None:
    content = load(EV / "m4" / "content_instr.json")
    vals, aucs = [], []
    for level, det in ROWS:
        rv, ra = [], []
        for _, m3p, ckey in CAMPAIGNS:
            if level == "V2":
                r = content["campaigns"][ckey]["block100"][det]
                f, a = r["flagged"]["0.01"], r["auc"]
            else:
                r = load(m3p)["detectors"][det]["populations"]["campaign"]
                f, a = r["budgets"]["0.01"]["frac_flagged"], r["auc"]
            rv.append(0.0 if f is None else f)
            ra.append(float("nan") if a is None else a)
        vals.append(rv)
        aucs.append(ra)
    cmap = LinearSegmentedColormap.from_list("blue_seq", ["#fcfcfb", "#cfe0f5", "#7fb0e6", BLUE])
    fig, ax = plt.subplots(figsize=(5.2, 5.6))
    ax.imshow(vals, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(CAMPAIGNS)))
    ax.set_xticklabels([c[0] for c in CAMPAIGNS], fontsize=8, color=INK)
    ax.set_yticks(range(len(ROWS)))
    ax.set_yticklabels([f"{lvl} {d}" for lvl, d in ROWS], fontsize=8, color=INK)
    for i, row in enumerate(vals):
        for j, v in enumerate(row):
            a = aucs[i][j]
            txt = f"{v:.2f}\nAUC {a:.2f}" if a == a else f"{v:.2f}\nAUC n/a"
            ax.text(
                j,
                i,
                txt,
                ha="center",
                va="center",
                fontsize=6.5,
                color="#ffffff" if v > 0.6 else INK,
            )
    for y in (6.5, 8.5):
        ax.axhline(y, color=GRID, lw=1)
    ax.set_title(
        "Fraction of campaign units flagged at the 1% budget (unevaded campaigns)",
        fontsize=8,
        color=INK,
    )
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    fig.tight_layout()
    fig.savefig(OUT / "ladder.pdf")
    fig.savefig(OUT / "ladder.png", dpi=200)
    plt.close(fig)


def fig_price() -> None:
    lev = load(EV / "m4" / "levers_c_real.json")
    l9 = load(EV / "m4" / "l9_search.json")
    n_req = lev["n_campaign_records"]
    cap = lev["rate_caps"]["0.99"]
    med = lambda v: sorted(v)[len(v) // 2]  # noqa: E731
    fig, ax = plt.subplots(figsize=(5.2, 4.6))
    xs = [1, 10, 100, 1000]
    xs = [x for x in xs if n_req / cap / x >= 1.0] + [n_req / cap]
    ax.plot(
        xs,
        [n_req / cap / x for x in xs],
        color=MUTED,
        lw=1.2,
        ls="--",
        label=f"bound: accounts × hours = N / {cap}",
    )
    styles = {
        0: ("o", "no re-timing"),
        26: ("s", f"rate cap {cap}/h"),
        8: ("D", "stricter caps"),
        2: ("D", None),
    }
    seen = set()
    for c in lev["cells"]:
        capc = c["cap_per_hour"]
        if c["n"] > 1 and capc not in (0, cap):
            continue  # the figure shows the cells of the price table only
        s = c["per_seed"]
        wc = med([x["price"]["wall_clock_s"] / 3600 for x in s])
        d1 = med([x["detectors"]["D1"]["budgets"]["0.01"]["frac_flagged"] for x in s])
        marker, lab = styles[capc]
        colour = ORANGE if d1 > 0.1 else BLUE
        key = (capc if capc in (0, cap) else "strict", d1 > 0.1)
        label = None
        if key not in seen:
            seen.add(key)
            what = "rate detector fires" if d1 > 0.1 else "clears the rate detector"
            label = f"{lab or 'stricter caps'}, {what}"
        ax.scatter([c["n"]], [wc], s=30, marker=marker, color=colour, label=label, zorder=3)
    cl = [c for c in l9["cells"] if c["clears"]]
    corr = {
        (c["n"], c["stagger_h"], c["count_cap"], float(c["session_mult"])): c["corrected_sessions"][
            "clears"
        ]
        for c in load(EV / "m13" / "clearing.json")["cells"]
        if c["source"] == "search"
    }

    def still(c: dict) -> bool:
        return corr[(c["n"], c["stagger_h"], c["count_cap"], float(c["session_mult"]))]

    lost = [c for c in cl if not still(c)]
    kept = [c for c in cl if still(c)]
    ax.scatter(
        [c["n"] for c in lost],
        [c["wall_clock_h"] for c in lost],
        s=26,
        marker="^",
        facecolors="none",
        edgecolors=AQUA,
        linewidths=0.9,
        label="wider search: clears as registered only",
        zorder=4,
    )
    ax.scatter(
        [c["n"] for c in kept],
        [c["wall_clock_h"] for c in kept],
        s=26,
        marker="^",
        color=AQUA,
        label="wider search: also clears with recalibrated cadence\n(flags counted over all sessions)",
        zorder=5,
    )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("accounts", fontsize=8, color=INK)
    ax.set_ylabel("scheduled wall-clock (hours)", fontsize=8, color=INK)
    ax.tick_params(labelsize=7, colors=INK)
    ax.grid(True, which="major", color=GRID, lw=0.6)
    for sp in ax.spines.values():
        sp.set_color(GRID)
    ax.legend(fontsize=8, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=1)
    fig.tight_layout()
    fig.savefig(OUT / "price.pdf")
    fig.savefig(OUT / "price.png", dpi=200)
    plt.close(fig)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    fig_ladder()
    fig_price()
    print("figures:", sorted(p.name for p in OUT.glob("*.pdf")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
