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
    co = load(EV / "m4" / "coordination11_c_real.json")
    n_req = lev["n_campaign_records"]
    cap = lev["rate_caps"]["0.99"]
    med = lambda v: sorted(v)[len(v) // 2]  # noqa: E731
    fig, ax = plt.subplots(figsize=(5.2, 3.9))
    xs = [1, 10, 100, 1000, 10000]
    ax.plot(
        xs,
        [n_req / cap / x for x in xs],
        color=MUTED,
        lw=1.2,
        ls="--",
        label=f"identities × hours = N / {cap}",
    )
    clear_x, clear_y, hit_x, hit_y = [], [], [], []
    for c in lev["cells"]:
        s = c["per_seed"]
        wc = med([x["price"]["wall_clock_s"] / 3600 for x in s])
        d1 = med([x["detectors"]["D1"]["budgets"]["0.01"]["frac_flagged"] for x in s])
        d2 = med([x["detectors"]["D2"]["budgets"]["0.01"]["frac_flagged"] for x in s])
        (hit_x if max(d1, d2) > 0.1 else clear_x).append(c["n"])
        (hit_y if max(d1, d2) > 0.1 else clear_y).append(wc)
    ax.scatter(hit_x, hit_y, s=28, color=ORANGE, label="volume level fires (D1 or D2)", zorder=3)
    ax.scatter(clear_x, clear_y, s=28, color=BLUE, label="clears the volume level", zorder=3)
    hx, hy, labels = [], [], []
    for c in co["cells"]:
        if c["kind"] != "heterogeneous":
            continue
        s = c["per_seed"]
        hx.append(c["n"])
        hy.append(med([x["price"]["wall_clock_s"] / 3600 for x in s]))
        labels.append((c["stagger_h"], med([x["joint_max_flagged_1pct"] for x in s])))
    ax.scatter(
        hx,
        hy,
        s=34,
        marker="^",
        color=AQUA,
        label="heterogeneous split (D10, D11 scored)",
        zorder=4,
    )
    for x, y, (S, j) in zip(hx, hy, labels):
        if S in (0, 72):
            dx, dy = (8, 4) if S == 72 else (8, -9)
            if x == 1000:
                dx = -8
            ax.annotate(
                f"stagger {S} h: max flagged {j:.2f}",
                (x, y),
                textcoords="offset points",
                xytext=(dx, dy),
                fontsize=6.5,
                color=INK,
                ha="left" if dx > 0 else "right",
            )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("identities", fontsize=8, color=INK)
    ax.set_ylabel("scheduled wall-clock (hours)", fontsize=8, color=INK)
    ax.tick_params(labelsize=7, colors=INK)
    ax.grid(True, which="major", color=GRID, lw=0.6)
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.legend(fontsize=6.5, frameon=False, loc="lower left")
    ax.set_title(
        "Price of clearing the volume level, ordinary-prompt campaign", fontsize=8, color=INK
    )
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
