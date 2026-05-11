"""
§1291 Excess Distribution determination and 125% test.

IRC §1291(b)(2)(A): a distribution is an "excess distribution" if it exceeds
125% of the average distributions received during the preceding 3 years
(or the taxpayer's holding period, if shorter).

IRC §1291(a)(2): on disposition, the entire gain is treated as an excess distribution.
"""
from decimal import Decimal

from pfic_engine.core.decimal_utils import to_decimal, safe_divide, round_cents

THRESHOLD = Decimal("1.25")  # 125%


def compute_prior_3yr_average(
    distributions: list[Decimal],
    holding_years: int,
) -> Decimal:
    """
    IRC §1291(b)(2)(B): if taxpayer held the stock fewer than 3 years,
    divide total prior distributions by the actual number of prior holding years.

    distributions: list of annual distributions (oldest first), up to 3 years.
    holding_years: total years held prior to the current year.
    """
    if holding_years <= 0 or not distributions:
        return Decimal("0")

    denominator = min(holding_years, 3)
    total = sum(to_decimal(d) for d in distributions[-3:])
    return safe_divide(total, Decimal(str(denominator)))


def compute_excess_amount(
    distribution: Decimal,
    prior_3yr_avg: Decimal,
) -> Decimal:
    """
    The excess portion = distribution - 125% * prior_avg.
    Returns 0 if distribution does not exceed the threshold.
    """
    distribution = to_decimal(distribution)
    prior_3yr_avg = to_decimal(prior_3yr_avg)

    threshold_amount = prior_3yr_avg * THRESHOLD
    excess = distribution - threshold_amount
    return max(excess, Decimal("0"))


def is_excess_distribution(
    distribution: Decimal,
    prior_3yr_avg: Decimal,
) -> bool:
    """IRC §1291(b)(2)(A): True if distribution exceeds 125% of prior 3-year average."""
    return compute_excess_amount(distribution, prior_3yr_avg) > Decimal("0")


def split_distribution(
    distribution: Decimal,
    prior_3yr_avg: Decimal,
) -> tuple[Decimal, Decimal]:
    """
    Split a distribution into (non_excess, excess) portions.
    non_excess is taxed as ordinary income in the current year.
    excess triggers the §1291 ratable allocation regime.
    """
    distribution = to_decimal(distribution)
    excess = compute_excess_amount(distribution, prior_3yr_avg)
    non_excess = distribution - excess
    return round_cents(non_excess), round_cents(excess)
