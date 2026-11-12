"""Query pool and capability suites (PROTOCOL §2, §3; decisions 7 and 13).

Every loader names its dataset, revision, config and split explicitly and raises if the split is
missing, smaller than expected, or lacks a required column. Nothing is substituted.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

from datasets import load_dataset

MATH_CONFIGS = (
    "algebra",
    "counting_and_probability",
    "geometry",
    "intermediate_algebra",
    "number_theory",
    "prealgebra",
    "precalculus",
)
EXPECTED_MIN = {
    "math_train": 7000,
    "gsm8k_train": 7000,
    "apps_train": 4500,
    "mbpp_pool": 450,
    "math500": 500,
    "gsm8k_test": 1319,
    "humaneval": 164,
    "mbpp_test": 500,
}


class LoaderError(RuntimeError):
    pass


@dataclass(frozen=True)
class Item:
    id: str
    source: str  # dataset name
    domain: str  # "math" | "code"
    prompt: str  # the problem text as the user would pose it
    verifier: str  # "math_boxed" | "gsm8k_numeric" | "humaneval" | "mbpp_asserts" | "apps_io"
    payload: dict  # verifier-specific gold data


def _check(rows, key: str, cols: Iterable[str]) -> None:
    n = len(rows)
    if n < EXPECTED_MIN[key]:
        raise LoaderError(f"{key}: got {n} rows, expected >= {EXPECTED_MIN[key]}")
    missing = [c for c in cols if c not in rows.column_names]
    if missing:
        raise LoaderError(f"{key}: missing columns {missing}")


def _boxed(s: str) -> str | None:
    """Last \\boxed{...} content with balanced braces, or None."""
    i = s.rfind("\\boxed")
    if i < 0:
        return None
    j = s.find("{", i)
    if j < 0:
        return None
    depth, k = 0, j
    while k < len(s):
        if s[k] == "{":
            depth += 1
        elif s[k] == "}":
            depth -= 1
            if depth == 0:
                return s[j + 1 : k]
        k += 1
    return None


# ---------- pool sources ----------


def load_math_train() -> list[Item]:
    items = []
    for cfg in MATH_CONFIGS:
        ds = load_dataset("EleutherAI/hendrycks_math", cfg, split="train")
        for i, r in enumerate(ds):
            gold = _boxed(r["solution"])
            if gold is None:
                continue
            items.append(
                Item(
                    f"math_train:{cfg}:{i}",
                    "EleutherAI/hendrycks_math",
                    "math",
                    r["problem"],
                    "math_boxed",
                    {"answer": gold, "level": r["level"]},
                )
            )
    if len(items) < EXPECTED_MIN["math_train"]:
        raise LoaderError(f"math_train: only {len(items)} items with a boxed answer")
    return items


def load_gsm8k(split: str) -> list[Item]:
    ds = load_dataset("openai/gsm8k", "main", split=split)
    _check(ds, f"gsm8k_{split}", ["question", "answer"])
    out = []
    for i, r in enumerate(ds):
        if "####" not in r["answer"]:
            raise LoaderError(f"gsm8k_{split}:{i} has no '####' answer marker")
        gold = r["answer"].split("####")[-1].strip().replace(",", "")
        out.append(
            Item(
                f"gsm8k_{split}:{i}",
                "openai/gsm8k",
                "math",
                r["question"],
                "gsm8k_numeric",
                {"answer": gold, "solution": r["answer"]},
            )
        )
    return out


def load_apps_train() -> list[Item]:
    import sys

    sys.set_int_max_str_digits(
        0
    )  # APPS test payloads carry integers beyond the 4,300-digit default
    ds = load_dataset("codeparrot/apps", "default", split="train", revision="refs/convert/parquet")
    _check(ds, "apps_train", ["problem_id", "question", "input_output", "difficulty"])
    out, n_unparsable = [], 0
    for r in ds:
        if not r["input_output"]:
            continue
        try:
            io = json.loads(r["input_output"])
        except ValueError:
            n_unparsable += 1
            continue
        if not io.get("inputs") or not io.get("outputs"):
            continue
        if r.get("starter_code"):
            continue  # function-call style; the stdin/stdout verifier covers only standard IO
        out.append(
            Item(
                f"apps_train:{r['problem_id']}",
                "codeparrot/apps",
                "code",
                r["question"],
                "apps_io",
                {
                    "inputs": io["inputs"][:10],
                    "outputs": io["outputs"][:10],
                    "difficulty": r["difficulty"],
                },
            )
        )
    if n_unparsable > 0.05 * len(ds):
        raise LoaderError(f"apps_train: {n_unparsable} unparsable input_output payloads")
    if len(out) < 3000:
        raise LoaderError(f"apps_train: only {len(out)} standard-IO items with tests")
    return out


def load_mbpp(splits: tuple[str, ...]) -> list[Item]:
    out = []
    for sp in splits:
        ds = load_dataset("google-research-datasets/mbpp", "full", split=sp)
        for r in ds:
            out.append(
                Item(
                    f"mbpp_{sp}:{r['task_id']}",
                    "google-research-datasets/mbpp",
                    "code",
                    r["text"],
                    "mbpp_asserts",
                    {
                        "tests": r["test_list"],
                        "setup": r.get("test_setup_code", "") or "",
                        "canonical": r["code"],
                    },
                )
            )
    return out


# ---------- suites ----------


def load_math500() -> list[Item]:
    ds = load_dataset("HuggingFaceH4/MATH-500", split="test")
    _check(ds, "math500", ["problem", "answer"])
    return [
        Item(
            f"math500:{r['unique_id']}",
            "HuggingFaceH4/MATH-500",
            "math",
            r["problem"],
            "math_boxed",
            {"answer": r["answer"], "level": r["level"]},
        )
        for r in ds
    ]


def load_humaneval() -> list[Item]:
    ds = load_dataset("openai/openai_humaneval", split="test")
    _check(ds, "humaneval", ["prompt", "test", "entry_point"])
    return [
        Item(
            f"humaneval:{r['task_id']}",
            "openai/openai_humaneval",
            "code",
            r["prompt"],
            "humaneval",
            {"test": r["test"], "entry_point": r["entry_point"]},
        )
        for r in ds
    ]


def suites() -> dict[str, list[Item]]:
    s = {
        "math500": load_math500(),
        "gsm8k_test": load_gsm8k("test"),
        "humaneval": load_humaneval(),
        "mbpp_test": load_mbpp(("test",)),
    }
    for k, v in s.items():
        if len(v) < EXPECTED_MIN[k]:
            raise LoaderError(f"suite {k}: {len(v)} items < {EXPECTED_MIN[k]}")
    return s


def pool_sources() -> dict[str, list[Item]]:
    p = {
        "math_train": load_math_train(),
        "gsm8k_train": load_gsm8k("train"),
        "apps_train": load_apps_train(),
        "mbpp_pool": load_mbpp(("train", "validation")),
    }
    if len(p["mbpp_pool"]) < EXPECTED_MIN["mbpp_pool"]:
        raise LoaderError(f"mbpp_pool: {len(p['mbpp_pool'])} items")
    return p


# ---------- contamination ----------

_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^\w\s]")


def normalise(s: str) -> str:
    return _WS.sub(" ", _PUNCT.sub(" ", s.lower())).strip()


def ngrams(s: str, n: int = 13) -> set[tuple[str, ...]]:
    w = normalise(s).split()
    return {tuple(w[i : i + n]) for i in range(len(w) - n + 1)}


def contamination(pool: dict[str, list[Item]], suite: dict[str, list[Item]], n: int = 13):
    """Return (clean_pool, report). A pool item is removed if its normalised prompt exactly equals
    any suite prompt or shares any n-gram with any suite prompt."""
    exact: dict[str, str] = {}
    grams: dict[tuple, str] = {}
    for sname, items in suite.items():
        for it in items:
            exact[normalise(it.prompt)] = sname
            for g in ngrams(it.prompt, n):
                grams[g] = sname
    report = {"n": n, "exact_hits": {}, "ngram_hits": {}, "removed": {}, "kept": {}}
    clean: dict[str, list[Item]] = {}
    for pname, items in pool.items():
        kept = []
        for it in items:
            key = normalise(it.prompt)
            hit = None
            if key in exact:
                hit = ("exact", exact[key])
            else:
                for g in ngrams(it.prompt, n):
                    if g in grams:
                        hit = ("ngram", grams[g])
                        break
            if hit is None:
                kept.append(it)
            else:
                kind, sname = hit
                d = report["exact_hits" if kind == "exact" else "ngram_hits"]
                d.setdefault(pname, {}).setdefault(sname, 0)
                d[pname][sname] += 1
        report["removed"][pname] = len(items) - len(kept)
        report["kept"][pname] = len(kept)
        clean[pname] = kept
    return clean, report


def write_jsonl(items: Iterable[Item], path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    with path.open("w") as fh:
        for it in items:
            line = json.dumps(asdict(it), ensure_ascii=False) + "\n"
            fh.write(line)
            h.update(line.encode())
    return h.hexdigest()


def read_jsonl(path: Path) -> list[Item]:
    out = []
    with Path(path).open() as fh:
        for n, line in enumerate(fh, 1):
            try:
                out.append(Item(**json.loads(line)))
            except Exception as e:  # noqa: BLE001
                raise LoaderError(f"{path}:{n}: malformed item: {e}") from e
    if not out:
        raise LoaderError(f"{path}: empty")
    return out
