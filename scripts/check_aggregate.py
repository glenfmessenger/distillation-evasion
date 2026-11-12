#!/usr/bin/env python
"""Sufficiency check (charter 3.10).

Rebuilds every table and figure from the committed aggregate files with the raw results
root pointed at an EMPTY directory. Any table that cannot be rebuilt fails the check.

M0 state: no aggregates, no tables. The script fails loudly rather than passing vacuously
(a check that passes when nothing exists is not a check; charter 3.4).
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

AGGREGATES = Path(__file__).resolve().parents[1] / "results" / "aggregates"
REQUIRED_GRAINS = ("runs", "requests", "sessions")


def main() -> int:
    missing = [g for g in REQUIRED_GRAINS if not (AGGREGATES / g).exists()]
    if missing:
        print(f"FAIL: aggregate grains missing: {missing} (nothing committed yet)")
        return 1
    with tempfile.TemporaryDirectory() as empty_raw:
        print(f"raw root pinned to empty dir {empty_raw}; table builders not yet registered")
        print("FAIL: no table builders registered (M0)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
