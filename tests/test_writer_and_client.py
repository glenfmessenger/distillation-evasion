"""Write-ahead semantics and server-sourced usage (charter 3.4, 3.7, M1)."""

import json
from pathlib import Path

import httpx
import pytest

from dev_harness.client import ChatClient, Sampling, ServerUsageMissing
from dev_harness.records import RequestRecord, check_token_identity
from dev_harness.writer import RecordWriter, calibration_records, read_records


def _sse(chunks):
    return "".join(f"data: {json.dumps(c)}\n\n" for c in chunks) + "data: [DONE]\n\n"


def _stream_body(usage=True, reasoning=True, prompt=12, completion=7, total=None):
    chunks = [
        {
            "choices": [
                {
                    "delta": {"reasoning_content": "hmm "} if reasoning else {"content": "x"},
                    "finish_reason": None,
                }
            ]
        },
        {"choices": [{"delta": {"content": "answer"}, "finish_reason": "stop"}]},
    ]
    if usage:
        chunks.append(
            {
                "choices": [],
                "usage": {
                    "prompt_tokens": prompt,
                    "completion_tokens": completion,
                    "total_tokens": prompt + completion if total is None else total,
                    "prompt_tokens_details": {"cached_tokens": 8},
                    "completion_tokens_details": {"reasoning_tokens": 3},
                },
            }
        )
    return _sse(chunks)


def _client(tmp_path: Path, body: str, status=200):
    transport = httpx.MockTransport(
        lambda req: httpx.Response(status, text=body, headers={"content-type": "text/event-stream"})
    )
    writer = RecordWriter(tmp_path / "records.jsonl")
    return ChatClient("http://teacher", "qwen3-8b", writer, transport=transport), writer


def _send(client, idx=0):
    return client.send(
        run_id="r",
        identity_id="i",
        session_id="s",
        request_index=idx,
        arm="benign",
        messages=[{"role": "user", "content": "hi"}],
        sampling=Sampling(),
    )


def test_usage_fields_are_server_sourced_and_written(tmp_path):
    client, writer = _client(tmp_path, _stream_body())
    comp = _send(client)
    rec = comp.record
    assert rec.prompt_tokens == 12 and rec.generated_tokens == 7 and rec.total_tokens == 19
    assert rec.cached_prompt_tokens == 8 and rec.reasoning_tokens == 3
    assert all(v.startswith("server:") for v in rec.source_fields.values())
    assert comp.reasoning == "hmm " and comp.content == "answer"
    recs = read_records(writer.path)
    assert len(recs) == 1 and recs[0].in_flight is False


def test_missing_usage_raises_and_leaves_record_in_flight(tmp_path):
    client, writer = _client(tmp_path, _stream_body(usage=False))
    with pytest.raises(ServerUsageMissing):
        _send(client)
    recs = read_records(writer.path)
    assert len(recs) == 1 and recs[0].in_flight is True


def test_token_identity_violation_raises(tmp_path):
    client, _ = _client(tmp_path, _stream_body(prompt=12, completion=7, total=99))
    with pytest.raises(ValueError, match="token identity violated"):
        _send(client)


def test_write_ahead_stub_survives_a_kill(tmp_path):
    """Simulate a process killed mid-request: only the stub line exists for request 1."""
    client, writer = _client(tmp_path, _stream_body())
    _send(client, idx=0)
    # Write a stub for request 1 and 'die' before completion.
    stub = RequestRecord(
        run_id="r",
        identity_id="i",
        session_id="s",
        request_index_in_session=1,
        arm="benign",
        t_send_ns=1,
        t_first_byte_ns=None,
        t_done_ns=None,
        prompt_tokens=None,
        generated_tokens=None,
        total_tokens=None,
        reasoning_tokens=None,
        cached_prompt_tokens=None,
        turn_count=1,
        finish_reason=None,
        http_status=None,
        in_flight=True,
    )
    writer.append(stub)
    recs = read_records(writer.path)
    kept, excluded = calibration_records(recs)
    assert len(recs) == 2 and len(kept) == 1 and excluded == 1
    assert kept[0].request_index_in_session == 0


def test_malformed_line_raises(tmp_path):
    p = tmp_path / "bad.jsonl"
    p.write_text('{"run_id": "r"}\n')
    with pytest.raises(ValueError, match="malformed record"):
        read_records(p)


def test_check_token_identity_skips_in_flight():
    stub = RequestRecord(
        run_id="r",
        identity_id="i",
        session_id="s",
        request_index_in_session=0,
        arm="benign",
        t_send_ns=1,
        t_first_byte_ns=None,
        t_done_ns=None,
        prompt_tokens=None,
        generated_tokens=None,
        total_tokens=None,
        reasoning_tokens=None,
        cached_prompt_tokens=None,
        turn_count=1,
        finish_reason=None,
        http_status=None,
        in_flight=True,
    )
    check_token_identity(stub)  # no raise
