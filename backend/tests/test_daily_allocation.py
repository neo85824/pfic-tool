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
    assert result["total_days"] == 364


def test_allocation_leap_year():
    # 2020 is a leap year; distribution date excluded → (12/31 − 1/1).days = 365
    result = allocate_excess_distribution(
        excess_amount=D("1000.00"),
        acquisition_date=date(2020, 1, 1),
        disposition_date=date(2020, 12, 31),
        current_tax_year=2020,
    )
    assert result["total_days"] == 365


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


# ── TC-MAIN L1 spot-check ────────────────────────────────────────────────────

def test_tc_main_l1_day_allocation():
    result = allocate_excess_distribution(
        excess_amount=D("581.41"),
        acquisition_date=date(2021, 9, 6),
        disposition_date=date(2022, 12, 31),
        current_tax_year=2022,
    )
    assert result["total_days"] == 481
    assert result["year_buckets"][2021]["days"] == 117
    assert result["year_buckets"][2022]["days"] == 364
    assert abs(result["year_buckets"][2021]["amount"] - D("141.42")) < D("0.01")
    assert abs(result["year_buckets"][2022]["amount"] - D("439.99")) < D("0.01")


# ── TC-04: Same-year purchase + distribution ──────────────────────────────────

def test_tc04_same_year_all_current():
    result = allocate_excess_distribution(
        excess_amount=D("500.00"),
        acquisition_date=date(2022, 3, 1),
        disposition_date=date(2022, 12, 31),
        current_tax_year=2022,
    )
    for bucket in result["year_buckets"].values():
        assert bucket["classification"] == DayClassification.CURRENT_YEAR
    assert DayClassification.PRIOR_PFIC not in {
        b["classification"] for b in result["year_buckets"].values()
    }


# ── TC-05: Leap year day count (2024) ────────────────────────────────────────

def test_tc05_leap_year_day_buckets():
    result = allocate_excess_distribution(
        excess_amount=D("10000.00"),
        acquisition_date=date(2022, 1, 1),
        disposition_date=date(2024, 12, 31),
        current_tax_year=2024,
    )
    assert result["total_days"] == 1095
    assert result["year_buckets"][2022]["days"] == 365
    assert result["year_buckets"][2023]["days"] == 365
    assert result["year_buckets"][2024]["days"] == 365  # 2024 is leap but Dec 31 excluded
    assert sum(b["days"] for b in result["year_buckets"].values()) == 1095


# ── TC-06: Pre-PFIC boundary ─────────────────────────────────────────────────

def test_tc06_pre_pfic_boundary():
    result = allocate_excess_distribution(
        excess_amount=D("10000.00"),
        acquisition_date=date(1985, 1, 1),
        disposition_date=date(2022, 12, 31),
        current_tax_year=2022,
    )
    assert result["year_buckets"][1985]["classification"] == DayClassification.PRE_PFIC
    assert result["year_buckets"][1986]["classification"] == DayClassification.PRE_PFIC
    assert result["year_buckets"][1987]["classification"] == DayClassification.PRIOR_PFIC
    assert result["year_buckets"][2022]["classification"] == DayClassification.CURRENT_YEAR
    assert result["year_buckets"][1985]["days"] == 365
    assert result["year_buckets"][1986]["days"] == 365


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
