#!/usr/bin/env python
"""Canonical scoring: re-derive every verdict from the stored raw text with the CURRENT verifier.

score_suite.py's inline verdicts are provisional (the verifier can change; F25). This script reads
$HARNESS_HOST_REPO/results/raw/scores/<label>/<suite>.jsonl, re-verifies each sample, and writes
summary_rescored.json with pass@1 (BCa CI), truncation and error counts, the verifier's git
commit, and the number of verdicts that changed versus the stored flags. Error rows (no text) stay
excluded and are counted. Usage: rescore.py [--registered-path] <label> [<label> ...]

Scoring rule (amendment A7, decision 34): dev_harness.verify.answer_text, i.e. the answer field,
or the whole output when the think span never closed. The count of samples that needed the
second branch is reported per suite. --registered-path reproduces v1.0's rule (answer field
only) into summary_rescored_registered.json, for the one-time side-by-side table.
"""

from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dev_harness.paths import host_repo
from dev_harness.pool import read_jsonl
from dev_harness.stats import mean_bca_ci
from dev_harness.verify import VerifyTimeout, answer_text, creditable, verify_item

SUITES = ("math500", "gsm8k_test", "humaneval", "mbpp_test")


def main(argv: list[str]) -> int:
    registered = "--registered-path" in argv
    a8 = "--a8" in argv
    labels = [a for a in argv if a not in ("--registered-path", "--a8")]
    if not labels:
        raise SystemExit("usage: rescore.py [--registered-path] <label> [<label> ...]")
    root = host_repo()
    commit = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[1],
    ).stdout.strip()
    for label in labels:
        d = root / "results" / "raw" / "scores" / label
        stored = (
            json.loads((d / "summary.json").read_text()) if (d / "summary.json").exists() else {}
        )
        mode = stored.get("mode")
        if mode not in ("chat", "completion"):
            raise RuntimeError(f"{label}: summary.json has no mode; cannot rescore")
        out = {"label": label, "mode": mode, "verifier_commit": commit, "suites": {}}
        for suite in SUITES:
            f = d / f"{suite}.jsonl"
            if not f.exists():
                continue
            items = {it.id: it for it in read_jsonl(root / "pool" / "suites" / f"{suite}.jsonl")}
            rows = [json.loads(line) for line in f.read_text().splitlines() if line.strip()]
            samples = [r for r in rows if "ok" in r]
            n_err = sum("error" in r for r in rows)

            def eff_text(r):
                if registered:
                    return r["text"]
                return answer_text(r["text"], r.get("reasoning"))[0]

            n_fallback = sum(
                0 if registered else answer_text(r["text"], r.get("reasoning"))[1] for r in samples
            )

            def rv(r):
                it = items[r["id"]]
                if a8 and not creditable(eff_text(r), r.get("finish")):
                    return False
                try:
                    return verify_item(
                        it.verifier, it.payload, eff_text(r), it.prompt, mode == "completion"
                    )
                except VerifyTimeout:
                    return None

            with ThreadPoolExecutor(max_workers=16) as ex:
                verdicts = list(ex.map(rv, samples))
            per_item: dict[str, list[int]] = {}
            changed = timeouts = 0
            for r, v in zip(samples, verdicts):
                if v is None:
                    timeouts += 1
                    continue
                changed += int(v != bool(r["ok"]))
                per_item.setdefault(r["id"], []).append(int(v))
            scored = [sum(v) / len(v) for v in per_item.values()]
            ci = mean_bca_ci(scored, seed=0)
            out["suites"][suite] = {
                "pass_at_1": ci,
                "n_items": len(items),
                "n_items_scored": len(scored),
                "n_samples": len(samples),
                "n_finish_length": sum(r.get("finish") == "length" for r in samples),
                "n_errors": n_err,
                "n_verify_timeouts": timeouts,
                "n_verdicts_changed_vs_stored": changed,
                "scoring_rule": "registered_v1" if registered else ("A8" if a8 else "A7"),
                "n_samples_scored_from_reasoning": n_fallback,
                "complete": len(scored) == len(items)
                and all(len(v) == stored.get("k", 4) for v in per_item.values()),
            }
            s = out["suites"][suite]
            print(
                f"{label} {suite}: pass@1={ci['mean']:.4f} [{ci['lo']:.4f},{ci['hi']:.4f}] items={len(scored)}/{len(items)} "
                f"len={s['n_finish_length']} err={n_err} changed={changed} complete={s['complete']}"
                + ("" if registered else f" from_reasoning={n_fallback}")
            )
        name = (
            "summary_rescored_registered.json"
            if registered
            else ("summary_rescored_a8.json" if a8 else "summary_rescored.json")
        )
        (d / name).write_text(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
