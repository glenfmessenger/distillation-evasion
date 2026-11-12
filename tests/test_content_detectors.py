import math

import numpy as np

from dev_harness.detectors.content import (
    b1_membership,
    b2_template_reuse,
    benchmark_index,
    c2_mmd_score,
    median_bandwidth,
    mmd2_unbiased,
)


def test_mmd_is_near_zero_for_same_distribution_and_large_for_shifted():
    rng = np.random.default_rng(0)
    pool = rng.normal(size=(400, 8))
    sigma = median_bandwidth(pool, rng)
    same = rng.normal(size=(60, 8))
    shifted = rng.normal(size=(60, 8)) + 3.0
    s_same = c2_mmd_score(same, pool, sigma, rng, n_match=30, n_sub=5, reference_repeats=5)
    s_shift = c2_mmd_score(shifted, pool, sigma, rng, n_match=30, n_sub=5, reference_repeats=5)
    assert abs(s_same) < 0.05
    assert s_shift > 0.3
    assert math.isnan(c2_mmd_score(same[:10], pool, sigma, rng))  # below matched n


def test_mmd_unbiased_matches_the_hand_formula():
    rng = np.random.default_rng(1)
    x, y, sigma = rng.normal(size=(5, 3)), rng.normal(size=(7, 3)), 1.3

    def k(a, b):
        return np.exp(-np.sum((a - b) ** 2) / (2 * sigma**2))

    xx = sum(k(x[i], x[j]) for i in range(5) for j in range(5) if i != j) / (5 * 4)
    yy = sum(k(y[i], y[j]) for i in range(7) for j in range(7) if i != j) / (7 * 6)
    xy = sum(k(x[i], y[j]) for i in range(5) for j in range(7)) / 35
    assert abs(mmd2_unbiased(x, y, sigma) - (xx + yy - 2 * xy)) < 1e-12


def test_b1_membership_catches_benchmark_prompts_only():
    pool = [
        "Let x be a real number such that x squared equals four. Find all possible values of x now please."
    ]
    idx = benchmark_index(pool)
    unit = [pool[0] + "\n\nPlease reason step by step.", "write me a poem about autumn"]
    assert b1_membership(unit, idx) == 0.5
    assert math.isnan(b1_membership([], idx))


def test_b2_template_reuse_detects_a_fixed_suffix():
    suffix = " Please reason step by step, and put your final answer within boxed."
    unit = [
        "q1" + suffix,
        "q2" + suffix,
        "something else entirely with no shared ending here at all",
    ]
    assert abs(b2_template_reuse(unit) - 2 / 3) < 1e-9
    assert b2_template_reuse(["a b c d e f g h i", "j k l m n o p q r"]) == 0.0
    assert math.isnan(b2_template_reuse(["one"]))


def test_c3_diversity_is_higher_for_a_broad_unit():
    from dev_harness.detectors.content import c3_diversity

    rng = np.random.default_rng(0)
    narrow = rng.normal(size=(40, 8)) * 0.05 + np.array([1.0] + [0.0] * 7)
    broad = rng.normal(size=(40, 8))
    narrow /= np.linalg.norm(narrow, axis=1, keepdims=True)
    broad /= np.linalg.norm(broad, axis=1, keepdims=True)
    assert c3_diversity(broad, rng, 30, 5) > c3_diversity(narrow, rng, 30, 5) + 0.5
    assert math.isnan(c3_diversity(broad[:10], rng, 30, 5))
