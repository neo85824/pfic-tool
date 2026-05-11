"""
§6621 + §6622 interest calculation for PFIC excess distributions.

IRC §6622: interest is compounded daily.
IRC §6621(a)(2): underpayment rate = federal short-term rate + 3%.
IRC §1291(c)(3)(A): interest accrues from the due date of the year-of-allocation
    return through the due date of the current-year return.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, getcontext

from pfic_engine.core.decimal_utils import to_decimal
from pfic_engine.core.tax_constants import get_6621_rate, quarter_for_date

getcontext().prec = 28

ONE = Decimal("1")
DAYS_PER_YEAR = Decimal("365")


@dataclass
class RatePeriod:
    """A contiguous period during which the §6621 rate is constant."""
    start: date
    end: date
    annual_rate: Decimal
    days: int


def get_rate_periods(start: date, end: date) -> list[RatePeriod]:
    """
    Break [start, end] into sub-periods where the §6621 rate is constant.
    The rate changes on the first day of each calendar quarter.
    """
    if start > end:
        return []

    periods: list[RatePeriod] = []
    current = start

    while current <= end:
        year = current.year
        quarter = quarter_for_date(current)
        annual_rate = get_6621_rate(year, quarter)

        # Find the last day of this quarter
        quarter_end_month = quarter * 3
        last_day_of_quarter_month = (
            30 if quarter_end_month in (4, 6, 9, 11)
            else 28 if quarter_end_month == 2
            else 31
        )
        # Feb adjustment for leap year (edge case — quarters don't end in Feb)
        quarter_end = date(year, quarter_end_month, last_day_of_quarter_month)
        period_end = min(quarter_end, end)

        days = (period_end - current).days + 1
        periods.append(RatePeriod(
            start=current,
            end=period_end,
            annual_rate=annual_rate,
            days=days,
        ))
        current = period_end + timedelta(days=1)

    return periods


def calculate_daily_compound_interest(
    principal: Decimal,
    start: date,
    end: date,
) -> Decimal:
    """
    IRC §6622: compute interest by daily compounding over [start, end].

    Formula: interest = principal * (∏(1 + r/365)^days_in_period - 1)
    where r is the §6621 annual rate for each period.

    Returns the interest amount (not including principal).
    """
    principal = to_decimal(principal)
    if principal <= Decimal("0") or start > end:
        return Decimal("0")

    periods = get_rate_periods(start, end)
    compound_factor = ONE

    for p in periods:
        daily_rate = p.annual_rate / DAYS_PER_YEAR
        period_factor = (ONE + daily_rate) ** p.days
        compound_factor *= period_factor

    interest = principal * (compound_factor - ONE)
    return interest


def calculate_interest_for_year_bucket(
    allocated_tax: Decimal,
    interest_start: date,
    interest_end: date,
) -> Decimal:
    """
    Compute §6622 daily-compounded interest on one year's deferred tax.

    IRC §1291(c)(1): deferred tax amount = tax + interest on that tax.
    interest_start: filing deadline for the allocation year (§1291(c)(3)(A))
    interest_end:   filing deadline for the distribution year
    """
    if interest_start >= interest_end:
        return Decimal("0")
    return calculate_daily_compound_interest(allocated_tax, interest_start, interest_end)


def build_interest_detail(
    year: int,
    allocated_tax: Decimal,
    interest_start: date,
    interest_end: date,
) -> dict:
    """
    Return a structured record of the interest calculation for audit / Line 16f.
    """
    periods = get_rate_periods(interest_start, interest_end)
    interest = calculate_interest_for_year_bucket(allocated_tax, interest_start, interest_end)

    return {
        "year": year,
        "allocated_tax": str(allocated_tax),
        "interest_start": interest_start.isoformat(),
        "interest_end": interest_end.isoformat(),
        "interest_rate_periods": [
            {
                "from": p.start.isoformat(),
                "to": p.end.isoformat(),
                "annual_rate": str(p.annual_rate),
                "days": p.days,
            }
            for p in periods
        ],
        "interest": str(interest),
    }
