"""Selection and layout of SFT examples from campaign pairs. Pure Python (no torch) so the
selection rules are testable without a GPU. Every filter is a named, counted switch."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def load_pairs(path: Path, limit: int = 0, max_gen_tokens: int = 0):
    """Usable pairs, counts of everything left out, and the sha256 of the lines used.

    Left out and counted: error rows; repeats of an id (a resumed run may re-issue a pair, the
    first is kept); finish_reason != stop; and, only when max_gen_tokens > 0 (amendment A5),
    pairs whose server-reported generated_tokens exceed it."""
    rows, seen = [], set()
    counts = {"errors": 0, "dropped_finish_length": 0, "dropped_over_max_gen": 0}
    h = hashlib.sha256()
    with Path(path).open() as fh:
        for line in fh:
            d = json.loads(line)
            if "error" in d:
                counts["errors"] += 1
                continue
            if d["id"] in seen:
                continue
            seen.add(d["id"])
            if d["finish"] != "stop":
                counts["dropped_finish_length"] += 1
                continue
            if max_gen_tokens and d["generated_tokens"] > max_gen_tokens:
                counts["dropped_over_max_gen"] += 1
                continue
            rows.append(d)
            h.update(line.encode())
    if not rows:
        raise RuntimeError(f"{path}: no usable pairs")
    if limit:
        rows = rows[:limit]
    return rows, counts, h.hexdigest()


def assistant_parts(d: dict) -> tuple[str, str]:
    """(think block, final answer) of the assistant turn: '<think>\\n...\\n</think>\\n\\n', answer."""
    reasoning = (d.get("reasoning") or "").strip()
    return f"<think>\n{reasoning}\n</think>\n\n", d["content"].strip()


def examples_for(prompt: str, d: dict, eos: str, answer_only_copy: bool) -> list[dict]:
    """Prompt/completion examples for one pair; loss is taken on the completion only.

    The first example is the full assistant turn. With answer_only_copy (amendment A5 variant b)
    a second example moves the think block into the prompt, so its loss covers the answer alone."""
    think, answer = assistant_parts(d)
    out = [{"prompt": prompt, "completion": think + answer + eos}]
    if answer_only_copy:
        out.append({"prompt": prompt + think, "completion": answer + eos})
    return out
