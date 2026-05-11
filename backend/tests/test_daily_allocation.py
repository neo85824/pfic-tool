"""Tests for §1291(a)(1)(A) ratable daily allocation."""
import pytest
from datetime import date
from decimal import Decimal

from pfic_engine.section_1291.daily_allocation import (
    allocate_excess_distribution,
    classify_year,
    aggregate_by_classification,
    DayClassification,
    FIRST_PFIC_YEAR,
)
from pfic_engine.core.date_utils import holding_days
from tests.fixtures.known_cases import PRE_PFIC_YEARS


def D(s):
    return Decimal(str(s))


# ── Year classification ──────────────────────────────────────────────────────

def test_classify_pre_pfic():
    assert classify_year(1985, 1990) == DayClassification.PRE_PFIC
    assert classify_year(1986, 1990) == DayClassification.PRE_PFIC


def test_classify_current_year():
    assert classify_year(2022, 2022) == DayClassification.CURRENT_YEAR


def test_classify_prior_pfic():
    assert classify_year(1987, 2022) == DayClassification.PRIOR_PFIC
    assert classify_year(2021, 2022) == DayClassification.PRIOR_PFIC


def test_first_pfic_year_is_prior_not_pre():
    # 1987 should be prior_pfic (not pre_pfic) when current year > 1987
    assert classify_year(FIRST_PFIC_YEAR, 2000) == DayClassification.PRIOR_PFIC


# ── Allocation arithmetic ────────────────────────────────────────────────────

def test_allocation_sums_to_excess():
    result = allocate_excess_distribution(
        excess_amount=D("3650.00"),
        acquisition_date=date(2020, 1, 15),
        disposition_date=date(2022, 6, 30),
        current_tax_year=2022,
    )
    bucket_total = sum(D(str(b["amount"])) for b in result["year_buckets"].values())
    assert abs(bucket_total - D("3650.00")) < D("0.01")


def test_allocation_total_days():
    result = allocate_excess_distribution(
        excess_amount=D("1000.00"),
        acquisition_date=date(2021, 1, 1),
        disposition_date=date(2021, 12, 31),
        current_tax_year=2021,
    )
    assert result["total_days"] == 365


def test_allocation_leap_year():
    # 2020 is a leap year (366 days)
    result = allocate_excess_distribution(
        excess_amount=D("1000.00"),
        acquisition_date=date(2020, 1, 1),
        disposition_date=date(2020, 12, 31),
        current_tax_year=2020,
    )
    assert result["total_days"] == 366


def test_pre_pfic_classification():
    f = PRE_PFIC_YEARS
    result = allocate_excess_distribution(
        excess_amount=f["excess_amount"],
        acquisition_date=f["acquisition_date"],
        disposition_date=f["distribution_date"],
        current_tax_year=f["current_tax_year"],
    )
    for year, expected_cls in f["expected_classifications"].items():
        if year in result["year_buckets"]:
            assert result["year_buckets"][year]["classification"] == expected_cls, \
                f"Year {year}: expected {expected_cls}, got {result['year_buckets'][year]['classification']}"


def test_aggregate_by_classification():
    result = allocate_excess_distribution(
        excess_amount=D("3000.00"),
        acquisition_date=date(1985, 1, 1),
        disposition_date=date(1990, 12, 31),
        current_tax_year=1990,
    )
    agg = aggregate_by_classification(result["year_buckets"])
    # 1985–1986 = pre_pfic, 1987–1989 = prior_pfic, 1990 = current_year
    assert DayClassification.PRE_PFIC in agg
    assert DayClassification.PRIOR_PFIC in agg
    assert DayClassification.CURRENT_YEAR in agg
    # All must sum to 3000
    total = sum(agg.values())
    assert abs(total - D("3000.00")) < D("0.02")
