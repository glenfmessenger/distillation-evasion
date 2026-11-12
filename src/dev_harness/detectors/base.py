from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from dev_harness.records import RequestRecord


@dataclass(frozen=True)
class SessionStatistic:
    detector_id: str
    session_id: str
    identity_id: str
    value: float
    n_records: int
    n_excluded_in_flight: int


class Detector(Protocol):
    detector_id: str
    direction: str  # "high" means larger statistic = more campaign-like

    def statistic(self, records: Sequence[RequestRecord]) -> SessionStatistic: ...


def drop_in_flight(records: Sequence[RequestRecord]) -> tuple[list[RequestRecord], int]:
    kept = [r for r in records if not r.in_flight]
    return kept, len(records) - len(kept)
