"""Tests for §6622 daily compound interest calculation."""
import pytest
from datetime import date
from decimal import Decimal

from pfic_engine.section_1291.interest import (
    calculate_daily_compound_interest,
    get_rate_periods,
    calculate_interest_for_year_bucket,
)
from tests.fixtures.known_cases import (
    COVID_YEAR_2019,
    COVID_YEAR_2020,
    INTEREST_SINGLE_QUARTER,
)


def D(s):
    return Decimal(str(s))


# ── Rate period segmentation ─────────────────────────────────────────────────

def test_single_quarter_one_period():
    periods = get_rate_periods(date(2022, 1, 1), date(2022, 3, 31))
    assert len(periods) == 1
    assert periods[0].annual_rate == D("0.03")
    assert periods[0].days == 90


def test_two_quarters_two_periods():
    periods = get_rate_periods(date(2022, 3, 1), date(2022, 5, 31))
    assert len(periods) == 2
    assert periods[0].annual_rate == D("0.03")  # Q1
    assert periods[1].annual_rate == D("0.04")  # Q2


def test_cross_year_periods():
    # 2022 Q4 → 2023 Q1
    periods = get_rate_periods(date(2022, 10, 1), date(2023, 3, 31))
    assert len(periods) == 2
    assert periods[0].annual_rate == D("0.06")  # 2022 Q4
    assert periods[1].annual_rate == D("0.07")  # 2023 Q1


def test_periods_day_count_adds_up():
    start = date(2022, 1, 1)
    end = date(2022, 12, 31)
    periods = get_rate_periods(start, end)
    total_days = sum(p.days for p in periods)
    assert total_days == 365


# ── Interest arithmetic ──────────────────────────────────────────────────────

def test_interest_single_quarter_approx():
    f = INTEREST_SINGLE_QUARTER
    interest = calculate_daily_compound_interest(f["principal"], f["start"], f["end"])
    diff = abs(interest - f["expected_interest_approx"])
    assert diff <= f["tolerance"], f"Expected ~{f['expected_interest_approx']}, got {interest}"


def test_interest_zero_days():
    interest = calculate_daily_compound_interest(D("1000"), date(2022, 4, 15), date(2022, 4, 14))
    assert interest == D("0")


def test_interest_zero_principal():
    interest = calculate_daily_compound_interest(D("0"), date(2022, 1, 1), date(2022, 12, 31))
    assert interest == D("0")


def test_interest_is_positive():
    interest = calculate_daily_compound_interest(D("5000"), date(2021, 5, 17), date(2024, 4, 15))
    assert interest > D("0")


def test_interest_for_year_bucket_no_span():
    # start == end → no interest
    d = date(2022, 4, 15)
    interest = calculate_interest_for_year_bucket(D("1000"), d, d)
    assert interest == D("0")


# ── COVID deadline integration ───────────────────────────────────────────────

def test_covid_2019_deadline_used_in_interest():
    """
    2019 allocation: interest starts 2020-07-15 (COVID), not 2020-04-15.
    If we compute interest starting 2020-07-15 vs 2020-04-15, the COVID case
    should give a *lower* interest amount (fewer days).
    """
    from pfic_engine.core.tax_constants import get_filing_deadline
    deadline_2019 = get_filing_deadline(2019)
    assert deadline_2019 == date(2020, 7, 15)

    # Interest from COVID deadline vs normal deadline, through 2023 deadline
    normal_start = date(2020, 4, 15)
    covid_start = date(2020, 7, 15)
    end = date(2023, 4, 18)

    interest_normal = calculate_daily_compound_interest(D("1000"), normal_start, end)
    interest_covid = calculate_daily_compound_interest(D("1000"), covid_start, end)

    assert interest_covid < interest_normal  # COVID extension → fewer interest days


def test_covid_2020_deadline():
    from pfic_engine.core.tax_constants import get_filing_deadline
    assert get_filing_deadline(2020) == date(2021, 5, 17)
