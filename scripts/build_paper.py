#!/usr/bin/env python
"""Paper build, step 1: every number in the manuscript comes from a committed evidence file.

Reads docs/evidence/**/*.json and writes paper/macros/generated.tex (\\newcommand macros, letters
only in names) and paper/tables/*.tex (booktabs tables). A missing or malformed source raises;
nothing is defaulted (global rules 1, 4). Run from the repo root: python scripts/build_paper.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "docs" / "evidence"
OUT_M = ROOT / "paper" / "macros" / "generated.tex"
OUT_T = ROOT / "paper" / "tables"

SUITES = [
    ("math500", "MATH-500"),
    ("gsm8k_test", "GSM8K"),
    ("humaneval", "HumanEval"),
    ("mbpp_test", "MBPP"),
]
SUITE_KEY = {"math500": "Math", "gsm8k_test": "Gsm", "humaneval": "HumanEval", "mbpp_test": "Mbpp"}
ARMS = [
    ("teacher_qwen3_8b", "Teacher (Qwen3-8B)", "Teacher"),
    ("student_base_chat_s0", "Student, untouched", "BaseChat"),
    ("student_after_sft_s0", "Fine-tuned on copied answers", "AfterSft"),
    ("student_after_repair_s0", "Fine-tuned, then reinforcement learning", "AfterRepair"),
    ("student_repair_only_s0", "Reinforcement learning only", "RepairOnly"),
]
DETS_V0 = ["D3", "D4", "D5", "D6", "D7", "D8", "D8b", "D9"]
DETS_V1 = ["D1", "D2"]
DETS_V2 = ["C1", "C2", "B1", "B2"]
DETS_V2_POST = ["C2low", "C3"]
CAMPAIGNS = [  # name, m3 json, levers json, content key (in content_s1.json)
    (
        "C-bench",
        EV / "m3" / "m3_v1_pilot.json",
        EV / "m4" / "levers_c_bench.json",
        "pilot_baseline",
    ),
    (
        "C-real, seed 0",
        EV / "m4" / "m3_c_real.json",
        EV / "m4" / "levers_c_real.json",
        "c_real_v2:20",
    ),
    (
        "C-real, seed 1",
        EV / "m4" / "m3_c_real_s1.json",
        EV / "m4" / "levers_c_real_s1.json",
        "c_real_v2_s1",
    ),
    ("C-instr", EV / "m4" / "m3_c_instr.json", EV / "m4" / "levers_c_instr.json", "c_instr_v2"),
]
CONTENT = EV / "m4" / "content_instr.json"

macros: dict[str, str] = {}


def load(p: Path) -> dict:
    if not p.exists():
        raise FileNotFoundError(f"evidence source missing: {p}")
    return json.loads(p.read_text())


def macro(name: str, value) -> None:
    if not re.fullmatch(r"[A-Za-z]+", name):
        raise ValueError(f"macro names are letters only: {name}")
    if name in macros:
        raise ValueError(f"duplicate macro {name}")
    macros[name] = str(value)


def num(x: float, nd: int = 2) -> str:
    return f"{x:.{nd}f}"


def pct(x: float, nd: int = 0) -> str:
    return f"{100 * x:.{nd}f}"


def intc(x: int) -> str:
    return f"{int(x):,}"


def frac_or_na(x) -> str:
    return "n/a" if x is None else num(x)


def main() -> int:
    OUT_T.mkdir(parents=True, exist_ok=True)
    OUT_M.parent.mkdir(parents=True, exist_ok=True)

    # ---- capability side table (A7 rule) and the registered-path numbers shown once
    rows_a7, rows_reg = [], []
    for label, text, key in ARMS:
        d = load(EV / "m2" / "scores" / f"{label}_a8.json")  # amendment A8 (F65)
        cells = []
        for s, _ in SUITES:
            c = d["suites"][s]["pass_at_1"]
            cells.append(f"{num(c['mean'])} [{num(c['lo'])}, {num(c['hi'])}]")
            macro(f"Cap{key}{SUITE_KEY[s]}", num(c["mean"]))
            macro(f"Cap{key}{SUITE_KEY[s]}Lo", num(c["lo"]))
            macro(f"Cap{key}{SUITE_KEY[s]}Hi", num(c["hi"]))
        rows_a7.append(f"{text} & " + " & ".join(cells) + r" \\")
        reg = EV / "m2" / "scores" / f"{label}_registered.json"
        if reg.exists():
            r = load(reg)
            rows_reg.append(
                f"{text} & "
                + " & ".join(num(r["suites"][s]["pass_at_1"]["mean"]) for s, _ in SUITES)
                + r" \\"
            )
    _table(
        "capability.tex",
        "l" + "c" * len(SUITES),
        "Arm & " + " & ".join(n for _, n in SUITES) + r" \\",
        rows_a7,
    )
    rows_a7 = []
    for label, text, key in ARMS:
        d7 = load(EV / "m2" / "scores" / f"{label}.json")
        rows_a7.append(
            f"{text} & "
            + " & ".join(num(d7["suites"][s_]["pass_at_1"]["mean"]) for s_, _ in SUITES)
            + r" \\"
        )
        for s_, _ in SUITES:
            macro(f"CapASeven{key}{SUITE_KEY[s_]}", num(d7["suites"][s_]["pass_at_1"]["mean"]))
    _table(
        "capability_a7.tex",
        "l" + "c" * len(SUITES),
        "Arm & " + " & ".join(n for _, n in SUITES) + r" \\",
        rows_a7,
    )
    _table(
        "capability_registered.tex",
        "l" + "c" * len(SUITES),
        "Arm & " + " & ".join(n for _, n in SUITES) + r" \\",
        rows_reg,
    )

    # ---- ladder table
    content = load(CONTENT)
    macro("NBenignContentUnits", intc(content["n_benign_units"]))
    macro("ContentModel", content["model"].replace("_", r"\_"))
    macro("MatchedN", intc(content["n_match"]))
    ladder_rows = []
    for name, m3p, levp, ckey in CAMPAIGNS:
        m3 = load(m3p)
        tag = _camel(name)
        macro(f"NRecords{tag}", intc(m3["n_campaign_records"]))
        for level, dets in (("V0 pattern", DETS_V0), ("V1 volume", DETS_V1)):
            for det in dets:
                dd = m3["detectors"][det]
                r = dd["populations"]["campaign"]
                b = r["budgets"]["0.01"]
                flagged = frac_or_na(b["frac_flagged"])
                auc = "n/a" if r["auc"] is None else num(r["auc"], 3)
                note = "below res." if b["below_resolution"] else ""
                ladder_rows.append(
                    f"{name} & {level} & {det} & {dd['grain']} & {flagged} & {auc} & {note} \\\\"
                )
                macro(f"Flag{tag}{_camel(det)}", flagged)
                macro(f"Auc{tag}{_camel(det)}", auc)
        cont = content["campaigns"][ckey]
        for det in DETS_V2 + DETS_V2_POST:
            level = "V2 content" + (" (post hoc)" if det in DETS_V2_POST else "")
            for unit in ("identity", "block100"):
                r = cont[unit][det]
                flagged = frac_or_na(r["flagged"]["0.01"])
                auc = "n/a" if r["auc"] is None else num(r["auc"], 3)
                ladder_rows.append(
                    f"{name} & {level} & {det} & {unit} & {flagged} & {auc} & below res.\\ at 0.1\\% \\\\"
                )
                if unit == "block100":
                    macro(f"Flag{tag}{_camel(det)}", flagged)
                    macro(f"Auc{tag}{_camel(det)}", auc)
    # condensed ladder: one row per detector (per unit for V2), one column per campaign
    cond: dict[str, list[str]] = {}
    for name, m3p, levp, ckey in CAMPAIGNS:
        m3 = load(m3p)
        cont = content["campaigns"][ckey]
        for level, dets in (("V0", DETS_V0), ("V1", DETS_V1)):
            for det in dets:
                dd = m3["detectors"][det]
                r = dd["populations"]["campaign"]
                b = r["budgets"]["0.01"]
                key = f"{level} & {det} & {dd['grain']}"
                cond.setdefault(key, []).append(
                    f"{frac_or_na(b['frac_flagged'])} ({'n/a' if r['auc'] is None else num(r['auc'])})"
                )
        for det in DETS_V2 + DETS_V2_POST:
            for unit in ("identity", "block100"):
                r = cont[unit][det]
                key = f"V2{' post hoc' if det in DETS_V2_POST else ''} & {det} & {unit}"
                cond.setdefault(key, []).append(
                    f"{frac_or_na(r['flagged']['0.01'])} ({'n/a' if r['auc'] is None else num(r['auc'])})"
                )
    _table(
        "ladder.tex",
        "lll" + "c" * len(CAMPAIGNS),
        "Level & Detector & Unit & " + " & ".join(n for n, *_ in CAMPAIGNS) + " \\\\",
        [f"{k} & " + " & ".join(v) + " \\\\" for k, v in cond.items()],
    )
    _table(
        "ladder_full.tex",
        "llllccl",
        "Campaign & Level & Detector & Unit & Flagged at 1\\% & AUC & Note \\\\",
        ladder_rows,
    )

    # ---- price table (V1 levers)
    price_rows = []
    for name, _, levp, _ in CAMPAIGNS:
        lev = load(levp)
        tag = _camel(name)
        caps = lev["rate_caps"]
        macro(f"CapPerHour{tag}", intc(caps["0.99"]))
        for c in lev["cells"]:
            want = (c["n"], c["q"]) in [
                (1, None),
                (1, 0.99),
                (1, 0.9),
                (1, 0.5),
                (10, None),
                (10, 0.99),
                (100, None),
                (100, 0.99),
                (1000, None),
            ]
            if not want:
                continue
            med = lambda v: v[len(v) // 2]  # noqa: E731
            if c["n"] == 1 and c["q"] == 0.99:
                macro(
                    f"AucDThreeShaped{tag}",
                    num(med([x["detectors"]["D3"]["auc"] for x in c["per_seed"]]), 3),
                )
            d1 = sorted(
                x["detectors"]["D1"]["budgets"]["0.01"]["frac_flagged"] for x in c["per_seed"]
            )
            d2 = sorted(
                x["detectors"]["D2"]["budgets"]["0.01"]["frac_flagged"] for x in c["per_seed"]
            )
            wc = sorted(x["price"]["wall_clock_s"] for x in c["per_seed"])
            med = lambda v: v[len(v) // 2]  # noqa: E731
            others = sorted(
                {
                    det
                    for x in c["per_seed"]
                    for det, v in x["detectors"].items()
                    if det not in ("D1", "D2") and (v["budgets"]["0.01"]["frac_flagged"] or 0) > 0.1
                }
            )
            if name == "C-real, seed 0":
                price_rows.append(
                    f"{intc(lev['n_campaign_records'])} & {c['n']} & {'none' if c['q'] is None else c['cap_per_hour']} & {num(med(wc) / 3600, 1)} & {num(med(d1))} & {num(med(d2))} \\\\"
                )
            cell = (
                f"N{c['n']}"
                + ("Shaped" if c["q"] is not None else "")
                + (f"Q{_camel(str(c['q']))}" if c["q"] not in (None, 0.99) else "")
            )
            macro(f"Hours{tag}{_camel(cell)}", num(med(wc) / 3600, 1))
            macro(f"FlagDOne{tag}{_camel(cell)}", num(med(d1)))
    lev8 = load(EV / "m4" / "levers_c_real_8k.json")
    for c in lev8["cells"]:
        if (c["n"], c["q"]) not in [(100, None), (1000, None), (1000, 0.99)]:
            continue
        d1 = sorted(x["detectors"]["D1"]["budgets"]["0.01"]["frac_flagged"] for x in c["per_seed"])
        d2 = sorted(x["detectors"]["D2"]["budgets"]["0.01"]["frac_flagged"] for x in c["per_seed"])
        wc = sorted(x["price"]["wall_clock_s"] for x in c["per_seed"])
        med = lambda v: v[len(v) // 2]  # noqa: E731
        others = sorted(
            {
                det
                for x in c["per_seed"]
                for det, v in x["detectors"].items()
                if det not in ("D1", "D2") and (v["budgets"]["0.01"]["frac_flagged"] or 0) > 0.1
            }
        )
        price_rows.append(
            f"{intc(lev8['n_campaign_records'])} & {c['n']} & {'none' if c['q'] is None else c['cap_per_hour']} & {num(med(wc) / 3600, 1)} & {num(med(d1))} & {num(med(d2))} \\\\"
        )
        macro(f"FlagDOneEightK{_camel(str(c['n']))}{'Shaped' if c['q'] else ''}", num(med(d1)))
        macro(
            f"OthersEightK{_camel(str(c['n']))}{'Shaped' if c['q'] else ''}",
            ", ".join(others) or "none",
        )
    _table(
        "price.tex",
        "rrrrcc",
        r"Requests & Accounts & Cap/h & Hours & D1 & D2 \\",
        price_rows,
    )
    macro("NReschedulings", intc(len(load(CAMPAIGNS[0][2])["cells"][0]["per_seed"])))

    # ---- content breadth table
    variants = [
        ("Replay calibration, bge-small, n=30, block 100", "content_s1.json"),
        ("Heavy-account calibration", "content_heavy.json"),
        ("bge-base encoder", "content_bgebase.json"),
        ("Matched n = 10", "content_nm10.json"),
        ("Matched n = 100 (heavy)", "content_nm100_heavy.json"),
        ("Block 50", "content_b50.json"),
        ("Block 500", "content_b500.json"),
    ]
    # extra rows (after review): the second seed and the uniform benign control, primary settings
    variants += [
        ("Seed 1, primary settings", "content_s1.json", "c_real_v2_s1"),
        (
            "Uniform benign control, primary settings",
            "content_ctrl.json",
            "control:uniform_firstturns",
        ),
        (
            "Uniform benign control, heavy calibration",
            "content_ctrl_heavy.json",
            "control:uniform_firstturns",
        ),
    ]
    breadth_rows = []
    for text, fn, *alt in variants:
        d = load(EV / "m4" / fn)
        creal = alt[0] if alt else "c_real_v2:20"
        blockkey = [k for k in d["campaigns"][creal] if k.startswith("block")][0]
        cells = []
        for ckey in ("pilot_baseline", creal):
            if alt and ckey == "pilot_baseline":
                cells += ["--"] * 4
                continue
            r = d["campaigns"][ckey][blockkey]
            cells += [frac_or_na(r[det]["flagged"]["0.01"]) for det in ("C2", "C2low", "C3", "B1")]
        mark = "$^\\dagger$" if int(0.01 * d["n_benign_units"]) < 10 else ""
        breadth_rows.append(
            f"{text}{mark} & {intc(d['n_benign_units'])} & " + " & ".join(cells) + r" \\"
        )
    _table(
        "content_breadth.tex",
        "lr" + "c" * 8,
        r"Variant & Benign units & \multicolumn{4}{c}{C-bench blocks} & \multicolumn{4}{c}{C-real or control blocks} \\ & & C2 & C2low & C3 & B1 & C2 & C2low & C3 & B1 \\",
        breadth_rows,
    )
    heavy = load(EV / "m4" / "content_heavy.json")
    macro("NHeavyUsers", intc(heavy["n_benign_units"]))

    # ---- pooled design (R3) table
    r3 = load(EV / "m4" / "r3batch_firstturn_ctrl.json")
    macro("PooledBatch", intc(r3["batch"]))
    macro("PooledNullDraws", intc(r3["null_samples"]))
    macro("PooledNRef", intc(r3["n_reference"]))
    macro("PooledNHeld", intc(r3["n_heldout"]))
    pooled_rows = [
        f"Benign held-out (heavy accounts) & {r3['benign_heldout']['median']:.2e} & {num(r3['benign_heldout']['flagged']['fpr_0.01'])} \\\\",
        f"Benign held-out, first turns only & {r3['benign_heldout_first_turns']['median']:.2e} & {num(r3['benign_heldout_first_turns']['flagged']['fpr_0.01'])} \\\\",
        f"Benign conversation-uniform first turns (control) & {r3['controls']['uniform_firstturns']['median']:.2e} & {num(r3['controls']['uniform_firstturns']['flagged']['fpr_0.01'])} \\\\",
    ]
    for ckey, text in (
        ("pilot_baseline", "C-bench, pure window"),
        ("c_real_v2", "C-real (long run), pure window"),
    ):
        p = r3["campaigns"][ckey]["pure"]
        pooled_rows.append(f"{text} & {p['median']:.2e} & {num(p['flagged']['fpr_0.01'])} \\\\")
    r3i = load(EV / "m4" / "r3batch_instr.json")
    p = r3i["campaigns"]["c_instr_v2"]["pure"]
    pooled_rows.append(
        f"C-instr, pure window & {p['median']:.2e} & {num(p['flagged']['fpr_0.01'])} \\\\"
    )
    _table(
        "pooled.tex",
        r">{\raggedright\arraybackslash}p{4.3cm}cc",
        r"Window & Median MMD$^2$ & Flagged at 1\% \\",
        pooled_rows,
    )
    share = load(EV / "m4" / "r3batch_share.json")
    share_rows = []
    for src, ckey, text in (
        (share, "pilot_baseline", "C-bench"),
        (share, "c_real_v2", "C-real, seed 0 (long run)"),
        (share, "c_real_v2_s1", "C-real, seed 1"),
        (r3i, "c_instr_v2", "C-instr"),
    ):
        cells = []
        for f in ("0.01", "0.02", "0.05", "0.1", "0.25", "0.5"):
            cells.append(num(src["campaigns"][ckey][f"mixed_{f}"]["flagged"]["fpr_0.01"]))
        share_rows.append(f"{text} & " + " & ".join(cells) + r" \\")
    _table(
        "share.tex",
        "l" + "c" * 6,
        r"Campaign & 1\% & 2\% & 5\% & 10\% & 25\% & 50\% \\",
        share_rows,
    )

    # ---- D10 coordination table (C-real seed 0; the other campaigns give the same cells)
    co = load(EV / "m4" / "coordination11_c_real.json")
    macro("DElevenThresholdTen", intc(co["calibration_d11"]["600"]["0.01"]["threshold"]))
    macro("DElevenThresholdSixty", intc(co["calibration_d11"]["3600"]["0.01"]["threshold"]))
    macro("NBenignIdentityDays", intc(co["n_benign_identity_days"]))
    macro("NBenignIdentitiesAbs", intc(co["n_benign_identities"]))
    macro("DTenThresholdOne", intc(co["calibration"]["0.01"]["threshold"]))
    macro("DTenThresholdTenth", intc(co["calibration"]["0.001"]["threshold"]))
    macro("DTenRadius", num(co["radius"], 3))
    rows = []
    for c in co["cells"]:
        want = (c["kind"], c["n"], c["shaped"], c["stagger_h"]) in {
            ("roundrobin", 10, True, None),
            ("roundrobin", 100, True, None),
            ("roundrobin", 1000, True, None),
            ("heterogeneous", 100, True, 0),
            ("heterogeneous", 100, True, 6),
            ("heterogeneous", 100, True, 24),
            ("heterogeneous", 1000, True, 0),
            ("heterogeneous", 1000, True, 24),
            ("heterogeneous", 1000, True, 72),
        }
        if not want:
            continue
        sd = c["per_seed"]
        m = lambda v: sorted(v)[len(v) // 2]  # noqa: E731
        f1 = [x["flagged"]["0.01"] for x in sd]
        f01 = [x["flagged"]["0.001"] for x in sd]
        wc = [x["price"]["wall_clock_s"] / 3600 for x in sd]
        kind = "round-robin" if c["kind"] == "roundrobin" else "heterogeneous"
        stag = "" if c["stagger_h"] is None else str(c["stagger_h"])
        d11 = [x["d11"]["600"]["flagged"]["0.01"] for x in sd]
        d2 = [x["timeline_detectors"]["D2"]["0.01"] for x in sd]
        joint = [x["joint_max_flagged_1pct"] for x in sd]
        rows.append(
            f"{kind} & {c['n']} & {stag} & {num(m(f1))} [{num(min(f1))}, {num(max(f1))}] & {num(m(f01))} & {num(m(d11))} & {num(max(d11))} & {num(m(d2))} & {num(m(joint))} & {num(m(wc), 1)} \\\\"
        )
        tag = f"{_camel(kind)}{_camel(str(c['n']))}" + (f"S{_camel(stag)}" if stag else "")
        macro(f"FlagDTen{tag}", num(m(f1)))
        macro(f"FlagDEleven{tag}", num(m(d11)))
        macro(f"FlagDElevenMax{tag}", num(max(d11)))
        macro(f"FlagDTwoLever{tag}", num(m(d2)))
        macro(f"Joint{tag}", num(m(joint)))
        macro(f"HoursDTen{tag}", num(m(wc), 1))
    _table(
        "coordination.tex",
        "lrrccccccr",
        r"Split & Identities & Stagger (h) & D10 at 1\% & D10 at 0.1\% & D11 at 1\% & D11 max & D2 at 1\% & Joint max & Wall-clock (h) \\",
        rows,
    )

    # ---- expected alert volume (B4 item 4): benign units per day and alerts per day at each budget
    tl = load(EV / "m4" / "coordination11_c_real.json")
    corpus_days = 387.0  # docs/evidence: manifest_abs span_days
    alert_rows = []
    m3c = load(EV / "m4" / "m3_c_real.json")
    for det in DETS_V0 + DETS_V1:
        dd = m3c["detectors"][det]
        b1 = dd["populations"]["campaign"]["budgets"]["0.01"]
        b01 = dd["populations"]["campaign"]["budgets"]["0.001"]
        mark = r"$^\dagger$" if b01["below_resolution"] else ""
        alert_rows.append(
            f"{det} & {dd['grain']} & {intc(b1['n_benign'])} & {b1['n_benign'] / corpus_days:.0f} & {b1['n_exceed'] / corpus_days:.1f} & {b01['n_exceed'] / corpus_days:.2f}{mark} \\\\"
        )
    for det, key, grain in (
        ("D10", "calibration", "identity-day"),
        ("D11", "calibration_d11", "identity birth"),
    ):
        c = tl[key] if key == "calibration" else tl[key]["600"]
        alert_rows.append(
            f"{det} & {grain} & {intc(c['0.01']['n_benign'])} & {c['0.01']['n_benign'] / corpus_days:.0f} & {c['0.01']['n_exceed'] / corpus_days:.1f} & {c['0.001']['n_exceed'] / corpus_days:.2f} \\\\"
        )
    _table(
        "alerts.tex",
        "llrrrr",
        r"Detector & Unit & Units & Per day & Alerts/day 1\% & at 0.1\% \\",
        alert_rows,
    )
    macro("CorpusDays", intc(corpus_days))
    tman = load(EV / "m4" / "timeline_abs_manifest.json")
    macro("CorpusRequestsPerDay", intc(round(tman["requests"] / tman["span_days"])))
    macro("CorpusSessionsPerDay", intc(round(tman["sessions"] / tman["span_days"])))
    macro("CorpusRequests", intc(tman["requests"]))

    # ---- benign coordinated populations (B4 item 1)
    ctrl = load(EV / "m4" / "coord_controls.json")
    ctrl_rows = []
    for name, text in (
        ("organisation", "Organisation, real accounts, staggered creation"),
        ("batch_job", "Batch job, 50 accounts created together"),
        ("eval_fleet", "Evaluation fleet, 20 accounts created together"),
    ):
        per = ctrl["populations"][name]
        m = lambda v: sorted(v)[len(v) // 2]  # noqa: E731
        d10 = [x["d10"]["0.01"] for x in per]
        d11 = [x["d11"]["0.01"] for x in per]
        ctrl_rows.append(
            f"{text} & {per[0]['identities']} & {num(m(d10))} [{num(min(d10))}, {num(max(d10))}] & {num(m(d11))} [{num(min(d11))}, {num(max(d11))}] \\\\"
        )
        macro(f"CtrlDTen{_camel(name)}", num(m(d10)))
        macro(f"CtrlDEleven{_camel(name)}", num(m(d11)))
    _table(
        "controls.tex",
        r">{\raggedright\arraybackslash}p{2.9cm}rcc",
        r"Population & Accounts & D10 & D11 \\",
        ctrl_rows,
    )

    # ---- prediction register
    preds = load(EV / "predictions.json")
    esc = lambda x: x.replace("%", "\\%")  # noqa: E731 - LaTeX comment character in statements
    pred_rows = [
        f"{esc(p['id'])} & {esc(p['protocol'])} & {esc(p['prediction'])} & {esc(p['outcome'])} \\\\"
        for p in preds
    ]
    _table(
        "predictions.tex",
        r"ll>{\raggedright\arraybackslash}p{7.6cm}>{\raggedright\arraybackslash}p{3.4cm}",
        r"Prediction & Protocol & Statement & Outcome \\",
        pred_rows,
    )
    n_failed = sum(1 for p in preds if p["outcome"].startswith("failed"))
    macro("NPredictions", intc(len(preds)))
    macro("NFailedPredictions", intc(n_failed))

    # ---- D3 on completion times (B4 item 3)
    d3 = load(EV / "m4" / "d3_completion.json")
    for ckey, tag in (("c_real_v2:20", "CRealSeedZero"), ("pilot_baseline", "CBench")):
        macro(f"AucDThreeCompletion{tag}", num(d3["campaigns"][ckey]["completion"]["auc"], 3))
        macro(f"MedianCvCompletion{tag}", num(d3["campaigns"][ckey]["completion"]["median_cv"]))
        macro(f"MedianCvSend{tag}", num(d3["campaigns"][ckey]["send"]["median_cv"]))

    # ---- combined adaptive attacker L9 (B4 item 2)
    l9 = load(EV / "m4" / "l9_search.json")
    clearing = [c for c in l9["cells"] if c["clears"]]
    macro("NSearchCells", intc(l9["n_cells"]))
    macro("NClearingCells", intc(len(clearing)))
    macro("NClearingCellsNoStagger", intc(sum(1 for c in clearing if c["stagger_h"] == 0)))
    cheap = min(clearing, key=lambda c: (c["wall_clock_h"], c["n"]))
    few = min(clearing, key=lambda c: (c["n"], c["wall_clock_h"]))
    macro("LNineCheapestHours", num(cheap["wall_clock_h"], 1))
    macro("LNineCheapestIdentities", intc(cheap["n"]))
    macro("LNineCheapestStagger", intc(cheap["stagger_h"]))
    macro("LNineCheapestJoint", num(cheap["joint_max"]))
    macro("LNineFewestHours", num(few["wall_clock_h"], 1))
    macro("LNineFewestIdentities", intc(few["n"]))
    shp = load(EV / "m4" / "l9_search_shape.json")
    macro("NClearingCellsAll", intc(shp["n_clearing_all"]))
    shape_max = max((v or 0.0) for c in shp["cells"] for v in c["shape_median_flagged"].values())
    macro("SearchShapeMax", num(shape_max))
    l9_rows = []
    for c in sorted(clearing, key=lambda c: (c["wall_clock_h"], c["n"]))[:8]:
        m = c["median_flagged"]
        l9_rows.append(
            f"{c['n']} & {c['count_cap']} & {c['session_mult']:g} & {c['stagger_h']} & {num(m['D2'])} & {num(m['D3'])} & {num(m['D10'])} & {num(m['D11'])} & {num(c['joint_max'])} & {num(c['wall_clock_h'], 1)} \\\\"
        )
    _table(
        "search.tex",
        "rrrrcccccr",
        r"Identities & Count cap & Session mult. & Stagger (h) & D2 & D3 & D10 & D11 & Joint max & Wall-clock (h) \\",
        l9_rows,
    )

    # ---- protocol constants used in prose (docs/evidence/constants.json, each with its source)
    for cname, cval in load(EV / "constants.json").items():
        if not cname.startswith("_"):
            macro(cname, cval["value"])

    # ---- label macros (names that contain digits, so prose never types one)
    for det in DETS_V0 + DETS_V1 + DETS_V2 + DETS_V2_POST:
        macro(f"Name{_camel(det)}", det)
    for key, text in (("Zero", "V0"), ("One", "V1"), ("Two", "V2")):
        macro(f"Level{key}", text)
    macro("NameDOneZero", "D10")
    macro("NameDOneOne", "D11")
    macro("SuiteMath", "MATH-500")
    macro("SuiteGsm", "GSM8K")
    macro("SuiteHumanEval", "HumanEval")
    macro("SuiteMbpp", "MBPP")
    macro("TeacherName", "Qwen3-8B")
    macro("StudentName", "Qwen3-1.7B-Base")

    # ---- counts
    m3b = load(EV / "m4" / "m3_c_real.json")
    macro("NBenignReplayRecords", intc(m3b["n_benign_replay_records"]))
    macro(
        "NBenignTimelineIdentities",
        intc(m3b["detectors"]["D1"]["populations"]["campaign"]["budgets"]["0.01"]["n_benign"]),
    )
    rep = load(EV / "m3" / "replay_m3_v1_manifest.json")
    macro("NBenignReplaySessions", intc(rep["sessions"]))
    pm = load(EV / "m4" / "c_real_v2_prompts_manifest.json")
    macro("NCrealCandidates", intc(pm["counts"]["candidates"]))
    macro("NCrealEightK", intc(pm["n"]))
    m8 = load(EV / "m4" / "m3_c_real_8k.json")
    macro("NRecordsCrealEightK", intc(m8["n_campaign_records"]))

    build_review_tables()
    build_revision_tables()
    build_second_round_tables()
    build_adversary_tables()
    build_followup_tables()
    build_api_baseline()
    OUT_M.write_text("".join(f"\\newcommand{{\\{k}}}{{{v}}}\n" for k, v in sorted(macros.items())))
    print(f"{len(macros)} macros, {len(list(OUT_T.glob('*.tex')))} tables")
    return 0


STAT_TEXT = {
    "D1": "max requests in any sliding hour",
    "D2": "sessions per day",
    "D3": "CV of inter-arrival times",
    "D4": "KS distance, output lengths",
    "D5": "median reasoning share",
    "D6": "KS distance, prompt lengths",
    "D7": "mean cached-prefix share",
    "D8": "JSD over length cells",
    "D8b": "distinct length cells",
    "D9": "single-turn fraction",
    "D10": "same-day profile neighbours",
    "D11": "accounts created within 10 min",
    "C1": "JSD over topic clusters",
    "C2": "embedding MMD",
    "B1": "benchmark membership share",
    "B2": "shared-suffix share",
}
GRAIN = {"identity": "account", "session": "session"}
REVIEW_CAMPAIGNS = [
    ("C-bench", "m3/m3_v1_pilot.json", "m4/b5_c_bench", "pilot_baseline", "CBench"),
    ("C-real, seed 0", "m4/m3_c_real.json", "m4/b5_c_real", "c_real_v2:20", "CRealSeedZero"),
    ("C-real, seed 1", "m4/m3_c_real_s1.json", "m4/b5_c_real_s1", "c_real_v2_s1", "CRealSeedOne"),
    ("C-instr", "m4/m3_c_instr.json", "m4/b5_c_instr", "c_instr_v2", "CInstr"),
]


def build_review_tables() -> None:
    """Tables and macros added in the author-review restructure (decision 43)."""
    content = load(CONTENT)
    m3c = load(EV / "m4" / "m3_c_real.json")
    co = load(EV / "m4" / "coordination11_c_real.json")
    med = lambda v: sorted(v)[len(v) // 2]  # noqa: E731

    # ---- method summary: detector, level, unit, calibration, n, threshold, realised FPR, alerts/day
    rows = []

    def mrow(det, level, unit, calset, c, per_day):
        fpr = 100.0 * c["n_exceed"] / c["n_benign"]
        thr = c["threshold"]
        thr_s = f"{thr:.0f}" if abs(thr - round(thr)) < 1e-9 and abs(thr) >= 1 else f"{thr:.3g}"
        alerts = f"{c['n_exceed'] / 387.0:.1f}" if per_day else "--"
        mark = "$^\\dagger$" if c["n_exceed"] < 10 else ""
        rows.append(
            f"{det}{mark} & {STAT_TEXT[det]} & {level} & {unit} & {calset} & {intc(c['n_benign'])} & "
            f"{'$>$' if c['direction'] == 'high' else '$<$'} {thr_s} & {fpr:.2f}\\% & {alerts} \\\\"
        )
        dname = det
        macro(f"RealisedFpr{_camel(dname)}", f"{fpr:.2f}\\%")
        macro(f"RealisedThr{_camel(dname)}", thr_s)

    for det in DETS_V0:
        dd = m3c["detectors"][det]
        tl = dd["benign_source"] == "timeline"
        mrow(
            det,
            "pattern",
            GRAIN[dd["grain"]],
            "timeline" if tl else "replay",
            dd["populations"]["campaign"]["budgets"]["0.01"],
            tl,
        )
    for det in DETS_V1:
        dd = m3c["detectors"][det]
        mrow(
            det,
            "volume",
            "account",
            "timeline",
            dd["populations"]["campaign"]["budgets"]["0.01"],
            True,
        )
    mrow("D10", "cross-account", "account-day", "timeline", co["calibration"]["0.01"], True)
    mrow("D11", "cross-account", "account", "timeline", co["calibration_d11"]["600"]["0.01"], True)
    for det in DETS_V2:
        mrow(
            det,
            "content",
            "account, block",
            "replay prompts",
            content["calibration"][det]["0.01"],
            False,
        )
    _table(
        "methods.tex",
        r"ll@{\hspace{6pt}}llllrrr",
        r"Detector & Statistic & Level & Unit & Calibration & Benign units & Flag if & Realised rate & Alerts/day \\",
        rows,
    )

    # ---- ladder with campaign unit counts
    cond: dict[str, list[str]] = {}
    for name, m3rel, _b5, ckey, tag in REVIEW_CAMPAIGNS:
        m3 = load(EV / m3rel)
        cont = content["campaigns"][ckey]
        for level, dets in (("Pattern", DETS_V0), ("Volume", DETS_V1)):
            for det in dets:
                dd = m3["detectors"][det]
                r = dd["populations"]["campaign"]
                key = f"{level} & {det} & {GRAIN[dd['grain']]} & {r['n_units']}"
                cond.setdefault(key, []).append(
                    f"{frac_or_na(r['budgets']['0.01']['frac_flagged'])} ({'n/a' if r['auc'] is None else num(r['auc'])})"
                )
        for det in DETS_V2 + DETS_V2_POST:
            for unit, ulabel in (("identity", "account"), ("block100", "block")):
                r = cont[unit][det]
                lvl = "Content, post hoc" if det in DETS_V2_POST else "Content"
                key = f"{lvl} & {det} & {ulabel} & {r['n_units']}"
                cond.setdefault(key, []).append(
                    f"{frac_or_na(r['flagged']['0.01'])} ({'n/a' if r['auc'] is None else num(r['auc'])})"
                )
                if unit == "identity":
                    macro(
                        f"AucAccount{tag}{_camel(det)}",
                        "n/a" if r["auc"] is None else num(r["auc"]),
                    )
    _table(
        "ladder2.tex",
        "lllr" + "c" * len(REVIEW_CAMPAIGNS),
        "Level & Detector & Unit & Units & " + " & ".join(c[0] for c in REVIEW_CAMPAIGNS) + r" \\",
        [f"{k} & " + " & ".join(v) + r" \\" for k, v in cond.items()],
    )

    # ---- session-definition sensitivity (amendment 5)
    srows = []
    for det in ("D2", "D3", "D4", "D5", "D6", "D7"):
        for label, suffix in (
            ("declared blocks", None),
            ("idle-gap rule", "gap"),
            ("size-matched", "benign_sized"),
        ):
            cells, units = [], None
            for name, m3rel, b5, _ckey, tag in REVIEW_CAMPAIGNS:
                d = load(EV / m3rel) if suffix is None else load(EV / f"{b5}_{suffix}.json")
                r = d["detectors"][det]["populations"]["campaign"]
                units = r["n_units"]
                f = r["budgets"]["0.01"]["frac_flagged"]
                cells.append(f"{frac_or_na(f)} ({'n/a' if r['auc'] is None else num(r['auc'])})")
                if suffix:
                    macro(f"Flag{_camel(det)}{_camel(suffix)}{tag}", frac_or_na(f))
                    macro(
                        f"Auc{_camel(det)}{_camel(suffix)}{tag}",
                        "n/a" if r["auc"] is None else num(r["auc"]),
                    )
                    if det == "D2":
                        macro(f"Median{_camel(det)}{_camel(suffix)}{tag}", f"{r['median']:.0f}")
            srows.append(f"{det} & {label} & {units} & " + " & ".join(cells) + r" \\")
    _table(
        "sessions.tex",
        "llr" + "c" * len(REVIEW_CAMPAIGNS),
        "Detector & Campaign sessions & Units & "
        + " & ".join(c[0] for c in REVIEW_CAMPAIGNS)
        + r" \\",
        srows,
    )
    macro(
        "DTwoThreshold",
        intc(m3c["detectors"]["D2"]["populations"]["campaign"]["budgets"]["0.01"]["threshold"]),
    )

    # ---- cross-account table (accounts wording, includes the 72 h cell at 100 accounts)
    crows = []
    want = [
        ("roundrobin", 10, None),
        ("roundrobin", 100, None),
        ("roundrobin", 1000, None),
        ("heterogeneous", 100, 0),
        ("heterogeneous", 100, 6),
        ("heterogeneous", 100, 24),
        ("heterogeneous", 100, 72),
        ("heterogeneous", 1000, 0),
        ("heterogeneous", 1000, 6),
        ("heterogeneous", 1000, 24),
        ("heterogeneous", 1000, 72),
    ]
    for c in co["cells"]:
        if not c["shaped"] or (c["kind"], c["n"], c["stagger_h"]) not in want:
            continue
        sd = c["per_seed"]
        f1 = [x["flagged"]["0.01"] for x in sd]
        d11 = [x["d11"]["600"]["flagged"]["0.01"] for x in sd]
        d2 = [x["timeline_detectors"]["D2"]["0.01"] for x in sd]
        joint = [x["joint_max_flagged_1pct"] for x in sd]
        wc = [x["price"]["wall_clock_s"] / 3600 for x in sd]
        kind = "round-robin" if c["kind"] == "roundrobin" else "heterogeneous"
        stag = "" if c["stagger_h"] is None else str(c["stagger_h"])
        crows.append(
            f"{kind} & {intc(c['n'])} & {stag} & {num(med(f1))} [{num(min(f1))}, {num(max(f1))}] & "
            f"{num(med(d11))} [{num(min(d11))}, {num(max(d11))}] & {num(med(d2))} [{num(min(d2))}, {num(max(d2))}] & {num(med(joint))} [{num(min(joint))}, {num(max(joint))}] & {num(med(wc), 1)} \\\\"
        )
        if c["kind"] == "roundrobin" and c["n"] == 10:
            macro("JointMaxWorstRoundRobinTen", num(max(joint)))
            macro("NPlacementsFlaggedRoundRobinTen", intc(sum(1 for j in joint if j > 0.10)))
    _table(
        "coordination2.tex",
        "lrrccccr",
        r"Split & Accounts & Stagger (h) & D10 & D11 & D2 & Joint max & Hours \\",
        crows,
    )

    # ---- search table and grid text
    l9 = load(EV / "m4" / "l9_search.json")
    g = l9["grid"]
    macro("GridAccounts", ", ".join(intc(v) for v in g["n"]))
    macro("GridDrawCap", ", ".join(intc(v) for v in g["count_cap"]))
    macro("GridSessionMult", ", ".join(f"{v:g}" for v in g["session_mult"]))
    macro("GridStagger", ", ".join(intc(v) for v in g["stagger_h"]))
    clearing = sorted(
        [c for c in l9["cells"] if c["clears"]], key=lambda c: (c["wall_clock_h"], c["n"])
    )
    lrows = []
    for c in clearing[:8]:
        m = c["median_flagged"]
        jseed = [max(x["flagged"].values()) for x in c["per_seed"]]
        lrows.append(
            f"{intc(c['n'])} & {c['count_cap']} & {c['session_mult']:g} & {c['stagger_h']} & {num(m['D2'])} & {num(m['D3'])} & {num(m['D10'])} & {num(m['D11'])} & {num(c['joint_max'])} [{num(min(jseed))}, {num(max(jseed))}] & {num(c['wall_clock_h'], 1)} \\\\"
        )
        if c is clearing[0]:
            macro("LNineCheapestJointWorst", num(max(jseed)))
    _table(
        "search2.tex",
        "rrrrcccccr",
        r"Accounts & Draw cap & Session multiplier & Stagger (h) & D2 & D3 & D10 & D11 & Joint max & Hours \\",
        lrows,
    )

    # ---- prediction register (clean labels) and counts
    preds = load(EV / "predictions.json")

    def _pred_key(q):  # first protocol first, then by prediction number, clauses together
        m = re.search(r"P(\d+)", q["id"])
        return (0 if q["protocol"].startswith("v1") else 1, int(m.group(1)) if m else 0, q["id"])

    preds = sorted(preds, key=_pred_key)
    esc = lambda x: x.replace("%", "\\%")  # noqa: E731

    def _is_revision(q):
        m = re.search(r"P(\d+)", q["id"])
        return bool(m) and int(m.group(1)) >= 25 and q["protocol"].startswith("v2")

    def _is_adversary(q):  # amendments eight to ten (P43 onwards) go in the third table
        mm = re.search(r"P(\d+)", q["id"])
        return _is_revision(q) and int(mm.group(1)) >= 43

    for fname, subset in (
        ("predictions2.tex", [q for q in preds if not _is_revision(q)]),
        ("predictions3.tex", [q for q in preds if _is_revision(q) and not _is_adversary(q)]),
        ("predictions4.tex", [q for q in preds if _is_adversary(q) and "am. 8" in q["protocol"]]),
        (
            "predictions5.tex",
            [q for q in preds if _is_adversary(q) and "am. 8" not in q["protocol"]],
        ),
    ):
        _table(
            fname,
            r"ll>{\raggedright\arraybackslash}p{7.6cm}>{\raggedright\arraybackslash}p{3.2cm}",
            r"Prediction & Protocol & Statement & Outcome \\",
            [
                f"{esc(q['id'])} & {esc(q['protocol'])} & {esc(q['prediction'])} & {esc(q['outcome'])} \\\\"
                for q in subset
            ],
        )
    n_fail = sum(1 for q in preds if q["outcome"].startswith("failed"))
    n_unt = sum(1 for q in preds if q["outcome"].startswith("not test"))
    macro("NPredAll", intc(len(preds)))
    macro("NPredFailed", intc(n_fail))
    macro("NPredUntested", intc(n_unt))
    macro("NPredHeld", intc(len(preds) - n_fail - n_unt))
    for pref, tag in (("v1", "VOne"), ("v2", "VTwo")):
        sub = [q for q in preds if q["protocol"].startswith(pref)]
        f = sum(1 for q in sub if q["outcome"].startswith("failed"))
        u = sum(1 for q in sub if q["outcome"].startswith("not test"))
        macro(f"NPred{tag}All", intc(len(sub)))
        macro(f"NPred{tag}Tested", intc(len(sub) - u))
        macro(f"NPred{tag}Held", intc(len(sub) - f - u))
        macro(f"NPred{tag}Failed", intc(f))

    # ---- volume bound and misc
    lev = load(EV / "m4" / "levers_c_real.json")
    cap = lev["rate_caps"]["0.99"]
    macro("BoundHours", num(lev["n_campaign_records"] / cap, 1))
    r3c = load(EV / "m4" / "r3batch_firstturn_ctrl.json")
    r3i2 = load(EV / "m4" / "r3batch_instr.json")
    ctrl_med = r3c["controls"]["uniform_firstturns"]["median"]
    macro("PooledInstrRatio", num(r3i2["campaigns"]["c_instr_v2"]["pure"]["median"] / ctrl_med, 1))
    macro(
        "PooledBenchRatio", num(r3c["campaigns"]["pilot_baseline"]["pure"]["median"] / ctrl_med, 1)
    )
    macro("ShapeRatePerHour", intc(cap - 1))
    macro("DOneMedianCReal", intc(m3c["detectors"]["D1"]["populations"]["campaign"]["median"]))
    shp = load(EV / "m4" / "l9_search_shape.json")
    macro(
        "NShapeUnscoreableCells",
        intc(
            sum(
                1
                for c in shp["cells"]
                if any(v is None for v in c["shape_median_flagged"].values())
            )
        ),
    )
    worst_over = sum(
        1
        for c in l9["cells"]
        if c["clears"] and max(max(x["flagged"].values()) for x in c["per_seed"]) > 0.10
    )
    macro("NClearingWorstOver", intc(worst_over))
    five = [
        load(EV / "m4" / f)["campaigns"]["pilot_baseline"]["mixed_0.05"]["flagged"]["fpr_0.01"]
        for f in (
            "r3batch_share.json",
            "r3batch_instr.json",
            "r3batch_firstturn.json",
            "r3batch_firstturn_ctrl.json",
        )
    ]
    macro("ShareBenchFiveMin", num(min(five)))
    macro("ShareBenchFiveMax", num(max(five)))
    macro(
        "MedianDTwoGapBench",
        f"{load(EV / 'm4' / 'b5_c_bench_gap.json')['detectors']['D2']['populations']['campaign']['median']:.0f}",
    )


def build_revision_tables() -> None:
    """Tables and macros from the revision analyses (amendment B6, decision 44)."""
    from statistics import median as _median

    m5 = EV / "m5"
    macro("TwentyFourHours", "24")
    macro("DTenFloor", "0.001")

    # ---- held-out calibration (B6 item 1)
    h = load(m5 / "heldout.json")
    order = DETS_V0 + DETS_V1 + ["D10", "D11"] + DETS_V2 + DETS_V2_POST
    rows = []
    for det in order:
        s = h["detectors"].get(det)
        if s is None:
            raise KeyError(f"held-out result missing for {det}")
        mark = "$^\\dagger$" if s["registered_below_resolution"] else ""
        lo, hi = s["median_split_ci"]
        k, n = s["median_split_k_n"]
        rows.append(
            f"{det}{mark} & {100 * s['registered_realised_fpr']:.2f}\\% & {100 * s['heldout_fpr_mean']:.2f}\\% & "
            f"[{100 * s['heldout_fpr_min']:.2f}\\%, {100 * s['heldout_fpr_max']:.2f}\\%] & {k}/{intc(n)} & "
            f"[{100 * lo:.2f}\\%, {100 * hi:.2f}\\%] \\\\"
        )
        macro(f"HeldoutFpr{_camel(det)}", f"{100 * s['heldout_fpr_mean']:.2f}\\%")
    _table(
        "heldout.tex",
        "lrrcrc",
        r"Detector & In-sample & Held-out mean & Held-out range & Median split $k/n$ & Exact 95\% CI \\",
        rows,
    )
    resolved = [d for d in order if not h["detectors"][d]["registered_below_resolution"]]
    macro("NHeldoutResolved", intc(len(resolved)))
    macro("NHeldoutInBand", intc(sum(1 for d in resolved if h["detectors"][d]["p25_mean_in_band"])))
    shifts = [
        abs(s["heldout_median"] - s["registered"])
        for dd in h["campaigns"].values()
        for s in dd.values()
        if s["registered"] is not None
    ]
    macro("HeldoutMaxCampaignShift", num(max(shifts)))
    c3u = h["campaigns"]["control:uniform_firstturns:identity"]["C3"]
    macro("CThreeControlSplitMax", num(c3u["heldout_max"]))
    c3b = h["campaigns"]["control:uniform_firstturns:block100"]["C3"]
    macro("CThreeControlBlockSplitMax", num(c3b["heldout_max"]))
    c3r = h["campaigns"]["c_real_v2:20:identity"]["C3"]
    macro("CThreeCRealSplitMax", num(c3r["heldout_max"]))
    macro("NHeldoutSplits", intc(h["splits"]))
    macro("HeldoutThrDTenMin", intc(h["detectors"]["D10"]["threshold_min"]))
    macro("HeldoutThrDTenMax", intc(h["detectors"]["D10"]["threshold_max"]))
    anyd = h["any_detector"]
    macro("AnyDetTimeline", pct(anyd["timeline_accounts"]["any"], 1) + "\\%")
    macro("AnyDetReplayPattern", pct(anyd["replayed_accounts"]["any_pattern_volume"], 1) + "\\%")
    macro("AnyDetReplayAll", pct(anyd["replayed_accounts"]["any_incl_cross_account"], 1) + "\\%")
    macro("NReplayAccountsAny", intc(anyd["replayed_accounts"]["n_accounts"]))
    macro("ReplayMeanSessions", num(anyd["replayed_accounts"]["mean_sessions_per_account"], 1))
    byd = anyd["replayed_accounts"]["by_detector"]
    top = max(byd, key=byd.get)
    macro("AnyDetReplayTopDet", top)
    macro("AnyDetReplayTopRate", pct(byd[top], 1) + "\\%")

    # ---- all-day placements (B6 item 2)
    pl = load(m5 / "placements.json")
    cells = pl["cells"]

    def find(**kw):
        for c in cells:
            if all(c.get(k) == v for k, v in kw.items()):
                return c
        raise KeyError(kw)

    prow = []

    def arow(label, c):
        s = c["summary_all"]
        e = c["summary_excluding_original_days"]

        def f(d):
            if d not in s:
                return "n/a"
            return f"{num(s[d]['median'])} [{num(s[d]['p5'])}, {num(s[d]['p95'])}]"

        st = "" if c["stagger_h"] is None else intc(c["stagger_h"])
        prow.append(
            f"{label} & {intc(c['n'])} & {st} & {intc(c['n_placements'])} & {num(s['wall_clock_h_median'], 1)} & {f('D10')} & {f('D11')} & "
            f"{num(s['joint_max']['median'])} [{num(s['joint_max']['p5'])}, {num(s['joint_max']['p95'])}] & "
            f"{num(s['p_any_unit_flagged'])} & {num(s['p_over_0.10'])} & {num(e['p_over_0.10'])} \\\\"
        )

    for c in cells:
        if c["source"] == "table5":
            arow("round-robin" if c["kind"] == "roundrobin" else "heterogeneous", c)
    search_cells = sorted(
        [c for c in cells if c["source"] == "search"],
        key=lambda c: (c["five_placement_wall_clock_h"], c["n"]),
    )
    seen_ns = set()
    for c in search_cells:  # one row per (accounts, stagger): the shortest schedule among them
        key = (c["n"], c["stagger_h"])
        if key in seen_ns:
            continue
        seen_ns.add(key)
        arow("search", c)
        if len(seen_ns) == 8:
            break
    _table(
        "placements.tex",
        "lrrrrcccccc",
        r"Split & Accounts & Stagger (h) & Days & Hours & D10 & D11 & Joint max & P(any) & P($>$0.10) & P($>$0.10), excl. \\",
        prow,
    )
    ten = find(source="table5", kind="roundrobin", n=10)
    macro("NPlacementDays", intc(ten["n_placements"]))
    macro("TenAccountPAnyDEleven", num(pl["predictions"]["P28_ten_account_p_any_d11"]))
    macro("TenAccountDElevenMedianAll", num(ten["summary_all"]["D11"]["median"]))
    macro("TenAccountDElevenPNinetyFive", num(ten["summary_all"]["D11"]["p95"]))
    macro("TenAccountPOver", num(ten["summary_all"]["p_over_0.10"]))
    hundred = find(source="table5", kind="roundrobin", n=100)
    macro("HundredAccountDTenMedianAll", num(hundred["summary_all"]["D10"]["median"]))
    macro("HundredAccountDTenPFive", num(hundred["summary_all"]["D10"]["p5"]))
    macro("NClearingAll", intc(len(search_cells)))
    macro("NClearingStillClear", intc(sum(1 for c in search_cells if c["summary_all"]["clears"])))
    reliable = [c for c in search_cells if c["summary_all"]["p_over_0.10"] <= 0.10]
    macro("NClearingReliable", intc(len(reliable)))
    best = min(reliable, key=lambda c: (c["summary_all"]["wall_clock_h_median"], c["n"]))
    macro("ReliableCheapestHours", num(best["summary_all"]["wall_clock_h_median"], 1))
    macro("ReliableCheapestAccounts", intc(best["n"]))
    macro("ReliableCheapestStagger", intc(best["stagger_h"]))
    macro("ReliableCheapestPOver", num(best["summary_all"]["p_over_0.10"]))
    macro("ReliableCheapestPAny", num(best["summary_all"]["p_any_unit_flagged"]))
    macro("ReliableCheapestHoursFive", num(best["five_placement_wall_clock_h"], 1))
    fewest = min(reliable, key=lambda c: (c["n"], c["summary_all"]["wall_clock_h_median"]))
    macro("ReliableFewestAccounts", intc(fewest["n"]))
    macro("ReliableFewestHours", num(fewest["summary_all"]["wall_clock_h_median"], 1))
    for tag, kw in (
        ("Fifty", dict(source="search", n=50, count_cap=26, session_mult=10.0, stagger_h=6)),
        ("Hundred", dict(source="search", n=100, count_cap=26, session_mult=10.0, stagger_h=6)),
    ):
        c = find(**kw)
        macro(f"Cell{tag}POver", num(c["summary_all"]["p_over_0.10"]))
        macro(f"Cell{tag}POverExcl", num(c["summary_excluding_original_days"]["p_over_0.10"]))
        macro(f"Cell{tag}JointPNinetyFive", num(c["summary_all"]["joint_max"]["p95"]))
        macro(f"Cell{tag}JointMedianAll", num(c["summary_all"]["joint_max"]["median"]))
        macro(f"Cell{tag}PAny", num(c["summary_all"]["p_any_unit_flagged"]))
        macro(f"Cell{tag}HoursFive", num(c["five_placement_wall_clock_h"], 1))
        macro(f"Cell{tag}HoursAll", num(c["summary_all"]["wall_clock_h_median"], 1))
    for t4 in pl["table4"]:
        w = t4["wall_clock_h"]
        tag = _camel(f"n{t4['n']}cap{t4['cap']}")
        macro(f"PriceRange{tag}", f"[{w['min']:.1f}, {w['max']:.1f}]")
    macro("NPriceReschedulings", intc(len(pl["table4"]) and 50))

    # ---- search summary by account count (replaces the per-cell recipe table)
    l9s = load(EV / "m4" / "l9_search.json")
    srows2 = []
    per_n = sorted({c["n"] for c in l9s["cells"]})
    for n in per_n:
        allc = [c for c in l9s["cells"] if c["n"] == n]
        cl = [c for c in allc if c["clears"]]
        rel = [c for c in search_cells if c["n"] == n and c["summary_all"]["p_over_0.10"] <= 0.10]
        if cl:
            hrs = [c["wall_clock_h"] for c in cl]
            stag = min(c["stagger_h"] for c in cl)
            hr_s = f"{min(hrs):.1f}--{max(hrs):.1f}"
            st_s = intc(stag)
        else:
            hr_s, st_s = "--", "--"
        rel_s = (
            f"{len(rel)} ({min(c['summary_all']['wall_clock_h_median'] for c in rel):.1f})"
            if rel
            else "0"
        )
        srows2.append(f"{intc(n)} & {len(cl)}/{len(allc)} & {st_s} & {hr_s} & {rel_s} \\\\")
    _table(
        "search_summary.tex",
        "rrrrr",
        r"Accounts & Clearing cells & Min.\ stagger (h) & Hours & Reliable cells (shortest, h) \\",
        srows2,
    )

    # ---- pooled-account control (B6 item 3b)
    pc = load(m5 / "pooled_control.json")
    prows = []
    for m in (5, 20, 100):
        c = pc["controls"][f"control:pooled_m{m}"]
        vals = [
            frac_or_na(c[u][d]["flagged"])
            for u in ("identity", "block100")
            for d in ("C1", "C2", "C2low", "C3", "B1", "B2")
        ]
        prows.append(
            f"{m} & {intc(c['n_groups'])} & {intc(c['block100']['C2']['n_units'])} & "
            + " & ".join(vals)
            + r" \\"
        )
        tag = _camel(str(m))
        macro(f"PooledCTwoLowAccount{tag}", frac_or_na(c["identity"]["C2low"]["flagged"]))
        macro(f"PooledCTwoLowBlock{tag}", frac_or_na(c["block100"]["C2low"]["flagged"]))
        macro(f"PooledCThreeAucAccount{tag}", num(c["identity"]["C3"]["auc"]))
    _table(
        "pooled_control.tex",
        "rrr" + "c" * 12,
        r"$m$ & Accounts & Blocks & \multicolumn{6}{c}{Per account} & \multicolumn{6}{c}{Per block} \\ & & & C1 & C2 & C2low & C3 & B1 & B2 & C1 & C2 & C2low & C3 & B1 & B2 \\",
        prows,
    )
    macro("NPooledBenignUnits", intc(pc["n_benign_units"]))

    # ---- sensitivity (B6 items 4 and 6)
    se = load(m5 / "sensitivity.json")
    vrows = []
    for fr in sorted({v["f"] for v in se["volume"]}):
        vs = [v for v in se["volume"] if v["f"] == fr]
        med = lambda k: _median([x[k] for x in vs])  # noqa: E731
        medc = lambda n, k: _median([x["cells"][n][k] for x in vs])  # noqa: E731
        vrows.append(
            f"{fr:g} & {intc(vs[0]['n_accounts'])} & {med('thr_d10'):.0f} & {med('thr_d11'):.0f} & "
            f"{num(medc('10', 'd11_median'))} & {num(medc('10', 'p_any_d11'))} & {num(medc('100', 'd10_median'))} & {num(medc('100', 'd11_median'))} \\\\"
        )
        tag = _camel(f"f{fr:g}".replace(".", "p"))
        macro(f"DElevenThr{tag}", f"{med('thr_d11'):.0f}")
        macro(f"DTenThr{tag}", f"{med('thr_d10'):.0f}")
        macro(f"TenAccountPAnyDEleven{tag}", num(medc("10", "p_any_d11")))
    _table(
        "volume_sensitivity.tex",
        "rrrrcccc",
        r"Fraction & Accounts & D10 thr. & D11 thr. & \multicolumn{2}{c}{10 accounts: D11, P(any)} & \multicolumn{2}{c}{100 accounts: D10, D11} \\",
        vrows,
    )
    names = {
        "registered": "registered (floor 0.001)",
        "drop_constant": "constant features dropped",
        "floor_1": "floor 1",
        "iqr": "IQR/1.349",
    }
    srows = []
    for v in se["scale"]:
        c = v["cells"]
        fmt = lambda k: f"{num(c[k]['median'])} [{num(c[k]['min'])}, {num(c[k]['max'])}]"  # noqa: E731
        srows.append(
            f"{names[v['variant']]} & {v['features_kept']} & {v['radius']:.2f} & {v['thr_d10']:.0f} & "
            f"{fmt('roundrobin_100')} & {fmt('organisation')} & {fmt('batch_job')} & {fmt('eval_fleet')} \\\\"
        )
    _table(
        "scale_sensitivity.tex",
        "lrrrcccc",
        r"Scale & Features & Radius & Threshold & Round-robin 100 & Organisation & Batch job & Eval.\ fleet \\",
        srows,
    )
    mad = dict(zip(se["feature_names"], se["scale"][0]["mad"]))
    macro("NConstantFeatures", intc(sum(1 for v in mad.values() if v == 0)))
    macro("ConstantFeatureNames", ", ".join(k.replace("_", " ") for k, v in mad.items() if v == 0))
    macro("NScaleVariantsHold", intc(sum(1 for ok in se["p36"].values() if ok)))
    macro("NScaleVariants", intc(len(se["p36"])))

    # ---- P22: request-weighted reference pool (B4 item 5, run in the revision)
    p22 = load(m5 / "r3batch_p22.json")
    macro("PTwoTwoCampaignMedian", f"{p22['campaigns']['c_real_v2']['pure']['median']:.2e}")
    macro("PTwoTwoControlMedian", f"{p22['controls']['uniform_firstturns']['median']:.2e}")
    macro(
        "PTwoTwoCampaignFlagged", num(p22["campaigns"]["c_real_v2"]["pure"]["flagged"]["fpr_0.01"])
    )
    macro(
        "PTwoTwoControlFlagged", num(p22["controls"]["uniform_firstturns"]["flagged"]["fpr_0.01"])
    )
    macro("PTwoTwoNIdentities", intc(p22["n_benign_identities_in_pools"]))
    macro("PTwoTwoNRef", intc(p22["n_reference"]))

    # ---- benign tails (B6 item 5)
    ta = load(m5 / "tails.json")
    d5, d3, b2, d1 = ta["D5"], ta["D3"], ta["B2"], ta["D1"]
    macro("DFiveNOver", intc(d5["n_over"]))
    macro("DFiveNRecordsOver", intc(d5["n_records_over"]))
    macro("DFiveTruncOver", pct(d5["truncated_share_over"]) + "\\%")
    macro("DFiveTruncReplay", pct(d5["truncated_share_replay"], 1) + "\\%")
    macro("DThreeNBelow", intc(d3["n_below"]))
    macro("DThreeShareThree", pct(d3["share_below_with_three_requests"]) + "\\%")
    macro("DThreeThrMinFive", num(d3["threshold_min_size"]["5"]["threshold"], 3))
    macro("DThreeThrMinTen", num(d3["threshold_min_size"]["10"]["threshold"], 3))
    macro("BTwoFullShare", pct(b2["share_b2_equal_1"], 1) + "\\%")
    macro("BTwoHalfShare", pct(b2["share_b2_at_least_0.5"], 1) + "\\%")
    macro("DOneAboveN", intc(d1["above"]["n"]))
    macro("DOneAboveMedianRequests", intc(d1["above"]["requests"]["50"]))
    macro("DOneAboveMedianSessions", intc(d1["above"]["sessions"]["50"]))
    macro("DOneAboveMedianSingleTurn", num(d1["above"]["single_turn_fraction"]["50"]))
    macro("DOneAbovePNinetySingleTurn", num(d1["above"]["single_turn_fraction"]["90"]))
    macro("DOneAboveMedianCv", num(d1["above"]["median_cadence_cv"]["50"]))
    macro("DOneAllMedianRequests", intc(d1["all"]["requests"]["50"]))


def build_second_round_tables() -> None:
    """Tables and macros from the second-round analyses (amendment B7, decision 46)."""
    m6 = EV / "m6"
    # ---- items 1 and 2: recalibrated thresholds
    th = load(m6 / "thresholds.json")
    d3, d5 = th["D3"], th["D5"]
    rows = []
    names = {
        "pilot_baseline": "C-bench",
        "c_real_v2:20": "C-real, seed 0",
        "c_real_v2_s1": "C-real, seed 1",
        "c_instr_v2": "C-instr",
    }
    rules = {"declared": "declared", "gap": "idle-gap", "benign-sized": "size-matched"}
    worst = 0.0
    for spec, label in names.items():
        for rule, rl in rules.items():
            cells = []
            for k in ("3", "5", "10"):
                r = d3["campaigns"][spec][f"{rule}:{k}"]
                cells.append(f"{frac_or_na(r['flagged'])} ({num(r['auc'])})")
                if k != "3" and r["flagged"] is not None:
                    worst = max(worst, r["flagged"])
            rows.append(f"{label} & {rl} & " + " & ".join(cells) + r" \\")
    _table(
        "cadence_sessions.tex",
        "llccc",
        r"Campaign & Sessions & Min.\ 3 & Min.\ 5 & Min.\ 10 \\",
        rows,
    )
    macro("DThreeRecalMaxFlagged", num(worst))
    macro("DThreeNSessionsMinFive", intc(d3["calibration"]["5"]["n_benign"]))
    macro("DThreeNSessionsMinTen", intc(d3["calibration"]["10"]["n_benign"]))
    macro("DFiveThrNoTrunc", num(d5["calibration_no_truncation"]["threshold"], 3))
    macro("BenignTruncShare", pct(d5["benign_truncated_share"], 1) + "\\%")
    for spec, tag in (
        ("pilot_baseline", "CBench"),
        ("c_real_v2:20", "CRealSeedZero"),
        ("c_real_v2_s1", "CRealSeedOne"),
        ("c_instr_v2", "CInstr"),
    ):
        c = d5["campaigns"][spec]
        macro(f"TruncShare{tag}", pct(c["truncated_share"], 1) + "\\%")
        macro(f"DFiveNoTruncFlagged{tag}", num(c["no_truncation"]["flagged"]))
        macro(f"DFiveNoTruncAuc{tag}", num(c["no_truncation"]["auc"]))

    # ---- item 4(c): pooled windows with filtered benign pools (batch 500)
    r5 = load(m6 / "r3batch_b500.json")
    r5f = load(m6 / "r3batch_b500_filtered.json")
    macro("PoolFilterDropped", intc(r5f["n_pool_prompts_filtered"]))
    macro("PoolFilterTotal", intc(r5f["n_pool_prompts_real"]))
    macro("PooledBatchSmall", intc(r5["batch"]))
    prow = []
    for label, rr in (("unfiltered pools", r5), ("filtered pools", r5f)):
        for name, key in (
            ("benign held-out, first turns", None),
            ("uniform benign control", "control"),
            ("C-real, pure window", "c_real_v2"),
            ("C-bench, pure window", "pilot_baseline"),
            ("C-real, mixed, share one quarter", "mixed"),
        ):
            if key is None:
                d = rr["benign_heldout_first_turns"]
            elif key == "control":
                d = rr["controls"]["uniform_firstturns"]
            elif key == "mixed":
                d = rr["campaigns"]["c_real_v2"]["mixed_0.25"]
            else:
                d = rr["campaigns"][key]["pure"]
            prow.append(
                f"{label} & {name} & {d['median']:.2e} & {num(d['flagged']['fpr_0.01'])} \\\\"
            )
    _table(
        "pooled_filtered.tex", "llrc", r"Pools & Window & Median MMD$^2$ & Flagged at 1\% \\", prow
    )
    cr, cf = (
        r5["campaigns"]["c_real_v2"]["pure"]["median"],
        r5f["campaigns"]["c_real_v2"]["pure"]["median"],
    )
    macro("PoolFilterCampaignRatio", num(cr / cf, 1))
    macro(
        "PoolFilterControlRatio",
        num(
            r5["controls"]["uniform_firstturns"]["median"]
            / r5f["controls"]["uniform_firstturns"]["median"],
            1,
        ),
    )
    macro(
        "PoolFilterCampaignFlagged",
        num(r5f["campaigns"]["c_real_v2"]["pure"]["flagged"]["fpr_0.01"]),
    )
    macro(
        "PoolFilterControlFlagged",
        num(r5f["controls"]["uniform_firstturns"]["flagged"]["fpr_0.01"]),
    )
    macro(
        "PoolFilterMixedQuarterBefore",
        num(r5["campaigns"]["c_real_v2"]["mixed_0.25"]["flagged"]["fpr_0.01"]),
    )
    macro(
        "PoolFilterMixedQuarterAfter",
        num(r5f["campaigns"]["c_real_v2"]["mixed_0.25"]["flagged"]["fpr_0.01"]),
    )

    # ---- item 4(a): controls under the second encoder
    cb = load(m6 / "content_ctrl_bgebase.json")
    u = cb["campaigns"]["control:uniform_firstturns"]
    bkey = [k for k in u if k.startswith("block")][0]
    macro("BgeBaseUniformCThreeBlock", frac_or_na(u[bkey]["C3"]["flagged"]["0.01"]))
    macro("BgeBaseUniformCTwoLowBlock", frac_or_na(u[bkey]["C2low"]["flagged"]["0.01"]))
    pb = load(m6 / "pooled_control_bgebase.json")
    for m in (5, 20, 100):
        c = pb["controls"][f"control:pooled_m{m}"]
        tag = _camel(str(m))
        macro(f"BgeBasePooledCThreeAccount{tag}", frac_or_na(c["identity"]["C3"]["flagged"]))
        macro(f"BgeBasePooledCThreeBlock{tag}", frac_or_na(c["block100"]["C3"]["flagged"]))
        macro(f"BgeBasePooledCTwoLowAccount{tag}", frac_or_na(c["identity"]["C2low"]["flagged"]))

    # ---- item 3 and 6: scalings on every cell; all-day controls
    sc = load(m6 / "scale_cells.json")
    ag = sc["p39"]["verdict_agreement"]
    macro("ScaleAgreeMin", pct(min(ag.values())) + "\\%")
    macro("NScaleCellsFive", intc(len(sc["five_placements"])))
    srows = []
    labels = {
        "registered": "registered",
        "drop_constant": "constant feature dropped",
        "floor_1": "floor one",
        "iqr": "IQR",
    }
    for d in sc["all_days"]:
        s = d["summary"]
        lab = (
            d.get("name", "").replace("_", " ")
            or f"{'round-robin' if d['kind'] == 'roundrobin' else 'search'} {intc(d['n'])}"
        )
        srows.append(
            f"{lab} & {labels[d['variant']]} & {intc(s['n'])} & {num(s['D10']['median'])} [{num(s['D10']['p5'])}, {num(s['D10']['p95'])}] & {num(s['D11']['median'])} & {num(s['p_any'])} & {num(s['p_over_0.10'])} \\\\"
        )
    _table(
        "scale_allday.tex",
        "llrcccc",
        r"Cell or population & Scaling & Days & D10 & D11 & P(any) & P($>$10\%) \\",
        srows,
    )
    for d in sc["all_days"]:
        if d.get("name"):
            tag = _camel(d["name"])
            macro(f"AllDay{tag}DTenMedian", num(d["summary"]["D10"]["median"]))
            macro(f"AllDay{tag}DElevenMedian", num(d["summary"]["D11"]["median"]))
            macro(f"AllDay{tag}PAny", num(d["summary"]["p_any"]))
    hp = sc["p39"]["headline_cells_p_over"]
    spread = max(max(v.values()) - min(v.values()) for v in hp.values())
    macro("ScaleHeadlineMaxShift", num(spread))

    # ---- item 5: overlay rows appended to the volume table
    ov = load(m6 / "volume_overlay.json")
    from statistics import median as _median

    orows = []
    for fr in sorted({v["f"] for v in ov["volume"]}):
        if fr <= 1.0:
            continue
        vs = [v for v in ov["volume"] if v["f"] == fr]
        med = lambda k: _median([x[k] for x in vs])  # noqa: E731
        medc = lambda n, k: _median([x["cells"][n][k] for x in vs])  # noqa: E731
        orows.append(
            f"$\\times${fr:g} & {intc(vs[0]['n_accounts'])} & {med('thr_d10'):.0f} & {med('thr_d11'):.0f} & {num(medc('10', 'd11_median'))} & {num(medc('10', 'p_any_d11'))} & {num(medc('100', 'd10_median'))} & {num(medc('100', 'd11_median'))} \\\\"
        )
        tag = _camel(f"x{fr:g}")
        macro(f"DElevenThr{tag}", f"{med('thr_d11'):.0f}")
        macro(f"DTenThr{tag}", f"{med('thr_d10'):.0f}")
        macro(f"TenAccountPAnyDEleven{tag}", num(medc("10", "p_any_d11")))
        macro(f"HundredAccountDTen{tag}", num(medc("100", "d10_median")))
    body = (OUT_T / "volume_sensitivity.tex").read_text()
    body = body.replace("\\bottomrule", "\n".join(orows) + "\n\\bottomrule", 1)
    (OUT_T / "volume_sensitivity.tex").write_text(body)


def build_adversary_tables() -> None:
    """Tables and macros from the adversary-pass analyses (amendment B8, decision 47)."""
    m7 = EV / "m7"
    from statistics import median as _median

    # ---- item 1: flag decomposition
    dc = load(m7 / "decompose.json")
    f50 = dc["search 50, stagger 6 h"]["by_detector"]
    macro("FiftyCellDThreeShare", pct(f50["D3"]["nonzero_share_of_flagged_days"]) + "\\%")
    macro("FiftyCellDThreeOnlyShare", pct(f50["D3"]["only_share_of_flagged_days"]) + "\\%")
    macro("FiftyCellDElevenShare", pct(f50["D11"]["nonzero_share_of_flagged_days"]) + "\\%")
    f100 = dc["search 100, stagger 6 h"]["by_detector"]
    macro("HundredCellDThreeShare", pct(f100["D3"]["nonzero_share_of_flagged_days"]) + "\\%")
    org = dc["organisation"]["by_detector"]
    macro("OrgDOneShare", pct(org["D1"]["nonzero_share_of_flagged_days"]) + "\\%")
    macro("OrgDTenShare", pct(org["D10"]["nonzero_share_of_flagged_days"]) + "\\%")
    macro("OrgDElevenShare", pct(org["D11"]["nonzero_share_of_flagged_days"]) + "\\%")
    macro("OrgDays", intc(dc["organisation"]["days"]))

    # ---- item 4: recalibrated replay detectors
    rc = load(m7 / "recalibrate.json")
    macro("DFiveThrMinTen", num(rc["min_ten"]["D5"]["threshold"], 3))
    macro("DSevenThrMinTen", num(rc["min_ten"]["D7"]["threshold"], 3))
    macro(
        "DFiveMinTenCBenchSized",
        num(rc["min_ten"]["D5"]["campaigns"]["pilot_baseline"]["benign-sized"]["flagged"]),
    )
    macro("RecalMaxFlagged", num(rc["p46"]["max_flagged"]))
    macro("NConstructedRemoved", intc(rc["n_constructed_accounts_removed"]))
    shifts = [
        abs(rc["no_constructed"][d]["threshold"] - rc["registered"][d]["threshold"])
        / abs(rc["registered"][d]["threshold"])
        for d in ("D4", "D5", "D6", "D7", "D8")
    ]
    macro("NoConstructedMaxThrShift", pct(max(shifts)) + "\\%")
    lo = rc["low_side"]["D4"]
    macro("DFourLowThr", num(lo["threshold"], 3))
    macro("DFourLowCRealDeclared", num(lo["campaigns"]["c_real_v2:20"]["flagged"]))
    macro("DFourLowCRealSized", num(lo["campaigns"]["c_real_v2:20"]["flagged_size_matched"]))
    macro("DFourLowCRealSeedOneDeclared", num(lo["campaigns"]["c_real_v2_s1"]["flagged"]))

    # ---- item 8: pilot truncation per arm
    for label, tag in (
        ("student_base_chat_s0", "Untouched"),
        ("student_after_sft_s0", "Sft"),
        ("student_after_repair_s0", "SftRl"),
        ("student_repair_only_s0", "RlOnly"),
        ("teacher_qwen3_8b", "Teacher"),
    ):
        d = load(EV / "m2" / "scores" / f"{label}_a8.json")["suites"]["math500"]
        macro(f"TruncArm{tag}", pct(d["n_finish_length"] / d["n_samples"], 1) + "\\%")

    # ---- item 3: budgets and size
    bg = load(m7 / "budgets.json")
    for b, tag in (("0.01", "One"), ("0.001", "Tenth"), ("0.0001", "Hundredth")):
        for det in ("D1", "D10", "D11"):
            v = bg["thresholds"][b][det]
            macro(f"Thr{_camel(det)}Budget{tag}", f"{v:.0f}")
    brow = []
    for c in bg["cross_cells"]:
        for b, tag in (("0.01", r"1\%"), ("0.001", r"0.1\%"), ("0.0001", r"0.01\%")):
            m = c["by_budget"][b]["median_flagged"]
            brow.append(
                f"{intc(int(c['size']))} & {c['cell']} & {num(c['hours'], 1)} & {tag} & "
                + " & ".join(num(m.get(d, float("nan"))) for d in ("D1", "D2", "D3", "D10", "D11"))
                + f" & {num(c['by_budget'][b]['joint_max'])} \\\\"
            )
    _table(
        "budgets.tex",
        "rlrrcccccc",
        r"Requests & Cell & Hours & Budget & D1 & D2 & D3 & D10 & D11 & Joint max \\",
        brow,
    )
    h = next(c for c in bg["cross_cells"] if c["size"] == "2000" and c["cell"] == "round-robin 100")
    macro("HundredDTenTenth", num(h["by_budget"]["0.001"]["median_flagged"]["D10"]))
    macro("HundredDElevenTenth", num(h["by_budget"]["0.001"]["median_flagged"]["D11"]))
    macro("HundredDTenHundredth", num(h["by_budget"]["0.0001"]["median_flagged"]["D10"]))
    t10 = next(
        c for c in bg["cross_cells"] if c["size"] == "8000" and c["cell"] == "round-robin 10"
    )
    f50c = next(c for c in bg["cross_cells"] if c["size"] == "8000" and c["cell"] == "search 50")
    macro("TenCellHoursEightK", num(t10["hours"], 1))
    macro("FiftyCellHoursEightK", num(f50c["hours"], 1))
    macro("TenCellJointEightK", num(t10["by_budget"]["0.01"]["joint_max"]))
    macro("FiftyCellJointEightK", num(f50c["by_budget"]["0.01"]["joint_max"]))
    for b, tag in (("0.001", "Tenth"), ("0.0001", "Hundredth")):
        # the scheduler spaces requests at an hour over (cap - 1), so one account needs N/(cap - 1) hours
        macro(f"HoursOneAccountBudget{tag}", num(2000 / (bg["thresholds"][b]["D1"] - 1), 1))

    # ---- items 5 and 6: D10 tail, timeline compounding, simultaneous creation
    ts = load(m7 / "tail_sim.json")
    tl = ts["d10_tail"]
    macro("DTenFlaggedAccountDays", intc(tl["n_flagged_account_days"]))
    macro("DTenFlaggedAccounts", intc(tl["n_flagged_accounts"]))
    macro("DTenTailSingleShare", pct(tl["share_single_request_single_session"]) + "\\%")
    macro("DTenAllSingleShare", pct(tl["share_single_request_single_session_all"]) + "\\%")
    macro("DTenTailMedianRequests", intc(tl["flagged_quantiles"]["requests"]["50"]))
    macro("DTenTailMedianStartHour", intc(tl["flagged_quantiles"]["start_hour"]["50"]))
    ta = ts["timeline_any"]
    macro("AnyDetTimelineSix", pct(ta["any_six"], 1) + "\\%")
    sim = ts["simultaneous_creation"]
    macro("SimCreationDEleven", num(sim["d11_median"]))
    macro("SimCreationDTen", num(sim["d10_median"]))
    macro("SimCreationDTenMax", num(sim["d10_max"]))

    # ---- item 7: out-of-corpus benign sample
    oc = load(m7 / "content_oasst.json")
    u = oc["campaigns"]["control:oasst"]
    bkey = [k for k in u if k.startswith("block")][0]
    for det in ("C1", "C2", "C2low", "C3", "B1", "B2"):
        macro(f"Oasst{_camel(det)}Block", frac_or_na(u[bkey][det]["flagged"]["0.01"]))
        macro(f"Oasst{_camel(det)}Account", frac_or_na(u["identity"][det]["flagged"]["0.01"]))
    orr = load(m7 / "r3batch_oasst.json")
    nr = load(EV / "m9" / "content_no_robots.json")["campaigns"]["control:no_robots"]
    nrk = [x for x in nr if x.startswith("block")][0]
    nrr = load(EV / "m9" / "r3batch_no_robots.json")["controls"]["no_robots"]
    orows2 = []
    for det in ("C1", "C2", "C2low", "C3", "B1", "B2"):
        orows2.append(
            f"{det} & {frac_or_na(u[bkey][det]['flagged']['0.01'])} & {frac_or_na(nr[nrk][det]['flagged']['0.01'])} \\\\"
        )
    orows2.append(
        f"Pooled design & {num(orr['controls']['oasst']['flagged']['fpr_0.01'])} ({orr['controls']['oasst']['median']:.2e}) & {num(nrr['flagged']['fpr_0.01'])} ({nrr['median']:.2e}) \\\\"
    )
    _table(
        "oasst.tex",
        "lcc",
        r"Statistic & Assistant conversations & Written instructions \\\\",
        orows2,
    )
    for det in ("C2low", "C3", "C2", "B1"):
        macro(f"NoRobots{_camel(det)}Block", frac_or_na(nr[nrk][det]["flagged"]["0.01"]))
    macro("NoRobotsCThreeAuc", num(nr[nrk]["C3"]["auc"]))
    macro("NoRobotsPooledFlagged", num(nrr["flagged"]["fpr_0.01"]))
    macro("NoRobotsPooledMedian", f"{nrr['median']:.2e}")
    macro("NoRobotsNPrompts", intc(nrr["n_prompts"]))
    macro("OasstPooledFlagged", num(orr["controls"]["oasst"]["flagged"]["fpr_0.01"]))
    macro("OasstPooledMedian", f"{orr['controls']['oasst']['median']:.2e}")
    macro("OasstNPrompts", intc(orr["controls"]["oasst"]["n_prompts"]))

    # ---- B9: recorded lever cells under recalibrated cadence thresholds
    cc = load(EV / "m8" / "cadence_cells.json")
    crows = []
    want = [
        ("round-robin 1, cap 26", "one account, cap"),
        ("round-robin 10, cap 26", "ten accounts, cap"),
        ("round-robin 100, cap none", "100 accounts, no re-timing"),
        ("round-robin 100, cap 26", "100 accounts, cap"),
        ("heterogeneous 100, stagger 6", "heterogeneous 100, stagger 6 h"),
        ("heterogeneous 1000, stagger 72", "heterogeneous 1,000, stagger 72 h"),
        ("search 50, stagger 6", "search 50, stagger 6 h"),
        ("search 100, stagger 6", "search 100, stagger 6 h"),
        ("unevaded single account", "unevaded single account"),
    ]
    by_cell = {c["cell"]: c for c in cc["cells"]}
    for key, label in want:
        s = by_cell[key]["summary"]
        f = lambda lab, k: frac_or_na(s[f"{lab}:{k}"]["flagged_median"])  # noqa: E731
        cv = s["own:3"]["cv_median"]
        crows.append(
            f"{label} & {num(by_cell[key]['hours'], 1)} & {'--' if cv is None else num(cv)} & {f('own', 3)} & {f('own', 5)} & {f('own', 10)} & {f('gap', 3)} & {f('gap', 5)} & {f('gap', 10)} \\\\"
        )
    _table(
        "cadence_cells.tex",
        "lrr" + "c" * 6,
        r"Cell & Hours & CV & \multicolumn{3}{c}{Own sessions: min.\ 3 / 5 / 10} & \multicolumn{3}{c}{Idle-gap sessions: min.\ 3 / 5 / 10} \\\\",
        crows,
    )
    for key, tag in (
        ("round-robin 1, cap 26", "One"),
        ("round-robin 10, cap 26", "Ten"),
        ("search 50, stagger 6", "Fifty"),
        ("search 100, stagger 6", "Hundred"),
    ):
        s = by_cell[key]["summary"]
        macro(f"CadenceMinTen{tag}", frac_or_na(s["own:10"]["flagged_median"]))
        macro(f"CadenceMinFive{tag}", frac_or_na(s["own:5"]["flagged_median"]))
        macro(f"CadenceCv{tag}", num(s["own:3"]["cv_median"]))
    macro("CadenceThrMinTen", num(cc["thresholds"]["10"], 3))
    macro("CadenceThrMinFive", num(cc["thresholds"]["5"], 3))
    n_paced = sum(
        1
        for c in cc["cells"]
        if c["source"] in ("price", "table7", "search")
        and c["summary"]["own:10"]["flagged_median"] is not None
        and "cap none" not in c["cell"]
    )
    n_paced_full = sum(
        1
        for c in cc["cells"]
        if c["source"] in ("price", "table7", "search")
        and c["summary"]["own:10"]["flagged_median"] == 1.0
        and "cap none" not in c["cell"]
    )
    macro("NPacedCells", intc(n_paced))
    macro("NPacedCellsCaught", intc(n_paced_full))

    # ---- B1 calibrated on the real accounts only (fifth review)
    b1 = load(EV / "m8" / "b1_real_only.json")
    macro("BOneNReal", intc(b1["n_real"]))
    macro("BOneThrReal", num(b1["threshold_real"], 3))
    macro("BOneRealisedFprReal", pct(b1["realised_fpr_real"], 1) + "\\%")
    macro("BOneNRealWithMembership", intc(b1["n_real_with_membership"]))
    macro(
        "BOneCBenchReal", num(b1["campaigns"]["pilot_baseline:block100"]["flagged_real_threshold"])
    )
    macro(
        "BOneSeedOneReal", num(b1["campaigns"]["c_real_v2_s1:identity"]["flagged_real_threshold"])
    )
    macro(
        "BOneControlReal",
        num(b1["campaigns"]["control:uniform_firstturns:block100"]["flagged_real_threshold"]),
    )
    # pooled design with all-turn pools (the run before first-turn matching), for the traced sentence
    r3a = load(EV / "m4" / "r3batch_ctrl.json")
    macro("PooledAllTurnHeldout", num(r3a["benign_heldout"]["flagged"]["fpr_0.01"]))
    macro("PooledAllTurnFirstTurns", num(r3a["benign_heldout_first_turns"]["flagged"]["fpr_0.01"]))
    macro("PooledAllTurnCReal", num(r3a["campaigns"]["c_real_v2"]["pure"]["flagged"]["fpr_0.01"]))

    # ---- B9 diagnostic: kernel terms of the per-account discrepancy
    kd = load(EV / "m8" / "kernel.json")
    for name, tag in (
        ("benign accounts", "Benign"),
        ("C-bench", "CBench"),
        ("C-real", "CReal"),
        ("C-instr", "CInstr"),
    ):
        macro(f"Kernel{tag}Within", num(kd["units"][name]["k_within"], 3))
        macro(f"Kernel{tag}Cross", num(kd["units"][name]["k_cross"], 3))
    macro("KernelPool", num(kd["k_pool_pool"], 3))

    # ---- item 2: overlay ×8, ×16 appended to the volume table
    orows = []
    for fname, fr in (("volume_overlay8.json", 8), ("volume_overlay16.json", 16)):
        ov = load(m7 / fname)
        vs = [v for v in ov["volume"] if v["f"] == float(fr)]
        med = lambda k: _median([x[k] for x in vs])  # noqa: E731
        medc = lambda n, k: _median([x["cells"][n][k] for x in vs])  # noqa: E731
        orows.append(
            f"$\\times${fr} & {intc(vs[0]['n_accounts'])} & {med('thr_d10'):.0f} & {med('thr_d11'):.0f} & {num(medc('10', 'd11_median'))} & {num(medc('10', 'p_any_d11'))} & {num(medc('100', 'd10_median'))} & {num(medc('100', 'd11_median'))} \\\\"
        )
        tag = _camel(f"x{fr}")
        macro(f"DElevenThr{tag}", f"{med('thr_d11'):.0f}")
        macro(f"DTenThr{tag}", f"{med('thr_d10'):.0f}")
        macro(f"HundredAccountDTen{tag}", num(medc("100", "d10_median")))
        macro(f"HundredAccountDEleven{tag}", num(medc("100", "d11_median")))
    body = (OUT_T / "volume_sensitivity.tex").read_text()
    body = body.replace("\\bottomrule", "\n".join(orows) + "\n\\bottomrule", 1)
    (OUT_T / "volume_sensitivity.tex").write_text(body)


def build_followup_tables() -> None:
    """Amendment B11: recalibrated cadence characterised; benign reference for the any-flag measure."""
    fu = load(EV / "m10" / "followup.json")
    cd = fu["cadence"]
    macro("CadTenNFlagged", intc(cd["n_flagged"]))
    macro("CadTenNFlaggedAccounts", intc(cd["n_flagged_accounts"]))
    macro("CadTenAlertsPerDay", num(cd["alerts_per_day"], 1))
    macro("CadTenHeldout", pct(cd["heldout_fpr_mean"], 2) + "\\%")
    macro("CadTenHeldoutMin", pct(cd["heldout_fpr_min"], 2) + "\\%")
    macro("CadTenHeldoutMax", pct(cd["heldout_fpr_max"], 2) + "\\%")
    macro("CadTenFlaggedMedianSize", intc(cd["flagged_session_size"]["50"]))
    macro("CadTenAllMedianSize", intc(cd["all_session_size"]["50"]))
    macro("CadTenFlaggedSingleTurn", num(cd["flagged_single_turn_share"]["50"]))
    macro("CadTenAllSingleTurn", num(cd["all_single_turn_share"]["50"]))
    br = fu["benign_reference"]
    macro("BenignAnyTen", num(br["groups"]["10"]["p_any"]))
    macro("BenignAnyFifty", num(br["groups"]["50"]["p_any"]))
    macro("BenignAnyHundred", num(br["groups"]["100"]["p_any"]))
    p53 = fu["p53"]
    macro("NSearchCellsCadence", intc(p53["n_cells"]))
    macro("NSearchCellsCadenceCaught", intc(p53["n_flagged_ge_0.9"]))
    macro("SearchMinShareSessionsScoreable", num(p53["min_share_sessions_scoreable"]))
    macro("SearchMinShareRequestsScoreable", num(p53["min_share_requests_in_scoreable"]))
    macro("NSearchUnderHalfScoreable", intc(p53["n_under_half_sessions_scoreable"]))

    def _cell(**kw):
        for c in fu["cells"]:
            if all(c.get(k) == v for k, v in kw.items()):
                return c
        raise KeyError(kw)

    c50 = _cell(source="search", n=50, count_cap=26, session_mult=10.0, stagger_h=6)
    macro("CadFiftyShareSessions", num(c50["share_sessions_scoreable"]))
    macro("CadFiftyShareRequests", num(c50["share_requests_in_scoreable"]))
    h100 = _cell(source="table7", n=100, stagger_h=6)
    macro("CadHetShareSessions", num(h100["share_sessions_scoreable"]))
    macro("CadHetShareRequests", num(h100["share_requests_in_scoreable"]))
    macro(
        "NSearchRequestsUnderHalf",
        intc(
            sum(
                1
                for c in fu["cells"]
                if c["source"] == "search" and c["share_requests_in_scoreable"] < 0.5
            )
        ),
    )
    rows = []
    f3 = lambda v: "n/a" if v is None else num(v)  # noqa: E731
    for c in fu["cells"]:
        if c["source"] == "price":
            lab, par = "rate cap", f"cap {c['cap']}"
        elif c["source"] == "table7":
            lab, par = "heterogeneous", f"stagger {c['stagger_h']} h"
        else:
            lab, par = "search", f"stagger {c['stagger_h']} h"
        rows.append(
            f"{lab} & {intc(c['n'])} & {par} & {f3(c['flagged'])} & {f3(c['share_sessions_scoreable'])} & {f3(c['share_requests_in_scoreable'])} \\\\"
        )
    _table(
        "cadence_all_cells.tex",
        "lrlccc",
        r"Cell & Accounts & Setting & Flagged & Sessions scoreable & Requests in scoreable sessions \\",
        rows,
    )
    rc = load(EV / "m7" / "recalibrate.json")
    trows = []
    for det in ("D4", "D5", "D6", "D7", "D8", "D8b"):
        r0, r1 = rc["registered"][det], rc["no_constructed"][det]
        mx = max(v["flagged"] for v in r1["campaigns"].values())
        trows.append(
            f"{det} & {r0['threshold']:.3g} & {intc(r0['n_benign'])} & {r1['threshold']:.3g} & {intc(r1['n_benign'])} & {num(mx)} \\\\"
        )
    _table(
        "no_constructed.tex",
        "lrrrrc",
        r"Detector & Registered thr. & Units & Without constructed thr. & Units & Largest campaign flagged \\",
        trows,
    )


def build_api_baseline() -> None:
    """Amendment B12: second benign baseline from public production API traffic."""
    ab = load(EV / "m11" / "api_baseline.json")
    pl = ab["language_pooled"]
    macro("ApiNClients", intc(pl["n_clients"]))
    macro("ApiNClientDays", intc(pl["n_client_days"]))
    macro("ApiNWindows", intc(pl["n_active_windows"]))
    macro("ApiBusiestHourMedian", intc(round(pl["client_max_hourly"]["50"], -2)))
    macro("ApiBusiestHourPTen", intc(round(pl["client_max_hourly"]["10"], -1)))
    macro("ApiShareOverChatThr", pct(pl["share_clients_over_chat_threshold"], 1) + "\\%")
    macro("ApiRateThrMillions", num(pl["client_day_threshold_1pct"] / 1e6, 2))
    macro("ApiRateThrExceed", intc(pl["client_day_n_exceed"]))
    macro("ApiCvMedian", num(pl["cv_quantiles"]["50"]))
    macro("ApiCvPFive", num(pl["cv_quantiles"]["5"]))
    macro("ApiCadenceThr", num(pl["cadence_threshold_1pct_low"], 3))
    macro("ApiShareBelowChatCadence", pct(pl["share_windows_below_chat_cadence"], 2) + "\\%")
    macro("ApiShareBelowLeverCadence", pct(pl["share_windows_below_lever_cadence"], 2) + "\\%")
    macro(
        "ApiClientsMedianBelowChat", pct(pl["share_clients_median_below_chat_cadence"], 2) + "\\%"
    )
    rows = []
    names = {
        "m-large": "language, large",
        "m-mid": "language, mid",
        "m-small": "language, small",
        "deepseek-r1": "reasoning",
    }
    for name, s in ab["sets"].items():
        c, v = s["client_max_hourly"], s["cv_quantiles"]
        rows.append(
            f"{names[name]} & {intc(s['n_clients'])} & {intc(s['n_client_days'])} & {intc(round(c['50'], -2))} & {intc(round(c['90'], -2))} & "
            f"{pct(s['share_clients_over_chat_threshold'])}\\% & {num(v['1'])} & {num(v['5'])} & {num(v['50'])} & "
            f"{pct(s['share_windows_below_chat_cadence'], 1)}\\% & {pct(s['share_windows_below_lever_cadence'], 1)}\\% \\\\"
        )
    c, v = pl["client_max_hourly"], pl["cv_quantiles"]
    rows.append(
        f"language, pooled & {intc(pl['n_clients'])} & {intc(pl['n_client_days'])} & {intc(round(c['50'], -2))} & {intc(round(c['90'], -2))} & "
        f"{pct(pl['share_clients_over_chat_threshold'])}\\% & {num(v['1'])} & {num(v['5'])} & {num(v['50'])} & "
        f"{pct(pl['share_windows_below_chat_cadence'], 1)}\\% & {pct(pl['share_windows_below_lever_cadence'], 1)}\\% \\\\"
    )
    _table(
        "api_baseline.tex",
        "lrrrrrccccc",
        r"Clients & $n$ & Client-days & \multicolumn{2}{c}{Busiest hour: median, 90th} & Over chat thr. & \multicolumn{3}{c}{Cadence CV: 1st, 5th, median} & Below 0.305 & Below 0.20 \\",
        rows,
    )


_WORDS = {
    "0": "Zero",
    "1": "One",
    "2": "Two",
    "3": "Three",
    "4": "Four",
    "5": "Five",
    "6": "Six",
    "7": "Seven",
    "8": "Eight",
    "9": "Nine",
}


def _camel(s: str) -> str:
    """Letters-only CamelCase: digits become words (D8b -> DEightB, C2low -> CTwoLow)."""
    out = []
    for w in re.split(r"[^A-Za-z0-9]+", s):
        if not w:
            continue
        piece, up = "", True
        for ch in w:
            if ch.isdigit():
                piece += _WORDS[ch]
                up = True
            else:
                piece += ch.upper() if up else ch
                up = False
        out.append(piece)
    return "".join(out)


def _table(name: str, spec: str, header: str, rows: list[str]) -> None:
    if not rows:
        raise ValueError(f"table {name} has no rows")
    body = "\n".join(rows)
    (OUT_T / name).write_text(
        f"\\begin{{tabular}}{{{spec}}}\n\\toprule\n{header}\n\\midrule\n{body}\n\\bottomrule\n\\end{{tabular}}\n"
    )


if __name__ == "__main__":
    sys.exit(main())
