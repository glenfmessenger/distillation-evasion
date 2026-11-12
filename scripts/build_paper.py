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
    ("student_base_chat_s0", "Student, untouched (chat mode)", "BaseChat"),
    ("student_after_sft_s0", "Student after SFT on copied pairs", "AfterSft"),
    ("student_after_repair_s0", "Copy, then repair", "AfterRepair"),
    ("student_repair_only_s0", "Repair only, no copy", "RepairOnly"),
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
        r"Requests & Identities & Cap/h & Hours & D1 & D2 \\",
        price_rows,
    )
    macro("NReschedulings", intc(len(load(CAMPAIGNS[0][2])["cells"][0]["per_seed"])))

    # ---- content breadth table
    variants = [
        ("Replay calibration, bge-small, n=30, block 100", "content_s1.json"),
        ("Heavy-user calibration", "content_heavy.json"),
        ("bge-base encoder", "content_bgebase.json"),
        ("Matched n = 10", "content_nm10.json"),
        ("Matched n = 100 (heavy)", "content_nm100_heavy.json"),
        ("Block 50", "content_b50.json"),
        ("Block 500", "content_b500.json"),
    ]
    breadth_rows = []
    for text, fn in variants:
        d = load(EV / "m4" / fn)
        blockkey = [k for k in d["campaigns"]["c_real_v2:20"] if k.startswith("block")][0]
        cells = []
        for ckey in ("pilot_baseline", "c_real_v2:20"):
            r = d["campaigns"][ckey][blockkey]
            cells += [frac_or_na(r[det]["flagged"]["0.01"]) for det in ("C2", "C2low", "C3", "B1")]
        breadth_rows.append(f"{text} & {intc(d['n_benign_units'])} & " + " & ".join(cells) + r" \\")
    _table(
        "content_breadth.tex",
        "lr" + "c" * 8,
        r"Variant & Benign units & \multicolumn{4}{c}{C-bench blocks} & \multicolumn{4}{c}{C-real blocks} \\ & & C2 & C2low & C3 & B1 & C2 & C2low & C3 & B1 \\",
        breadth_rows,
    )
    heavy = load(EV / "m4" / "content_heavy.json")
    macro("NHeavyUsers", intc(heavy["n_benign_units"]))

    # ---- pooled design (R3) table
    r3 = load(EV / "m4" / "r3batch_firstturn_ctrl.json")
    macro("PooledBatch", intc(r3["batch"]))
    macro("PooledNullDraws", intc(r3["null_samples"]))
    pooled_rows = [
        f"Benign held-out (heavy users) & {r3['benign_heldout']['median']:.2e} & {num(r3['benign_heldout']['flagged']['fpr_0.01'])} \\\\",
        f"Benign held-out, first turns only & {r3['benign_heldout_first_turns']['median']:.2e} & {num(r3['benign_heldout_first_turns']['flagged']['fpr_0.01'])} \\\\",
        f"Benign conversation-uniform first turns (control) & {r3['controls']['uniform_firstturns']['median']:.2e} & {num(r3['controls']['uniform_firstturns']['flagged']['fpr_0.01'])} \\\\",
    ]
    for ckey, text in (
        ("pilot_baseline", "C-bench, pure window"),
        ("c_real_v2", "C-real, pure window"),
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
        (share, "c_real_v2", "C-real, seed 0"),
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
        ("organisation", "Organisation, real users, staggered births"),
        ("batch_job", "Batch job, 50 keys born together"),
        ("eval_fleet", "Evaluation fleet, 20 keys born together"),
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
        r">{\raggedright\arraybackslash}p{2.6cm}rcc",
        r"Population & Identities & D10 flagged at 1\% & D11 flagged at 1\% \\",
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

    OUT_M.write_text("".join(f"\\newcommand{{\\{k}}}{{{v}}}\n" for k, v in sorted(macros.items())))
    print(f"{len(macros)} macros, {len(list(OUT_T.glob('*.tex')))} tables")
    return 0


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
