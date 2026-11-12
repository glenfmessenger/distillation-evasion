"""Math-verification worker process. One JSON request per stdin line, one JSON reply per line on
the original stdout. Runs in its own process so the parent can kill it: a symbolic comparison that
enters one giant integer operation holds the interpreter lock and cannot be timed out from a
thread (FINDINGS F38)."""

from __future__ import annotations

import json
import os
import sys


def main() -> None:
    out = os.fdopen(os.dup(1), "w")
    os.dup2(2, 1)  # anything a library prints goes to stderr, never into the reply channel
    sys.stdout = sys.stderr
    from math_verify import parse, verify

    for line in sys.stdin:
        req = json.loads(line)
        try:
            # math-verify's own timeouts use signal.alarm; the parent enforces the budget instead.
            g = parse(f"${req['gold']}$", parsing_timeout=None)
            if req["boxed"] is not None:
                p = parse(f"${req['boxed']}$", parsing_timeout=None)
            else:
                # No \boxed{}: math-verify's default extraction (last LaTeX / number), F25.
                p = parse(req["pred_text"], parsing_timeout=None)
            rep = {"ok": bool(verify(g, p, timeout_seconds=None)) if p else False}
        except MemoryError:
            rep = {"budget": "memory"}
        except Exception as e:  # noqa: BLE001 - reported to the parent, which raises
            rep = {"err": repr(e)}
        out.write(json.dumps(rep) + "\n")
        out.flush()


if __name__ == "__main__":
    main()
