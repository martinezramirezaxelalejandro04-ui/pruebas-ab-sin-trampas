"""The two calculations every A/B test needs: how many visitors, and did B really win."""
from __future__ import annotations

from math import ceil, sqrt
from statistics import NormalDist

NORMAL = NormalDist()


def sample_size(baseline: float, relative_lift: float, alpha: float = 0.05,
                power: float = 0.80) -> int:
    """Visitors needed in EACH variant to detect the lift.

    baseline       current conversion rate, e.g. 0.03 for 3%
    relative_lift  smallest improvement worth detecting, e.g. 0.10 for +10%
    alpha          accepted chance of a false alarm (5% by convention)
    power          chance of detecting the lift if it is real (80% by convention)
    """
    if not 0 < baseline < 1 or relative_lift <= 0:
        raise ValueError("baseline must be between 0 and 1 and relative_lift above 0")
    p1, p2 = baseline, baseline * (1 + relative_lift)
    if p2 >= 1:
        raise ValueError("the lift pushes the conversion rate above 100%")
    average = (p1 + p2) / 2
    z_alpha = NORMAL.inv_cdf(1 - alpha / 2)
    z_power = NORMAL.inv_cdf(power)
    numerator = (z_alpha * sqrt(2 * average * (1 - average))
                 + z_power * sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    return ceil(numerator / (p2 - p1) ** 2)


def compare(conversions_a: int, visitors_a: int, conversions_b: int, visitors_b: int,
            alpha: float = 0.05) -> dict:
    """Two-sided test for the difference between two conversion rates."""
    rate_a, rate_b = conversions_a / visitors_a, conversions_b / visitors_b
    pooled = (conversions_a + conversions_b) / (visitors_a + visitors_b)
    pooled_error = sqrt(pooled * (1 - pooled) * (1 / visitors_a + 1 / visitors_b))
    z = (rate_b - rate_a) / pooled_error if pooled_error else 0.0
    p_value = 2 * (1 - NORMAL.cdf(abs(z)))

    # Plausible range for the true difference (uses each variant's own variability).
    error = sqrt(rate_a * (1 - rate_a) / visitors_a + rate_b * (1 - rate_b) / visitors_b)
    margin = NORMAL.inv_cdf(1 - alpha / 2) * error
    difference = rate_b - rate_a
    return {
        "rate_a": rate_a,
        "rate_b": rate_b,
        "relative_lift": difference / rate_a if rate_a else float("nan"),
        "p_value": p_value,
        "significant": p_value < alpha,
        "difference_low": difference - margin,
        "difference_high": difference + margin,
    }
