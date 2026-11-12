"""Prompt formats for scoring and for the campaign (recorded here so they are versioned).

chat mode: instruction-tuned / distilled students and the teacher (thinking on by default).
completion mode: the base student before any training (few-shot, stop sequences).
"""

from __future__ import annotations

from dev_harness.pool import Item

MATH_INSTR = "Please reason step by step, and put your final answer within \\boxed{}."
CODE_INSTR = (
    "Write a correct, complete Python solution. Return the final code in a single "
    "```python code block."
)
APPS_INSTR = (
    "Write a complete Python program that reads from standard input and writes to "
    "standard output. Return the final program in a single ```python code block."
)


def chat_messages(it: Item) -> list[dict[str, str]]:
    if it.verifier in ("math_boxed", "gsm8k_numeric"):
        return [{"role": "user", "content": f"{it.prompt}\n\n{MATH_INSTR}"}]
    if it.verifier == "humaneval":
        return [
            {
                "role": "user",
                "content": f"Complete the following Python function.\n\n```python\n{it.prompt}\n```\n\n{CODE_INSTR}",
            }
        ]
    if it.verifier == "mbpp_asserts":
        tests = "\n".join(it.payload["tests"])
        return [
            {
                "role": "user",
                "content": f"{it.prompt}\nYour code should pass these tests:\n```python\n{tests}\n```\n\n{CODE_INSTR}",
            }
        ]
    if it.verifier == "apps_io":
        return [{"role": "user", "content": f"{it.prompt}\n\n{APPS_INSTR}"}]
    raise ValueError(it.verifier)


# ---- completion mode (base model) ----


def completion_prompt(it: Item, shots: list[Item]) -> tuple[str, list[str], int]:
    """Returns (prompt, stop sequences, max_tokens)."""
    if it.verifier == "math_boxed":
        pre = "".join(
            f"Problem:\n{s.prompt}\nSolution:\n{s.payload['solution']}\n\n" for s in shots
        )
        return pre + f"Problem:\n{it.prompt}\nSolution:\n", ["\n\nProblem:"], 1024
    if it.verifier == "gsm8k_numeric":
        pre = "".join(f"Question: {s.prompt}\nAnswer: {s.payload['solution']}\n\n" for s in shots)
        return pre + f"Question: {it.prompt}\nAnswer:", ["\n\nQuestion:"], 512
    if it.verifier == "humaneval":
        return (
            it.prompt,
            ["\ndef ", "\nclass ", "\nif __name__", "\nprint("],
            512,
        )  # vLLM allows <= 4 stops
    if it.verifier == "mbpp_asserts":
        pre = "".join(
            f"You are an expert Python programmer, and here is your task: {s.prompt} Your code should pass these tests:\n\n"
            + "\n".join(s.payload["tests"])
            + f"\n[BEGIN]\n{s.payload['canonical']}\n[DONE]\n"
            for s in shots
        )
        tests = "\n".join(it.payload["tests"])
        return (
            pre
            + f"You are an expert Python programmer, and here is your task: {it.prompt} Your code should pass these tests:\n\n{tests}\n[BEGIN]\n",
            ["[DONE]"],
            512,
        )
    raise ValueError(it.verifier)
