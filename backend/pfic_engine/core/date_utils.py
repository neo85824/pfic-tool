"""
Date helpers for PFIC calculations.
Handles §7503 holiday/weekend shifts and holding-period edge cases.
"""
import calendar
from datetime import date, timedelta

from pfic_engine.core.tax_constants import get_filing_deadline


# Federal holidays that can shift a filing deadline (simplified — only Patriots Day
# in Massachusetts/Maine matters for IRS in practice for April deadlines).
# §7503 shifts only when the due date falls on a Saturday, Sunday, or legal holiday.


def is_weekend(d: date) -> bool:
    return d.weekday() >= 5  # 5=Saturday, 6=Sunday


def days_in_year(year: int) -> int:
    """Return 365 or 366 for leap years."""
    return 366 if calendar.isleap(year) else 365


def holding_days(acquisition_date: date, disposition_date: date) -> int:
    """
    Number of days in a PFIC holding period.
    Includes both the acquisition date and disposition date per §1291 conventions.
    """
    return (disposition_date - acquisition_date).days + 1


def calendar_year_days_in_range(start: date, end: date) -> dict[int, int]:
    """
    Break a date range into {year: day_count} segments.
    Used to attribute holding days to each tax year.
    """
    if start > end:
        return {}
    result: dict[int, int] = {}
    current = start
    while current <= end:
        year = current.year
        year_end = min(date(year, 12, 31), end)
        count = (year_end - current).days + 1
        result[year] = result.get(year, 0) + count
        current = date(year + 1, 1, 1)
    return result


def interest_start_date(tax_year: int) -> date:
    """
    IRC §1291(c)(3)(A): interest accrues from the due date of the return for
    the year in which the income was allocated (i.e., the tax year's filing deadline).
    """
    return get_filing_deadline(tax_year)


def interest_end_date(current_tax_year: int) -> date:
    """
    IRC §1291(c)(3)(A): interest accrues through the due date of the current
    year's return (the year in which the excess distribution is received).
    """
    return get_filing_deadline(current_tax_year)
