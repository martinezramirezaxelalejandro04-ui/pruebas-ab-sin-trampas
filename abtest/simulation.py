"""Simulate thousands of A/B tests to show two traps that the formulas hide.

Trap 1, peeking: checking a running test every day and stopping the first time
it looks significant. Simulated with variants that are IDENTICAL, so every
"winner" is a false alarm.

Trap 2, exaggerated winners: stopping a test with too few visitors. The few
tests that reach significance do so because luck inflated the result.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .stats import NORMAL, sample_size

Z_CRITICAL = NORMAL.inv_cdf(0.975)  # two-sided 5%


def _z_scores(conversions_a, conversions_b, visitors):
    """z statistic for equal-sized variants; arrays broadcast together."""
    pooled = (conversions_a + conversions_b) / (2 * visitors)
    error = np.sqrt(pooled * (1 - pooled) * 2 / visitors)
    with np.errstate(divide="ignore", invalid="ignore"):
        z = (conversions_b - conversions_a) / visitors / error
    return np.nan_to_num(z)


def peeking(rate: float = 0.03, visitors_per_day: int = 500, days: int = 28,
            simulations: int = 20000, seed: int = 7) -> pd.DataFrame:
    """False-alarm rate of an A/A test under three ways of looking at it."""
    rng = np.random.default_rng(seed)
    a = rng.binomial(visitors_per_day, rate, size=(simulations, days)).cumsum(axis=1)
    b = rng.binomial(visitors_per_day, rate, size=(simulations, days)).cumsum(axis=1)
    visitors = visitors_per_day * np.arange(1, days + 1)
    significant = np.abs(_z_scores(a, b, visitors)) > Z_CRITICAL  # simulations x days

    schedules = {
        "Solo al final": [days - 1],
        "Cada semana": list(range(6, days, 7)),
        "Cada día": list(range(days)),
    }
    return pd.DataFrame([
        {"schedule": name, "looks": len(day_indexes),
         "false_alarm_pct": round(100 * significant[:, day_indexes].any(axis=1).mean(), 1)}
        for name, day_indexes in schedules.items()
    ])


def exaggerated_winners(baseline: float = 0.03, true_lift: float = 0.10,
                        simulations: int = 200000, seed: int = 7) -> pd.DataFrame:
    """What "winning" tests report when run with a fraction of the visitors they need."""
    rng = np.random.default_rng(seed)
    needed = sample_size(baseline, true_lift)
    rows = []
    for share in (0.10, 0.25, 0.50, 1.00):
        visitors = int(needed * share)
        a = rng.binomial(visitors, baseline, size=simulations)
        b = rng.binomial(visitors, baseline * (1 + true_lift), size=simulations)
        wins = _z_scores(a, b, visitors) > Z_CRITICAL
        reported_lift = (b[wins] - a[wins]) / a[wins]
        rows.append({
            "share_of_needed_visitors_pct": int(share * 100),
            "visitors_per_variant": visitors,
            "tests_that_detect_it_pct": round(100 * wins.mean(), 1),
            "true_lift_pct": round(100 * true_lift, 1),
            "lift_reported_by_winners_pct": round(100 * float(np.median(reported_lift)), 1),
        })
    return pd.DataFrame(rows)
