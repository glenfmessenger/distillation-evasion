"""Content-blind detectors. Each detector maps a session (or identity) of RequestRecords
to one scalar statistic; thresholds are set later from benign sessions per FPR budget
(charter 3.11: statistics are stored per session, never detection rates per run)."""

from .base import Detector, SessionStatistic

__all__ = ["Detector", "SessionStatistic"]
