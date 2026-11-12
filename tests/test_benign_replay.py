"""Benign schedule construction and replay (PROTOCOL §4). Test fixtures are hand-built rows; the
real loader path is exercised on the VM against WildChat (scripts/build_benign.py)."""

import json
import random

import httpx
import pytest

from dev_harness.benign import (
    BenignDataError,
    Conversation,
    ScheduledRequest,
    _sessionise,
    build_schedule,
    constructed_schedule,
    read_schedule,
    real_user_schedule,
    select_replay_subset,
    user_key,
    write_schedule,
)
from dev_harness.client import ChatClient, Sampling
from dev_harness.detectors.stats import d3_cadence
from dev_harness.records import RequestRecord
from dev_harness.replay import replay
from dev_harness.writer import RecordWriter, read_records


def corpus(n_users=400, seed=0):
    rng = random.Random(seed)
    out = []
    for u in range(n_users):
        t = 1_700_000_000.0 + rng.uniform(0, 1e6)
        for c in range(rng.randint(1, 4)):
            n_turns = rng.choice([1, 1, 1, 2, 3, 9])
            turns, tt = [], t
            for k in range(n_turns):
                tt += rng.uniform(5, 120)
                body = (
                    ("long " * 1000) if (n_turns == 1 and rng.random() < 0.5) else f"q{u}-{c}-{k}"
                )
                turns.append((tt, body))
            out.append(
                Conversation(
                    f"h{u}-{c}", user_key(f"ip{u}", "ua"), tuple(turns), has_code=(u % 7 == 0)
                )
            )
            t = tt + rng.choice([60, 4000, 90000])
    out.append(None)  # one row skipped for missing timestamps
    return out


EVAL = [f"mcq {i}" for i in range(400)]


def test_sessionise_splits_on_idle_gap_and_rebases_time():
    s = _sessionise(
        "id", "conversational", [(100.0, "c", 0, "a"), (160.0, "c", 1, "b"), (5000.0, "d", 0, "c")]
    )
    assert [r.session_id for r in s] == ["id:s0", "id:s0", "id:s1"]
    assert [r.request_index for r in s] == [0, 1, 0] and [r.t_sched_s for r in s] == [
        0.0,
        60.0,
        4900.0,
    ]


def test_mixture_counts_and_manifest():
    sched, m = build_schedule(corpus(), n_identities=100, seed=1, eval_prompts=EVAL)
    assert m["identities_by_component"] == {
        "conversational": 85,
        "eval_harness": 4,
        "batch_summarise": 3,
        "agent_loop": 3,
        "code_assistant": 5,
    }
    assert m["n_conversations_skipped_missing_timestamps"] == 1
    assert m["n_requests"] == len(sched) and m["identities_with_ge_30_requests"] >= 4
    assert {r.component for r in sched} == set(m["weights"])


def test_build_is_deterministic_and_roundtrips(tmp_path):
    a, _ = build_schedule(corpus(), 100, 1, EVAL)
    b, _ = build_schedule(corpus(), 100, 1, EVAL)
    assert a == b
    h1 = write_schedule(a, tmp_path / "s.jsonl")
    assert read_schedule(tmp_path / "s.jsonl") == a and len(h1) == 64


def test_insufficient_corpus_raises_instead_of_shrinking():
    with pytest.raises(BenignDataError, match="read more files"):
        build_schedule(corpus(n_users=20), 1000, 1, EVAL)


def _sse_handler(seen):
    def h(req: httpx.Request) -> httpx.Response:
        body = json.loads(req.content)
        seen.append(body["messages"])
        chunks = [
            {
                "choices": [
                    {"delta": {"content": f"A{len(body['messages'])}"}, "finish_reason": "stop"}
                ]
            },
            {
                "choices": [],
                "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
            },
        ]
        return httpx.Response(
            200, text="".join(f"data: {json.dumps(c)}\n\n" for c in chunks) + "data: [DONE]\n\n"
        )

    return h


def test_replay_carries_teacher_history_and_scheduled_time(tmp_path):
    sched = [
        ScheduledRequest("i", "i:s0", 0, "conversational", 0.0, "c1", 0, "hello"),
        ScheduledRequest("i", "i:s0", 1, "conversational", 42.0, "c1", 1, "again"),
        ScheduledRequest("i", "i:s0", 2, "conversational", 50.0, "c2", 0, "new topic"),
    ]
    seen: list = []
    w = RecordWriter(tmp_path / "r.jsonl")
    client = ChatClient("http://t", "m", w, transport=httpx.MockTransport(_sse_handler(seen)))
    stats = replay(sched, client, "run", Sampling(), concurrency=2)
    assert stats["completed"] == 3 and stats["failed"] == 0
    assert seen[1] == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "A1"},
        {"role": "user", "content": "again"},
    ]
    assert seen[2] == [{"role": "user", "content": "new topic"}]
    recs = sorted(read_records(w.path), key=lambda r: r.request_index_in_session)
    assert [r.t_sched_ns for r in recs] == [0, 42_000_000_000, 50_000_000_000]
    assert [r.turn_count for r in recs] == [1, 2, 1]
    assert d3_cadence(recs).value == pytest.approx(
        0.68, abs=0.01
    )  # gaps 42 s and 8 s on the scheduled timeline


