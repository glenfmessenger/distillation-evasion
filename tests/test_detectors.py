"""Each detector has a configuration where it MUST fire and one where it MUST NOT (charter 3.3)."""

import math

import numpy as np
import pytest

from dev_harness.detectors.stats import (
    BenignReference,
    all_statistics,
    calibrate,
    d1_rate,
    d3_cadence,
    d5_reasoning_share,
    d7_cache_share,
    d8_coverage,
    d9_single_turn,
    fires,
    jsd,
)
from dev_harness.records import RequestRecord


def rec(
    ident, sess, i, t_s, prompt=100, gen=300, reasoning=None, cached=None, turns=1, in_flight=False
):
    return RequestRecord(
        run_id="t",
        identity_id=ident,
        session_id=sess,
        request_index_in_session=i,
        arm="x",
        t_send_ns=int(t_s * 1e9),
        t_first_byte_ns=int(t_s * 1e9) + 1,
        t_done_ns=int(t_s * 1e9) + 2,
        prompt_tokens=prompt,
        generated_tokens=gen,
        total_tokens=prompt + gen,
        reasoning_tokens=reasoning,
        cached_prompt_tokens=cached,
        turn_count=turns,
        finish_reason="stop",
        http_status=200,
        in_flight=in_flight,
    )


def benign(rng, n_users=40, per=20):
    out = []
    for u in range(n_users):
        t = 0.0
        for i in range(per):
            t += rng.exponential(60.0)
            out.append(
                rec(
                    f"u{u}",
                    f"u{u}:s",
                    i,
                    t,
                    prompt=int(rng.integers(20, 600)),
                    gen=int(rng.integers(50, 900)),
                    reasoning=int(rng.integers(0, 100)),
                    cached=0,
                    turns=int(rng.integers(1, 5)),
                )
            )
    return out


@pytest.fixture
def ref():
    return BenignReference.fit(benign(np.random.default_rng(0)))


def test_in_flight_records_are_excluded_and_counted():
    s = [rec("a", "a:s", i, i * 1.0) for i in range(5)] + [rec("a", "a:s", 5, 5.0, in_flight=True)]
    st = d3_cadence(s)
    assert st.n_records == 5 and st.n_excluded_in_flight == 1


def test_d3_regular_cadence_low_cv_human_cadence_high_cv():
    regular = [rec("c", "c:s", i, i * 2.0) for i in range(30)]
    rng = np.random.default_rng(1)
    human = [rec("h", "h:s", i, t) for i, t in enumerate(np.cumsum(rng.exponential(30, 30)))]
    assert d3_cadence(regular).value < 0.05 < d3_cadence(human).value


def test_d1_rate_fires_on_burst_not_on_trickle():
    burst = [rec("b", "b:s", i, i * 1.0) for i in range(500)]
    trickle = [rec("t", "t:s", i, i * 600.0) for i in range(50)]
    assert d1_rate(burst).value == 500 and d1_rate(trickle).value == 7


def test_d5_reasoning_share_direction():
    heavy = [rec("r", "r:s", i, i, gen=1000, reasoning=900) for i in range(5)]
    light = [rec("l", "l:s", i, i, gen=1000, reasoning=50) for i in range(5)]
    assert d5_reasoning_share(heavy).value > 0.8 > 0.1 > d5_reasoning_share(light).value


def test_d7_cache_share_and_none_handling():
    hits = [rec("x", "x:s", i, i, prompt=400, cached=256) for i in range(5)]
    none = [rec("y", "y:s", i, i, prompt=400, cached=None) for i in range(5)]
    assert d7_cache_share(hits).value == pytest.approx(0.64)
    assert math.isnan(d7_cache_share(none).value)


def test_d9_single_turn():
    assert d9_single_turn([rec("a", "a:s", i, i, turns=1) for i in range(4)]).value == 1.0
    assert d9_single_turn([rec("a", "a:s", i, i, turns=3) for i in range(4)]).value == 0.0


def test_d8_concentrated_identity_diverges_more_than_benign_like_identity(ref):
    rng = np.random.default_rng(2)
    conc = [rec("camp", "camp:s", i, i, prompt=150, gen=6000) for i in range(60)]  # one cell
    like = benign(rng, n_users=1, per=60)
    like = [r.model_copy(update={"identity_id": "like", "session_id": "like:s"}) for r in like]
    assert d8_coverage(conc, ref).value > d8_coverage(like, ref).value
    assert math.isnan(d8_coverage(conc[:10], ref).value)  # below matched n: unscoreable


def test_d8_matched_n_is_invariant_to_sample_size(ref):
    big = [rec("camp", "camp:s", i, i, prompt=150, gen=6000) for i in range(600)]
    small = big[:60]
    assert d8_coverage(big, ref).value == pytest.approx(d8_coverage(small, ref).value, abs=1e-9)


def test_jsd_bounds():
    assert jsd({"a": 1.0}, {"a": 1.0}) == 0.0
    assert jsd({"a": 1.0}, {"b": 1.0}) == pytest.approx(1.0)


def test_calibrate_reports_resolution_and_exceedances():
    vals = list(np.random.default_rng(3).normal(size=2000))
    cal = calibrate(vals, "high", 0.01)
    assert (
        cal["n_exceed"] == 20 and cal["below_resolution"] is False and cal["resolution"] == 1 / 2000
    )
    cal2 = calibrate(vals, "high", 0.001)
    assert cal2["n_exceed"] == 2 and cal2["below_resolution"] is True
    assert fires(cal["threshold"] + 1, cal) is True and fires(float("nan"), cal) is None


def test_all_statistics_runs_on_benign_and_covers_every_detector(ref):
    stats = all_statistics(benign(np.random.default_rng(5), n_users=5, per=40), ref)
    assert {s.detector_id for s in stats} == {
        "D1",
        "D2",
        "D3",
        "D4",
        "D5",
        "D6",
        "D7",
        "D8",
        "D8b",
        "D9",
    }
