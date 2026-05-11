"""
Per-year deferred tax computation under §1291.

IRC §1291(c)(2): each prior PFIC year's allocated amount is taxed at the
highest applicable marginal rate for that year (not the current year's rate).
IRC §1291(c)(1): deferred tax amount = tax + §6622 interest on that tax.
"""
from decimal import Decimal
from datetime import date

from pfic_engine.core.decimal_utils import to_decimal, round_cents
from pfic_engine.core.tax_constants import get_max_tax_rate, get_filing_deadline
from pfic_engine.core.date_utils import interest_start_date, interest_end_date
from pfic_engine.section_1291.daily_allocation import DayClassification
from pfic_engine.section_1291.interest import (
    calculate_interest_for_year_bucket,
    build_interest_detail,
)


def compute_year_tax(year: int, allocated_amount: Decimal) -> Decimal:
    """
    IRC §1291(c)(2): tax = allocated_amount * max_rate_for_that_year.
    """
    allocated_amount = to_decimal(allocated_amount)
    rate = get_max_tax_rate(year)
    return allocated_amount * rate


def compute_deferred_tax_with_interest(
    year_buckets: dict,
    current_tax_year: int,
) -> dict:
    """
    For every prior-PFIC year bucket, compute:
      - allocated tax at historical max rate
      - §6622 daily-compounded interest from that year's due date
        to the current year's due date

    Pre-PFIC and current-year amounts are passed through as ordinary income
    (no deferred tax, no interest).

    Returns full detail dict for audit trail and Form 8621 Part V output.
    """
    current_deadline = get_filing_deadline(current_tax_year)
    results = {}
    total_deferred_tax = Decimal("0")
    total_interest = Decimal("0")
    ordinary_income = Decimal("0")

    for year, bucket in sorted(year_buckets.items()):
        cls = bucket["classification"]
        amount = to_decimal(bucket["amount"])

        if cls in (DayClassification.PRE_PFIC, DayClassification.CURRENT_YEAR):
            ordinary_income += amount
            results[year] = {
                "year": year,
                "classification": cls,
                "allocated_amount": str(amount),
                "tax": None,
                "interest": None,
                "interest_detail": None,
            }
            continue

        # Prior PFIC year — compute deferred tax + interest
        tax = compute_year_tax(year, amount)
        i_start = interest_start_date(year)
        i_end = interest_end_date(current_tax_year)
        interest = calculate_interest_for_year_bucket(tax, i_start, i_end)
        detail = build_interest_detail(year, tax, i_start, i_end)

        total_deferred_tax += tax
        total_interest += interest
        results[year] = {
            "year": year,
            "classification": cls,
            "allocated_amount": str(amount),
            "tax": str(tax),
            "interest_start": i_start.isoformat(),
            "interest_end": i_end.isoformat(),
            "interest": str(interest),
            "interest_detail": detail,
        }

    return {
        "year_results": results,
        "ordinary_income": str(ordinary_income),
        "total_deferred_tax": str(total_deferred_tax),
        "total_interest": str(total_interest),
        "grand_total": str(round_cents(total_deferred_tax + total_interest)),
    }