def test_replay_aborts_session_after_failure_and_counts(tmp_path):
    sched = [
        ScheduledRequest("i", "i:s0", k, "conversational", float(k), "c1", k, f"t{k}")
        for k in range(3)
    ]
    w = RecordWriter(tmp_path / "r.jsonl")
    client = ChatClient(
        "http://t", "m", w, transport=httpx.MockTransport(lambda r: httpx.Response(500))
    )
    stats = replay(sched, client, "run", Sampling(), concurrency=1)
    assert stats == {
        "sessions": 1,
        "requests": 3,
        "sessions_aborted": 1,
        "completed": 0,
        "failed": 1,
        "requests_skipped_after_failure": 2,
        "requests_too_long": 0,
    }
    recs = read_records(w.path)
    assert len(recs) == 1 and recs[0].in_flight is True


def test_request_record_has_no_content_field():
    """Detectors read RequestRecord only; it must not be able to carry prompt or response text."""
    forbidden = {"content", "prompt", "messages", "text", "user_content", "reasoning", "response"}
    assert not forbidden & set(RequestRecord.model_fields)


def test_mixed_time_base_is_rejected():
    base = dict(
        run_id="r",
        identity_id="i",
        session_id="s",
        arm="x",
        t_first_byte_ns=2,
        t_done_ns=3,
        prompt_tokens=1,
        generated_tokens=1,
        total_tokens=2,
        reasoning_tokens=None,
        cached_prompt_tokens=None,
        turn_count=1,
        finish_reason="stop",
        http_status=200,
        in_flight=False,
    )
    recs = [
        RequestRecord(**base, request_index_in_session=0, t_send_ns=1, t_sched_ns=5),
        RequestRecord(**base, request_index_in_session=1, t_send_ns=2),
        RequestRecord(**base, request_index_in_session=2, t_send_ns=3),
    ]
    from dev_harness.detectors.stats import by_session

    with pytest.raises(ValueError, match="mixed scheduled"):
        by_session(recs)


def test_real_user_schedule_and_stratified_subset():
    full, skipped = real_user_schedule(corpus(n_users=600, seed=3))
    assert skipped == 1 and {r.component for r in full} <= {"conversational", "code_assistant"}
    sub, info = select_replay_subset(full, n_heavy=3, n_light=50, cap=12, seed=0, heavy_min=15)
    per = {}
    for r in sub:
        per[r.identity_id] = per.get(r.identity_id, 0) + 1
    assert len(per) == 53 and max(per.values()) == 12 and info["identities_truncated"] >= 3
    assert info["population_heavy"] >= 3 and info["sampled_light"] == 50
    with pytest.raises(BenignDataError, match="strata too small"):
        select_replay_subset(full, n_heavy=10**6, n_light=1, cap=12, seed=0)


def test_truncation_keeps_conversation_prefix():
    full, _ = real_user_schedule(corpus(n_users=600, seed=3))
    sub, _ = select_replay_subset(full, n_heavy=3, n_light=0, cap=12, seed=0, heavy_min=15)
    seen = {}
    for r in sorted(sub, key=lambda r: (r.identity_id, r.t_sched_s, r.request_index)):
        assert r.turn_index == seen.get(r.conv_id, -1) + 1, (
            "a later turn was kept without its earlier turns"
        )
        seen[r.conv_id] = r.turn_index


def test_constructed_components_sizes():
    out = constructed_schedule(
        corpus(n_users=3000, seed=4),
        EVAL,
        seed=0,
        n_eval=2,
        n_batch=2,
        n_agent=3,
        eval_range=(50, 60),
        batch_range=(30, 35),
    )
    per = {}
    for r in out:
        per.setdefault(r.component, {}).setdefault(r.identity_id, 0)
        per[r.component][r.identity_id] += 1
    assert len(per["eval_harness"]) == 2 and all(
        50 <= v <= 60 for v in per["eval_harness"].values()
    )
    assert len(per["batch_summarise"]) == 2 and all(
        30 <= v <= 35 for v in per["batch_summarise"].values()
    )
    assert len(per["agent_loop"]) == 3 and all(v >= 8 for v in per["agent_loop"].values())


def test_replay_skips_and_counts_prompts_that_do_not_fit(tmp_path):
    sched = [
        ScheduledRequest("i", "i:s0", 0, "conversational", 0.0, "c1", 0, "x"),
        ScheduledRequest("i", "i:s0", 1, "conversational", 1.0, "c1", 1, "y"),
    ]
    w = RecordWriter(tmp_path / "r.jsonl")
    client = ChatClient("http://t", "m", w, transport=httpx.MockTransport(_sse_handler([])))
    stats = replay(
        sched,
        client,
        "run",
        Sampling(),
        concurrency=1,
        sampling_fn=lambda m: None if len(m) > 1 else Sampling(),
    )
    assert stats["completed"] == 1 and stats["requests_too_long"] == 1 and stats["failed"] == 0
