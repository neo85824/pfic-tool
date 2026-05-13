"""Tests for §6621 rate table, max tax rates, and filing deadlines."""
import pytest
from datetime import date
from decimal import Decimal

from pfic_engine.core.tax_constants import (
    get_6621_rate,
    get_max_tax_rate,
    get_filing_deadline,
    IRS_6621_RATES,
    quarter_for_date,
)


def test_rate_table_has_158_entries():
    assert len(IRS_6621_RATES) == 158


def test_rate_table_starts_1987_q1():
    assert IRS_6621_RATES[0].year == 1987
    assert IRS_6621_RATES[0].quarter == 1


def test_rate_table_ends_2026_q2():
    last = IRS_6621_RATES[-1]
    assert last.year == 2026
    assert last.quarter == 2


def test_rate_lookup_known_values():
    # Low-rate era: 2022 Q1 = 3%
    assert get_6621_rate(2022, 1) == Decimal("0.03")
    # Post-hike: 2023 Q4 = 8%
    assert get_6621_rate(2023, 4) == Decimal("0.08")
    # COVID era: 2020 Q2 = 3%
    assert get_6621_rate(2020, 2) == Decimal("0.03")
    # High-rate era: 1989 Q2 = 12%
    assert get_6621_rate(1989, 2) == Decimal("0.12")


def test_rate_lookup_missing_raises():
    with pytest.raises(ValueError, match="No §6621 rate"):
        get_6621_rate(2030, 1)


def test_max_tax_rates():
    assert get_max_tax_rate(1987) == Decimal("0.386")
    assert get_max_tax_rate(1993) == Decimal("0.396")
    assert get_max_tax_rate(2018) == Decimal("0.370")
    assert get_max_tax_rate(2025) == Decimal("0.370")


def test_max_tax_rate_missing_raises():
    with pytest.raises(ValueError):
        get_max_tax_rate(1800)


def test_filing_deadline_normal():
    assert get_filing_deadline(2018) == date(2019, 4, 15)
    assert get_filing_deadline(2023) == date(2024, 4, 15)


def test_filing_deadline_covid_2019():
    assert get_filing_deadline(2019) == date(2020, 7, 15)


def test_filing_deadline_covid_2020():
    assert get_filing_deadline(2020) == date(2021, 5, 17)


def test_filing_deadline_weekend_shifts():
    assert get_filing_deadline(1987) == date(1988, 4, 18)
    assert get_filing_deadline(2021) == date(2022, 4, 18)
    assert get_filing_deadline(2022) == date(2023, 4, 18)


def test_quarter_for_date():
    assert quarter_for_date(date(2022, 1, 1)) == 1
    assert quarter_for_date(date(2022, 3, 31)) == 1
    assert quarter_for_date(date(2022, 4, 1)) == 2
    assert quarter_for_date(date(2022, 6, 30)) == 2
    assert quarter_for_date(date(2022, 7, 1)) == 3
    assert quarter_for_date(date(2022, 9, 30)) == 3
    assert quarter_for_date(date(2022, 10, 1)) == 4
    assert quarter_for_date(date(2022, 12, 31)) == 4
