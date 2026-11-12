import numpy as np

from dev_harness.detectors.coordination import (
    Standardiser,
    features,
    nearest_neighbour_radius,
    same_day_density,
    score_campaign,
)


def _row(requests, start_hour, day=0, sessions=1, gap=30.0, span=600.0, st=1.0):
    return {
        "identity": "x",
        "day": day,
        "requests": requests,
        "sessions": sessions,
        "session_len_median": requests / sessions,
        "gap_median_s": gap,
        "span_s": span,
        "start_hour": start_hour,
        "single_turn_frac": st,
    }


def test_clones_have_high_density_and_scattered_users_do_not():
    rng = np.random.default_rng(0)
    benign = [
        _row(
            int(rng.integers(1, 40)),
            rng.uniform(0, 24),
            day=int(rng.integers(0, 10)),
            sessions=int(rng.integers(1, 5)),
            gap=float(rng.uniform(5, 600)),
            span=float(rng.uniform(60, 40000)),
            st=float(rng.uniform(0, 1)),
        )
        for _ in range(2000)
    ]
    zb = np.stack([features(r) for r in benign])
    db = np.array([r["day"] for r in benign])
    std = Standardiser(zb)
    zb = std(zb)
    r = nearest_neighbour_radius(zb, db)
    benign_density = same_day_density(zb, db, r)
    thr = np.sort(benign_density)[-int(0.01 * len(benign)) - 1]
    clones = [
        _row(
            20,
            9.0 + rng.uniform(0, 0.05),
            day=3,
            sessions=1,
            gap=30.0 + rng.uniform(0, 1),
            span=600.0 + rng.uniform(0, 5),
            st=1.0,
        )
        for _ in range(100)
    ]
    zc = std(np.stack([features(c) for c in clones]))
    dc = np.array([c["day"] for c in clones])
    dens = score_campaign(zb, db, zc, dc, r)
    assert np.mean(dens > thr) >= 0.9
    assert np.median(dens) >= 50


def test_birth_burst_counts_neighbours_within_window():
    from dev_harness.detectors.coordination import birth_burst, score_births

    b = np.array([0.0, 100.0, 130.0, 5000.0, 5001.0, 5002.0])
    assert birth_burst(b, 60.0).tolist() == [0, 1, 1, 2, 2, 2]
    benign = np.arange(0, 86400.0, 600.0)  # one birth every ten minutes
    camp = np.full(100, 43200.0) + np.arange(100) * 0.5  # a hundred births within a minute
    assert (score_births(benign, camp, 600.0) >= 99).all()
