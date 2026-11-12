"""Record schema: in_flight is mandatory; token counts must be server-sourced (charter 3.7, M1)."""

import pytest
from pydantic import ValidationError

from dev_harness.records import RequestRecord, assert_server_sourced

BASE = dict(
    run_id="r",
    identity_id="i",
    session_id="s",
    request_index_in_session=0,
    arm="benign",
    t_send_ns=1,
    t_first_byte_ns=2,
    t_done_ns=3,
    prompt_tokens=10,
    generated_tokens=20,
    total_tokens=30,
    reasoning_tokens=None,
    cached_prompt_tokens=None,
    turn_count=1,
    finish_reason="stop",
    http_status=200,
)


def test_in_flight_has_no_default():
    with pytest.raises(ValidationError):
        RequestRecord(**BASE)


def test_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        RequestRecord(**BASE, in_flight=False, surprise=1)


def test_client_inferred_token_counts_rejected():
    rec = RequestRecord(
        **BASE,
        in_flight=False,
        source_fields={"prompt_tokens": "client", "generated_tokens": "server:usage"},
    )
    with pytest.raises(ValueError, match="prompt_tokens must be server-sourced"):
        assert_server_sourced(rec)


def test_missing_source_rejected():
    rec = RequestRecord(**BASE, in_flight=False, source_fields={"prompt_tokens": "server:usage"})
    with pytest.raises(ValueError, match="generated_tokens"):
        assert_server_sourced(rec)


def test_server_sourced_accepted():
    rec = RequestRecord(
        **BASE,
        in_flight=False,
        source_fields={
            "prompt_tokens": "server:usage",
            "generated_tokens": "server:usage",
            "total_tokens": "server:usage",
        },
    )
    assert_server_sourced(rec)
