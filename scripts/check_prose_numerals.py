#!/usr/bin/env python
"""Pre-commit hook: a paper .tex file must not contain hand-typed numerals in prose.

Allowed: numerals inside \\num{...}-style generated macros defined in paper/macros/*.tex,
citation keys, labels, \\ref/\\cite arguments, LaTeX dimension arguments, and lines marked
% numeral-ok: <reason>. Everything else that matches a digit run fails the commit.
Exit 1 lists file:line:text for every violation.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ALLOW_LINE = re.compile(r"%\s*numeral-ok:")
STRIP = [
    re.compile(r"\\[A-Za-z]+(\[[^\]]*\])?\{[^}]*\}"),  # \macro[opt]{arg}, incl. \includegraphics
    re.compile(r"\\[A-Za-z]+\{[^}]*\}"),  # any single-arg macro, incl. generated \Dnum{...}
    re.compile(r"\\[A-Za-z]+\d*"),  # macro names that end in digits, e.g. \FprOneP
    re.compile(r"\[[^\]]*\]"),  # optional args, e.g. [width=0.5\textwidth]
    re.compile(r"%.*$"),  # comments
]
DIGITS = re.compile(r"\d")


def violations(path: Path) -> list[tuple[int, str]]:
    out = []
    for i, line in enumerate(path.read_text().splitlines(), 1):
        if ALLOW_LINE.search(line):
            continue
        stripped = line
        for pat in STRIP:
            stripped = pat.sub("", stripped)
        if DIGITS.search(stripped):
            out.append((i, line.strip()))
    return out


def main(argv: list[str]) -> int:
    rc = 0
    for arg in argv:
        p = Path(arg)
        if not p.exists() or p.suffix != ".tex" or "macros" in p.parts:
            continue
        for ln, txt in violations(p):
            print(f"{p}:{ln}: hand-typed numeral: {txt}")
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
