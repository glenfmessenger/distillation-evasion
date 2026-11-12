from collections import Counter

import pytest

from dev_harness.detectors.stats import d1_rate
from dev_harness.levers import price, shape_rate, split_identities
from dev_harness.records import RequestRecord


def _rec(i, t_s):
    return RequestRecord(
        run_id="c",
        identity_id="campaign-0",
        session_id=f"campaign-0:s{i // 100}",
        request_index_in_session=i % 100,
        arm="campaign:test",
        t_send_ns=int(t_s * 1e9),
        t_sched_ns=int(t_s * 1e9),
        t_first_byte_ns=1,
        t_done_ns=2,
        prompt_tokens=10 + i,
        generated_tokens=20,
        total_tokens=30 + i,
        reasoning_tokens=5,
        cached_prompt_tokens=0,
        turn_count=1,
        finish_reason="stop",
        http_status=200,
        in_flight=False,
        source_fields={
            k: "server:usage"
            for k in (
                "prompt_tokens",
                "generated_tokens",
                "total_tokens",
                "reasoning_tokens",
                "cached_prompt_tokens",
            )
        },
    )


def test_split_keeps_every_record_and_deals_evenly():
    recs = [_rec(i, i * 2.0) for i in range(250)]
    out = split_identities(recs, n=10, seed=3)
    assert len(out) == 250
    assert Counter(r.prompt_tokens for r in out) == Counter(r.prompt_tokens for r in recs)
    per = Counter(r.identity_id for r in out)
    assert len(per) == 10 and set(per.values()) == {25}
    assert split_identities(recs, n=1, seed=0)[0].identity_id.endswith(":L1n1:i0")
    with pytest.raises(ValueError):
        split_identities(recs, n=0, seed=0)


def test_rate_shaping_respects_the_hourly_cap_and_is_seeded():
    recs = split_identities([_rec(i, i * 0.5) for i in range(300)], n=3, seed=0)
    for cap in (1, 2, 5, 26):
        shaped = shape_rate(recs, cap_per_hour=cap, seed=1)
        by = {}
        for r in shaped:
            by.setdefault(r.identity_id, []).append(r)
        for ident, rs in by.items():
            rs.sort(key=lambda r: r.t_sched_ns)
            assert d1_rate(rs).value <= cap, (cap, ident, d1_rate(rs).value)
    a = shape_rate(recs, 5, seed=1)
    b = shape_rate(recs, 5, seed=2)
    assert [r.t_sched_ns for r in a] != [r.t_sched_ns for r in b]
    assert shape_rate(recs, 0, seed=0) == list(recs)


def test_price_counts_identities_and_wall_clock():
    recs = [_rec(i, i * 60.0) for i in range(10)]
    p = price(shape_rate(split_identities(recs, 2, 0), cap_per_hour=2, seed=0))
    assert p["identities"] == 2 and p["requests"] == 10
    assert p["wall_clock_s"] >= 4 * 3600  # five per identity at one per hour, spread


def test_heterogeneous_split_keeps_every_record_and_sums_counts():
    from dev_harness.levers import split_heterogeneous

    recs = [_rec(i, i * 0.5) for i in range(500)]
    out = split_heterogeneous(
        recs,
        n=20,
        seed=1,
        benign_counts=[1, 2, 5, 30, 80],
        benign_session_lens=[1, 2, 4, 9],
        stagger_s=3600.0,
        interval_s=60.0,
    )
    assert len(out) == 500
    assert Counter(r.prompt_tokens for r in out) == Counter(r.prompt_tokens for r in recs)
    per = Counter(r.identity_id for r in out)
    assert len(per) == 20 and len(set(per.values())) > 1  # counts differ across identities
    starts = {}
    for r in out:
        starts.setdefault(r.identity_id, r.t_sched_ns)
        starts[r.identity_id] = min(starts[r.identity_id], r.t_sched_ns)
    assert max(starts.values()) <= 3600 * 10**9
    assert out == split_heterogeneous(
        recs,
        n=20,
        seed=1,
        benign_counts=[1, 2, 5, 30, 80],
        benign_session_lens=[1, 2, 4, 9],
        stagger_s=3600.0,
        interval_s=60.0,
    )
