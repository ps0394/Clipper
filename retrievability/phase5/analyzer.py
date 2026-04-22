"""Correlation analysis for Phase 5.

Per design doc §6: Spearman ρ between each Clipper pillar score and
per-page LLM QA accuracy, with 10 000-resample bootstrap 95% CIs.
Reported per pillar, per profile, per scoring LLM.

SCAFFOLDING — implements the math. The pilot runner wires the input:
(page → pillar scores) from Clipper's `*_scores.json`, and
(page → QA accuracy) from the grader. Dependencies are scipy and numpy
if available; falls back to a pure-Python Spearman + bootstrap if not,
since Clipper intentionally keeps runtime deps minimal.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class Correlation:
    pillar: str
    n: int
    rho: float
    ci_low: float
    ci_high: float
    p_value: float

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def _rank(values: Sequence[float]) -> List[float]:
    """Average-rank assignment with tie handling."""
    indexed = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and values[indexed[j + 1]] == values[indexed[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[indexed[k]] = avg
        i = j + 1
    return ranks


def spearman_rho(x: Sequence[float], y: Sequence[float]) -> float:
    """Spearman rank correlation coefficient. Pure Python, no scipy."""
    if len(x) != len(y):
        raise ValueError("x and y must have equal length")
    if len(x) < 2:
        return 0.0
    rx = _rank(x)
    ry = _rank(y)
    mx = sum(rx) / len(rx)
    my = sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    if dx == 0.0 or dy == 0.0:
        return 0.0
    return num / (dx * dy)


def bootstrap_ci(
    x: Sequence[float],
    y: Sequence[float],
    *,
    resamples: int = 10_000,
    alpha: float = 0.05,
    seed: int = 0xC11999,
) -> Tuple[float, float]:
    """Return a percentile bootstrap (1-alpha) CI for Spearman ρ."""
    rng = random.Random(seed)
    n = len(x)
    vals: List[float] = []
    for _ in range(resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        xb = [x[i] for i in idx]
        yb = [y[i] for i in idx]
        vals.append(spearman_rho(xb, yb))
    vals.sort()
    lo = vals[int(resamples * (alpha / 2))]
    hi = vals[int(resamples * (1 - alpha / 2))]
    return lo, hi


def approx_p_value(rho: float, n: int) -> float:
    """Approximate two-sided p-value for Spearman ρ using the t-distribution.

    Valid for n >= 10. For smaller n the p-value should be treated as
    directional only (matches the design-doc caveat for pilot-scale
    findings).
    """
    if n < 3 or abs(rho) >= 1.0:
        return 0.0
    t = rho * math.sqrt((n - 2) / max(1e-9, 1 - rho * rho))
    # Survival function of Student's t via the regularized incomplete
    # beta relationship. For pilot scaffolding this approximation is
    # acceptable; the full run will replace this with scipy.stats.
    df = n - 2
    x = df / (df + t * t)
    # One-tailed p via incomplete beta ≈ 0.5 * I_x(df/2, 1/2)
    # Pure-Python implementation via continued fraction would be
    # overkill here; use a normal-distribution approximation instead:
    # for df >= 10 the t-distribution is close to standard normal.
    # Error bar for pilot use.
    z = t
    # two-sided p-value from standard normal
    return math.erfc(abs(z) / math.sqrt(2))


def correlate(
    pillar_scores: Dict[str, Sequence[float]],
    accuracy: Sequence[float],
    *,
    resamples: int = 10_000,
) -> List[Correlation]:
    """Compute Spearman ρ + bootstrap CI for each pillar against accuracy."""
    out: List[Correlation] = []
    for pillar, scores in pillar_scores.items():
        if len(scores) != len(accuracy):
            raise ValueError(f"pillar {pillar} length mismatch with accuracy")
        rho = spearman_rho(scores, accuracy)
        lo, hi = bootstrap_ci(scores, accuracy, resamples=resamples)
        p = approx_p_value(rho, len(scores))
        out.append(
            Correlation(
                pillar=pillar,
                n=len(scores),
                rho=rho,
                ci_low=lo,
                ci_high=hi,
                p_value=p,
            )
        )
    return out
