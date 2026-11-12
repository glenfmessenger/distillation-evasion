"""Write-ahead JSONL record store (charter 3.7).

Protocol: before a request is sent, a stub line with ``in_flight=True`` is appended. When the
response completes, a second line for the same request key is appended with ``in_flight=False``
and the server-sourced fields filled. A reader keeps the LAST line per key. If the process dies
mid-request, only the stub exists, so the record is in flight by construction, not by a flag
someone remembered to set.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from dev_harness.records import RequestRecord, request_key


class RecordWriter:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("a", buffering=1)  # line-buffered

    def append(self, record: RequestRecord) -> None:
        self._fh.write(record.model_dump_json() + "\n")
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()


def read_records(path: Path) -> list[RequestRecord]:
    """All records, last line per request key wins. Malformed lines raise."""
    last: dict[tuple, RequestRecord] = {}
    with Path(path).open() as fh:
        for n, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = RequestRecord.model_validate(json.loads(line))
            except Exception as e:  # noqa: BLE001 - re-raised with location
                raise ValueError(f"{path}:{n}: malformed record: {e}") from e
            last[request_key(rec)] = rec
    return list(last.values())


def calibration_records(records: Iterable[RequestRecord]) -> tuple[list[RequestRecord], int]:
    """Completed records only; returns (kept, number excluded as in-flight)."""
    kept, excluded = [], 0
    for r in records:
        if r.in_flight:
            excluded += 1
        else:
            kept.append(r)
    return kept, excluded
