"""
§1291 ratable daily allocation of excess distributions.

IRC §1291(a)(1)(A): The amount of any excess distribution shall be allocated
ratably to each day in the taxpayer's holding period for the stock.

Form 8621 Instructions (Rev. 12/2025), Line 16a:
"Divide the amount on line 15e(2) or 15f by the number of days in your holding period."
"""
from decimal import Decimal
from datetime import date

from datetime import timedelta

from pfic_engine.core.decimal_utils import to_decimal, safe_divide
from pfic_engine.core.date_utils import calendar_year_days_in_range

FIRST_PFIC_YEAR = 1987  # IRC §1291 does not apply before 1987


class DayClassification:
    PRE_PFIC = "pre_pfic"         # Before 1987 — taxed as ordinary income
    PRIOR_PFIC = "prior_pfic"     # 1987+, before the current tax year — deferred + interest
    CURRENT_YEAR = "current_year" # Current tax year — taxed as ordinary income


def classify_year(year: int, current_tax_year: int) -> str:
    """
    IRC §1291(a)(1)(B): days in pre-PFIC years and in the current year
    are included in current-year ordinary income (not subject to interest).
    Days in prior PFIC years bear deferred tax + interest.
    """
    if year < FIRST_PFIC_YEAR:
        return DayClassification.PRE_PFIC
    if year == current_tax_year:
        return DayClassification.CURRENT_YEAR
    return DayClassification.PRIOR_PFIC


def allocate_excess_distribution(
    excess_amount: Decimal,
    acquisition_date: date,
    disposition_date: date,
    current_tax_year: int,
) -> dict:
    """
    Allocate excess_amount ratably across each day of the holding period,
    then group by year with classification.

    Returns:
    {
        "daily_amount": Decimal,           # per-day allocation
        "total_days": int,
        "year_buckets": {
            year: {
                "days": int,
                "amount": Decimal,
                "classification": str,
            }
        }
    }
    """
    excess_amount = to_decimal(excess_amount)
    # Holding days = distribution_date − purchase_date (distribution date excluded)
    total_days = (disposition_date - acquisition_date).days
    daily_amount = safe_divide(excess_amount, Decimal(str(total_days)))

    # Exclude the distribution date itself from year buckets
    year_days = calendar_year_days_in_range(acquisition_date, disposition_date - timedelta(days=1))
    year_buckets: dict[int, dict] = {}

    running_total = Decimal("0")
    years = sorted(year_days.keys())

    for i, year in enumerate(years):
        days = year_days[year]
        if i < len(years) - 1:
            amount = daily_amount * Decimal(str(days))
        else:
            # Last year: remainder prevents rounding drift
            amount = excess_amount - running_total

        running_total += amount
        year_buckets[year] = {
            "days": days,
            "amount": amount,
            "classification": classify_year(year, current_tax_year),
        }

    return {
        "daily_amount": daily_amount,
        "total_days": total_days,
        "year_buckets": year_buckets,
    }


def aggregate_by_classification(year_buckets: dict) -> dict[str, Decimal]:
    """
    Sum allocated amounts by classification for Form 8621 Line 16b/16c reporting.

    Returns: {classification: total_amount}
    """
    totals: dict[str, Decimal] = {}
    for bucket in year_buckets.values():
        cls = bucket["classification"]
        totals[cls] = totals.get(cls, Decimal("0")) + bucket["amount"]
    return totals
