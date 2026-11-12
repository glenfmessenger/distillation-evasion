"""Verifiers for suite items and RL rewards. Code runs in a subprocess with CPU/memory limits and
a timeout, in a temp dir. This is a throwaway VM, not a security sandbox (TtV)."""

from __future__ import annotations

import json
import os
import queue
import re
import resource
import select
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from dev_harness.pool import _boxed

CODE_BLOCK = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.S)
LAST_NUMBER = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def extract_code(text: str) -> str:
    blocks = CODE_BLOCK.findall(text)
    return blocks[-1] if blocks else text


def _limits(mem_mb: int = 2048, cpu_s: int = 10):
    def pre():
        if (
            sys.platform == "linux"
        ):  # RLIMIT_AS is not honoured usefully on macOS (dev machines only)
            resource.setrlimit(resource.RLIMIT_AS, (mem_mb << 20, mem_mb << 20))
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_s, cpu_s))
        os.setsid()

    return pre


def run_python(code: str, stdin: str = "", timeout: float = 10.0) -> tuple[int | None, str, str]:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "prog.py"
        p.write_text(code)
        try:
            r = subprocess.run(
                [sys.executable, "-I", str(p)],
                input=stdin,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=d,
                preexec_fn=_limits(),
            )
            return r.returncode, r.stdout, r.stderr
        except subprocess.TimeoutExpired:
            return None, "", "timeout"


class VerifyTimeout(RuntimeError):
    """Symbolic verification exceeded its time budget; the caller records an error, never a 0."""


MATH_WORKERS = 4
MATH_MEM_MB = 8192


class _MathWorker:
    """A killable math-verify process (dev_harness.math_worker). F38: a thread cannot be timed
    out while it holds the interpreter lock inside one big-integer operation; a process can."""

    def __init__(self) -> None:
        def pre():
            if sys.platform == "linux":
                resource.setrlimit(resource.RLIMIT_AS, (MATH_MEM_MB << 20, MATH_MEM_MB << 20))

        self.p = subprocess.Popen(
            [sys.executable, "-m", "dev_harness.math_worker"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            preexec_fn=pre,
        )

    def call(self, req: dict, timeout_s: float) -> dict | None:
        """The worker's reply, or None if it died or ran out of time (it is killed either way)."""
        try:
            self.p.stdin.write((json.dumps(req) + "\n").encode())
            self.p.stdin.flush()
        except (BrokenPipeError, OSError):
            self.kill()
            return None
        ready, _, _ = select.select([self.p.stdout], [], [], timeout_s)
        line = self.p.stdout.readline() if ready else b""
        if not line:
            self.kill()
            return None
        return json.loads(line)

    def kill(self) -> None:
        self.p.kill()
        self.p.wait()

    def alive(self) -> bool:
        return self.p.poll() is None


_MATH_IDLE: queue.LifoQueue = queue.LifoQueue()
_MATH_SLOTS = threading.BoundedSemaphore(MATH_WORKERS)


def verify_math_boxed(pred_text: str, gold: str, timeout_s: float = 20.0) -> bool:
    req = {"gold": gold, "pred_text": pred_text[-2000:], "boxed": _boxed(pred_text)}
    with _MATH_SLOTS:
        try:
            w = _MATH_IDLE.get_nowait()
        except queue.Empty:
            w = _MathWorker()
        rep = w.call(req, timeout_s)
        if w.alive():
            _MATH_IDLE.put(w)
    if rep is None or "budget" in rep:
        raise VerifyTimeout(
            f"math verification exceeded its budget ({timeout_s}s / {MATH_MEM_MB} MB) "
            f"for gold={gold!r}"
        )
    if "err" in rep:
        raise RuntimeError(f"math verification failed for gold={gold!r}: {rep['err']}")
    return rep["ok"]


def verify_gsm8k(pred_text: str, gold: str) -> bool:
    pb = _boxed(pred_text)
    cand = pb if pb is not None else (LAST_NUMBER.findall(pred_text) or [None])[-1]
    if cand is None:
        return False
    try:
        return abs(float(cand.replace(",", "")) - float(gold)) < 1e-6
    except ValueError:
        return False


def verify_humaneval(
    pred_text: str, prompt: str, test: str, entry_point: str, completion_mode: bool
) -> bool:
    body = pred_text if completion_mode else extract_code(pred_text)
    code = (prompt + body) if completion_mode else body
    prog = f"{code}\n\n{test}\n\ncheck({entry_point})\n"
    rc, _, _ = run_python(prog)
    return rc == 0


def verify_mbpp(pred_text: str, tests: list[str], setup: str) -> bool:
    code = extract_code(pred_text)
    prog = f"{setup}\n{code}\n\n" + "\n".join(tests) + "\n"
    rc, _, _ = run_python(prog)
    return rc == 0


def verify_apps(pred_text: str, inputs: list[str], outputs: list[str]) -> bool:
    code = extract_code(pred_text)
    for i, o in zip(inputs, outputs):
        rc, out, _ = run_python(code, stdin=i if isinstance(i, str) else "\n".join(i))
        if rc != 0:
            return False
        exp = o if isinstance(o, str) else "\n".join(o)
        if out.strip().split() != exp.strip().split():
            return False
    return True


def answer_text(text: str, reasoning: str | None) -> tuple[str, bool]:
    """The text a verdict is taken from under amendment A7 (decision 34): the answer field, or,
    when it is empty because the model never closed its think span (the whole output then sits in
    the reasoning field), the reasoning field. Returns (text, used_reasoning)."""
    if not text.strip() and (reasoning or "").strip():
        return reasoning, True
    return text, False


def creditable(text: str, finish: str | None) -> bool:
    """Amendment A8: a sample cut off at the length cap is creditable only if it carries a boxed
    answer; trailing text of a truncated trace must not be mined for a gold number (F65)."""
    return finish != "length" or _boxed(text) is not None


def verify_item(
    verifier: str, payload: dict, pred_text: str, prompt: str, completion_mode: bool
) -> bool:
    if verifier == "math_boxed":
        return verify_math_boxed(pred_text, payload["answer"])
    if verifier == "gsm8k_numeric":
        return verify_gsm8k(pred_text, payload["answer"])
    if verifier == "humaneval":
        return verify_humaneval(
            pred_text, prompt, payload["test"], payload["entry_point"], completion_mode
        )
    if verifier == "mbpp_asserts":
        return verify_mbpp(pred_text, payload["tests"], payload.get("setup", ""))
    if verifier == "apps_io":
        return verify_apps(pred_text, payload["inputs"], payload["outputs"])
    raise ValueError(f"unknown verifier {verifier!r}")


def reward(verifier: str, payload_json: str, pred_text: str, prompt: str) -> float:
    return 1.0 if verify_item(verifier, json.loads(payload_json), pred_text, prompt, False) else 0.0
