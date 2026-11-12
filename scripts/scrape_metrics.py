#!/usr/bin/env python
"""Scrape the vLLM Prometheus endpoint and list metric families (name, type, sample count).
Usage: scrape_metrics.py <base_url> <out.txt>. Writes the raw scrape to out.txt and prints families.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import httpx


def main(base_url: str, out: str) -> int:
    text = httpx.get(f"{base_url.rstrip('/')}/metrics", timeout=30).text
    Path(out).write_text(text)
    families: dict[str, tuple[str, int]] = {}
    for line in text.splitlines():
        m = re.match(r"# TYPE (\S+) (\S+)", line)
        if m:
            families[m.group(1)] = (m.group(2), 0)
        elif line and not line.startswith("#"):
            name = re.match(r"([A-Za-z_:][A-Za-z0-9_:]*)", line).group(1)
            base = re.sub(r"_(bucket|sum|count|total|created)$", "", name)
            key = name if name in families else base if base in families else name
            t, c = families.get(key, ("?", 0))
            families[key] = (t, c + 1)
    for name, (t, c) in sorted(families.items()):
        print(f"{name}\t{t}\t{c}")
    print(f"# {len(families)} families")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
