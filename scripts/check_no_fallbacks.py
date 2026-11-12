#!/usr/bin/env python
"""Pre-commit hook: harness code must not contain silent-fallback patterns (charter 7,
global rule 4). Any loader that could substitute synthetic or default data must raise.

Forbidden patterns (regex, case-insensitive) are listed in FORBIDDEN with the reason.
A line may be exempted with  # fallback-ok: <reason>  which is itself grepped and listed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

FORBIDDEN: list[tuple[str, str]] = [
    (r"synthetic", "no synthetic stand-ins on a reportable path"),
    (r"placeholder", "no placeholder data"),
    (r"dummy", "no dummy data"),
    (r"os\.environ\.get\(\s*['\"]HARNESS_HOST_REPO['\"]\s*,", "HARNESS_HOST_REPO has no default"),
    (
        r"except\s+(Exception|BaseException)?\s*:\s*(pass|return\s+None|return\s+\[\]|return\s+\{\})",
        "swallowed exception",
    ),
    (
        r"\.get\([^)]*,\s*(\[\]|\{\}|0|0\.0|''|\"\")\s*\)\s*#?\s*(default|fallback)",
        "defaulted data",
    ),
    (r"if\s+not\s+.*:\s*\n\s*.*=\s*(\[\]|\{\}|generate_|fake_|mock_)", "empty/fake substitution"),
    (r"\bmock\b(?!\w)", "mocks are for tests only"),
    (r"\bfake_", "fake data generator"),
]
EXEMPT = re.compile(r"#\s*fallback-ok:\s*\S")


def scan(path: Path) -> list[tuple[int, str, str]]:
    text = path.read_text()
    hits = []
    lines = text.splitlines()
    for pat, why in FORBIDDEN:
        for m in re.finditer(pat, text, flags=re.IGNORECASE | re.MULTILINE):
            ln = text.count("\n", 0, m.start()) + 1
            line = lines[ln - 1]
            if EXEMPT.search(line):
                continue
            hits.append((ln, why, line.strip()))
    return sorted(set(hits))


def main(argv: list[str]) -> int:
    rc = 0
    for arg in argv:
        p = Path(arg)
        if p.suffix != ".py" or "tests" in p.parts or p.name == "check_no_fallbacks.py":
            continue  # the checker's own pattern table is not harness code
        for ln, why, line in scan(p):
            print(f"{p}:{ln}: {why}: {line}")
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
