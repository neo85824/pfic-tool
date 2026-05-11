"""Tests for per-year deferred tax + interest computation."""
import pytest
from datetime import date
from decimal import Decimal

from pfic_engine.section_1291.deferred_tax import (
    compute_year_tax,
    compute_deferred_tax_with_interest,
)
from pfic_engine.section_1291.daily_allocation import (
    allocate_excess_distribution,
    DayClassification,
)


def D(s):
    return Decimal(str(s))


def test_compute_year_tax_2018_rate():
    # 2018 max rate = 37%
    tax = compute_year_tax(2018, D("10000"))
    assert tax == D("3700")


def test_compute_year_tax_1993_rate():
    # 1993-2000 max rate = 39.6%
    tax = compute_year_tax(1995, D("1000"))
    assert tax == D("396.0")


def test_deferred_tax_prior_years_only():
    """Prior PFIC years get deferred tax + interest; current year does not."""
    year_buckets = {
        2020: {"amount": D("2000"), "classification": DayClassification.PRIOR_PFIC},
        2021: {"amount": D("1500"), "classification": DayClassification.PRIOR_PFIC},
        2022: {"amount": D("500"),  "classification": DayClassification.CURRENT_YEAR},
    }
    result = compute_deferred_tax_with_interest(year_buckets, current_tax_year=2022)

    assert result["year_results"][2020]["tax"] is not None
    assert result["year_results"][2021]["tax"] is not None
    assert result["year_results"][2022]["tax"] is None  # current year — no deferred tax

    assert D(result["total_deferred_tax"]) > D("0")
    assert D(result["total_interest"]) > D("0")


def test_deferred_tax_grand_total():
    year_buckets = {
        2021: {"amount": D("5000"), "classification": DayClassification.PRIOR_PFIC},
        2022: {"amount": D("1000"), "classification": DayClassification.CURRENT_YEAR},
    }
    result = compute_deferred_tax_with_interest(year_buckets, current_tax_year=2022)

    tax = D(result["total_deferred_tax"])
    interest = D(result["total_interest"])
    grand = D(result["grand_total"])
    assert abs((tax + interest) - grand) < D("0.02")


def test_deferred_tax_pre_pfic_no_tax():
    year_buckets = {
        1985: {"amount": D("3000"), "classification": DayClassification.PRE_PFIC},
        1990: {"amount": D("2000"), "classification": DayClassification.CURRENT_YEAR},
    }
    result = compute_deferred_tax_with_interest(year_buckets, current_tax_year=1990)
    assert result["year_results"][1985]["tax"] is None
    assert D(result["total_deferred_tax"]) == D("0")


def test_ordinary_income_captured():
    year_buckets = {
        2019: {"amount": D("1000"), "classification": DayClassification.PRIOR_PFIC},
        2020: {"amount": D("500"),  "classification": DayClassification.CURRENT_YEAR},
    }
    result = compute_deferred_tax_with_interest(year_buckets, current_tax_year=2020)
    assert D(result["ordinary_income"]) == D("500")


def test_covid_interest_start_2020():
    """
    2019 allocation year: interest must start 2020-07-15 (COVID), not 2020-04-15.
    Verify that the interest_detail reflects the COVID deadline.
    """
    year_buckets = {
        2019: {"amount": D("10000"), "classification": DayClassification.PRIOR_PFIC},
    }
    result = compute_deferred_tax_with_interest(year_buckets, current_tax_year=2023)
    interest_start = result["year_results"][2019]["interest_start"]
    assert interest_start == "2020-07-15"
