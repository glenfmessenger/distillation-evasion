from dev_harness.detectors.base import drop_in_flight
from dev_harness.records import RequestRecord

BASE = dict(
    run_id="r",
    identity_id="i",
    session_id="s",
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
)


def test_drop_in_flight_counts_exclusions():
    recs = [
        RequestRecord(**BASE, request_index_in_session=k, in_flight=(k % 2 == 1)) for k in range(5)
    ]
    kept, n_excl = drop_in_flight(recs)
    assert len(kept) == 3 and n_excl == 2
    assert all(not r.in_flight for r in kept)
