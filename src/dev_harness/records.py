"""Per-request record schema (charter M1, 3.7).

Every field is populated server-side or by the harness client at send/receive time and
written as one JSONL line per request. `in_flight` is mandatory: a record whose response
had not completed when the run ended is marked True and excluded from calibration by
default (charter 3.7). There is no default value for `in_flight`; a writer that forgets
it fails validation.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RequestRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    identity_id: str
    session_id: str
    request_index_in_session: int = Field(ge=0)
    arm: str  # e.g. "benign", "campaign:baseline", "campaign:L6:c0.5"

    t_send_ns: int  # client monotonic send time
    t_sched_ns: int | None = (
        None  # scheduled (corpus/policy) time; cadence detectors use it when set
    )
    t_first_byte_ns: int | None  # None when in_flight
    t_done_ns: int | None  # None when in_flight

    prompt_tokens: int | None
    generated_tokens: int | None
    total_tokens: int | None  # server-reported; used for the consistency identity
    reasoning_tokens: int | None  # None if the serving layer does not expose it
    cached_prompt_tokens: int | None  # prefix-cache hit tokens, None if not exposed

    turn_count: int = Field(ge=1)  # number of user turns in the request's messages
    finish_reason: str | None
    http_status: int | None

    in_flight: bool  # no default on purpose (charter 3.7)
    source_fields: dict[str, str] = Field(default_factory=dict)
    # Maps each token/cache field name to where it came from ("server:usage",
    # "server:usage.prompt_tokens_details", ...). "client" is forbidden for token counts;
    # see tests/test_records.py.


CLIENT_INFERRED_FORBIDDEN = (  # ordered: error messages must be deterministic (FINDINGS F14)
    "prompt_tokens",
    "generated_tokens",
    "total_tokens",
    "reasoning_tokens",
    "cached_prompt_tokens",
)


def assert_server_sourced(record: RequestRecord) -> None:
    """Raise if any token/cache field present on the record is not server-sourced."""
    for name in CLIENT_INFERRED_FORBIDDEN:
        if getattr(record, name) is None:
            continue
        src = record.source_fields.get(name)
        if src is None or not src.startswith("server:"):
            raise ValueError(f"{name} must be server-sourced; got source_fields[{name!r}]={src!r}")


REQUEST_KEY_FIELDS = ("run_id", "identity_id", "session_id", "request_index_in_session")


def request_key(record: RequestRecord) -> tuple[str, str, str, int]:
    return tuple(getattr(record, f) for f in REQUEST_KEY_FIELDS)  # type: ignore[return-value]


def check_token_identity(record: RequestRecord) -> None:
    """Consistency identity on completed records: prompt + generated == total (all server-side)."""
    if record.in_flight:
        return
    if (
        record.prompt_tokens is None
        or record.generated_tokens is None
        or record.total_tokens is None
    ):
        raise ValueError(f"completed record {request_key(record)} is missing a server token count")
    if record.prompt_tokens + record.generated_tokens != record.total_tokens:
        raise ValueError(
            f"token identity violated for {request_key(record)}: "
            f"{record.prompt_tokens} + {record.generated_tokens} != {record.total_tokens}"
        )
    if record.t_first_byte_ns is None or record.t_done_ns is None:
        raise ValueError(f"completed record {request_key(record)} lacks timestamps")
    if not (record.t_send_ns <= record.t_first_byte_ns <= record.t_done_ns):
        raise ValueError(f"timestamp order violated for {request_key(record)}")


def event_time_ns(record: RequestRecord) -> int:
    """Time used by cadence/rate detectors: the scheduled time when the run has one, else send time."""
    return record.t_sched_ns if record.t_sched_ns is not None else record.t_send_ns
