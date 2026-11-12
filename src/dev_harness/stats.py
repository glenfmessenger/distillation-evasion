"""Bootstrap confidence intervals (PROTOCOL §2, §8): BCa over items, seeds recorded."""

from __future__ import annotations

import numpy as np
from scipy import stats


def mean_bca_ci(values, n_resamples: int = 2000, seed: int = 0, level: float = 0.95) -> dict:
    x = np.asarray(values, dtype=float)
    if x.size < 2:
        raise ValueError("need at least two items for a bootstrap CI")
    if np.allclose(x, x[0]):
        return {
            "mean": float(x.mean()),
            "lo": float(x.mean()),
            "hi": float(x.mean()),
            "n": int(x.size),
            "method": "degenerate",
            "seed": seed,
        }
    rng = np.random.default_rng(seed)
    res = stats.bootstrap(
        (x,),
        np.mean,
        n_resamples=n_resamples,
        confidence_level=level,
        method="BCa",
        random_state=rng,
    )
    return {
        "mean": float(x.mean()),
        "lo": float(res.confidence_interval.low),
        "hi": float(res.confidence_interval.high),
        "n": int(x.size),
        "method": "BCa",
        "n_resamples": n_resamples,
        "seed": seed,
    }
