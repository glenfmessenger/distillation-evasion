"""V2 content-level statistics (PROTOCOL v2.0 §5). These read prompt text; they are never part of
the content-blind set. Pure numpy so they are testable without a GPU; embeddings are supplied.

C2 follows R3 (Liu, Guo, Dong, arXiv:2606.05725; LabRAI/mmd-llm-mea-detection,
MMD_detection/mmd_detector_gpu.py): RBF kernel, bandwidth = sqrt(median positive squared pairwise
distance) over a benign sample, unbiased MMD^2 with diagonal terms excluded, score = mean over
reference draws of the same size from the benign pool. Deviations, stated: our unit is an
identity at matched n = 30 (or a 100-request block), not a 1,500-query batch; the benign null is
the per-unit statistic of benign units scored against a pool that excludes their own identity,
so that the FPR procedure is the one every other detector uses (calibrate()); no multi-kernel.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence

import numpy as np

from dev_harness.pool import ngrams

_TOKEN = re.compile(r"\S+")


def median_bandwidth(x: np.ndarray, rng: np.random.Generator, sample: int = 2000) -> float:
    """R3's median heuristic: sqrt of the median positive squared distance in a benign sample."""
    if len(x) > sample:
        x = x[rng.choice(len(x), size=sample, replace=False)]
    d2 = _sqdist(x, x)
    pos = d2[np.triu_indices(len(x), k=1)]
    pos = pos[pos > 0]
    if pos.size == 0:
        return 1.0
    return float(np.sqrt(np.median(pos)))


def _sqdist(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    aa = np.sum(a * a, axis=1)[:, None]
    bb = np.sum(b * b, axis=1)[None, :]
    return np.maximum(aa + bb - 2.0 * (a @ b.T), 0.0)


def mmd2_unbiased(x: np.ndarray, y: np.ndarray, sigma: float) -> float:
    """Unbiased MMD^2 with an RBF kernel, diagonal terms excluded (R3's estimator)."""
    m, n = len(x), len(y)
    if m < 2 or n < 2:
        raise ValueError("MMD needs at least two points per sample")
    kxx = np.exp(-_sqdist(x, x) / (2.0 * sigma * sigma))
    kyy = np.exp(-_sqdist(y, y) / (2.0 * sigma * sigma))
    kxy = np.exp(-_sqdist(x, y) / (2.0 * sigma * sigma))
    xx = (kxx.sum() - np.trace(kxx)) / (m * (m - 1))
    yy = (kyy.sum() - np.trace(kyy)) / (n * (n - 1))
    return float(xx + yy - 2.0 * kxy.sum() / (m * n))


def c2_mmd_score(
    unit: np.ndarray,
    pool: np.ndarray,
    sigma: float,
    rng: np.random.Generator,
    n_match: int = 30,
    n_sub: int = 20,
    reference_repeats: int = 20,
) -> float:
    """Median over `n_sub` matched-n subsamples of the unit of the mean unbiased MMD^2 against
    `reference_repeats` draws of n_match points from the benign pool (which must exclude the
    unit's own prompts)."""
    if len(unit) < n_match or len(pool) < n_match:
        return float("nan")
    vals = []
    for _ in range(n_sub):
        u = unit[rng.choice(len(unit), size=n_match, replace=False)]
        refs = [
            pool[rng.choice(len(pool), size=n_match, replace=False)]
            for _ in range(reference_repeats)
        ]
        vals.append(float(np.mean([mmd2_unbiased(u, r, sigma) for r in refs])))
    return float(np.median(vals))


def normalise(text: str) -> str:
    return " ".join(_TOKEN.findall(text.lower()))


def benchmark_index(pool_prompts: Iterable[str], n: int = 13) -> tuple[set[str], set[tuple]]:
    """Exact normalised texts and n-grams of the public query pool (B1's reference)."""
    exact, grams = set(), set()
    for p in pool_prompts:
        exact.add(normalise(p))
        grams |= ngrams(p, n)
    return exact, grams


def b1_membership(prompts: Sequence[str], index: tuple[set[str], set[tuple]], n: int = 13) -> float:
    """B1: share of a unit's prompts that occur in the public pool (exact or any n-gram)."""
    exact, grams = index
    if not prompts:
        return float("nan")
    hits = 0
    for p in prompts:
        if normalise(p) in exact or (grams & ngrams(p, n)):
            hits += 1
    return hits / len(prompts)


def b2_template_reuse(prompts: Sequence[str], min_suffix_tokens: int = 8) -> float:
    """B2: share of a unit's prompts whose last `min_suffix_tokens` tokens are shared with at
    least one other prompt in the unit (a fixed instruction suffix)."""
    if len(prompts) < 2:
        return float("nan")
    tails = [tuple(_TOKEN.findall(p.lower())[-min_suffix_tokens:]) for p in prompts]
    counts: dict[tuple, int] = {}
    for t in tails:
        if len(t) == min_suffix_tokens:
            counts[t] = counts.get(t, 0) + 1
    shared = sum(1 for t in tails if len(t) == min_suffix_tokens and counts[t] >= 2)
    return shared / len(prompts)


def c3_diversity(
    unit: np.ndarray, rng: np.random.Generator, n_match: int = 30, n_sub: int = 20
) -> float:
    """C3 (post-hoc, amendment B1): median over matched-n subsamples of the mean pairwise cosine
    distance among the unit's (unit-normalised) prompt embeddings. Direction high: a unit broader
    than any real user."""
    if len(unit) < n_match:
        return float("nan")
    vals = []
    for _ in range(n_sub):
        e = unit[rng.choice(len(unit), size=n_match, replace=False)]
        sim = e @ e.T
        vals.append(float(1.0 - (sim.sum() - n_match) / (n_match * (n_match - 1))))
    return float(np.median(vals))
