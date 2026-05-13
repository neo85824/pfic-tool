"""Tests for static IRS lookup tables: §6621 rates, max tax rates, filing deadlines."""
from datetime import date
from decimal import Decimal

import pytest

from pfic_engine.core.tax_constants import (
    get_6621_rate,
    get_max_tax_rate,
    get_filing_deadline,
)


def D(s):
    return Decimal(str(s))


# ── TC-01: §7503 weekend shift ───────────────────────────────────────────────

def test_tc01_2021_deadline_not_april_15():
    deadline = get_filing_deadline(2021)
    assert deadline == date(2022, 4, 18)
    assert deadline != date(2022, 4, 15)


# ── TC-02: COVID 2019 extension ──────────────────────────────────────────────

def test_tc02_2019_covid_deadline():
    assert get_filing_deadline(2019) == date(2020, 7, 15)


def test_covid_2020_deadline():
    assert get_filing_deadline(2020) == date(2021, 5, 17)


# ── §6621 rate spot-checks ───────────────────────────────────────────────────

def test_6621_rates_2022():
    assert get_6621_rate(2022, 1) == D("0.03")
    assert get_6621_rate(2022, 2) == D("0.04")
    assert get_6621_rate(2022, 3) == D("0.05")
    assert get_6621_rate(2022, 4) == D("0.06")


def test_6621_rates_2023():
    assert get_6621_rate(2023, 1) == D("0.07")
    assert get_6621_rate(2023, 2) == D("0.07")
    assert get_6621_rate(2023, 3) == D("0.07")
    assert get_6621_rate(2023, 4) == D("0.08")


def test_6621_rates_2026_includes_q2():
    assert get_6621_rate(2026, 1) == D("0.07")
    assert get_6621_rate(2026, 2) == D("0.06")


def test_6621_rates_2019():
    assert get_6621_rate(2019, 1) == D("0.06")
    assert get_6621_rate(2019, 2) == D("0.06")
    assert get_6621_rate(2019, 3) == D("0.05")
    assert get_6621_rate(2019, 4) == D("0.05")


def test_6621_rates_2020_covid():
    assert get_6621_rate(2020, 1) == D("0.05")
    assert get_6621_rate(2020, 2) == D("0.03")
    assert get_6621_rate(2020, 3) == D("0.03")
    assert get_6621_rate(2020, 4) == D("0.03")


def test_6621_rates_2021():
    for q in (1, 2, 3, 4):
        assert get_6621_rate(2021, q) == D("0.03")


def test_6621_rates_2024():
    for q in (1, 2, 3, 4):
        assert get_6621_rate(2024, q) == D("0.08")


def test_6621_rates_2025():
    for q in (1, 2, 3, 4):
        assert get_6621_rate(2025, q) == D("0.07")


# ── Max tax rate spot-checks ─────────────────────────────────────────────────

def test_max_tax_rates():
    assert get_max_tax_rate(2021) == D("0.370")
    assert get_max_tax_rate(2022) == D("0.370")
    assert get_max_tax_rate(2019) == D("0.370")
    assert get_max_tax_rate(2020) == D("0.370")
