"""Tests for §1291 125% excess distribution test."""
import pytest
from decimal import Decimal

from pfic_engine.section_1291.excess_dist import (
    compute_prior_3yr_average,
    compute_excess_amount,
    is_excess_distribution,
    split_distribution,
)
from tests.fixtures.known_cases import (
    THRESHOLD_EXACT_125PCT,
    THRESHOLD_ONE_CENT_OVER,
    HOLDING_UNDER_3_YEARS,
    ZERO_PRIOR_DISTRIBUTIONS,
    MULTIPLE_DISTRIBUTIONS_125PCT,
)


def D(s):
    return Decimal(str(s))


# ── Prior average computation ────────────────────────────────────────────────

def test_prior_avg_full_3_years():
    avg = compute_prior_3yr_average(
        [D("800"), D("900"), D("1000")], holding_years=3
    )
    assert avg == D("900")


def test_prior_avg_under_3_years():
    f = HOLDING_UNDER_3_YEARS
    avg = compute_prior_3yr_average(
        f["prior_distributions"], f["holding_years_before"]
    )
    assert avg == f["expected_prior_avg"]


def test_prior_avg_zero_distributions():
    f = ZERO_PRIOR_DISTRIBUTIONS
    avg = compute_prior_3yr_average(
        f["prior_distributions"], f["holding_years_before"]
    )
    assert avg == f["expected_prior_avg"]


def test_prior_avg_uses_only_last_3():
    # Even if 5 years of history provided, only last 3 are used
    avg = compute_prior_3yr_average(
        [D("100"), D("200"), D("800"), D("900"), D("1000")], holding_years=5
    )
    assert avg == D("900")


# ── Excess amount computation ────────────────────────────────────────────────

def test_exact_125pct_not_excess():
    f = THRESHOLD_EXACT_125PCT
    avg = compute_prior_3yr_average(f["prior_distributions"], f["holding_years_before"])
    excess = compute_excess_amount(f["distribution"], avg)
    assert excess == f["expected_excess_amount"]
    assert not is_excess_distribution(f["distribution"], avg)


def test_one_cent_over_is_excess():
    f = THRESHOLD_ONE_CENT_OVER
    avg = compute_prior_3yr_average(f["prior_distributions"], f["holding_years_before"])
    excess = compute_excess_amount(f["distribution"], avg)
    assert excess == f["expected_excess_amount"]
    assert is_excess_distribution(f["distribution"], avg)


def test_excess_with_zero_prior():
    f = ZERO_PRIOR_DISTRIBUTIONS
    avg = compute_prior_3yr_average(f["prior_distributions"], f["holding_years_before"])
    excess = compute_excess_amount(f["distribution"], avg)
    assert excess == f["expected_excess"]


def test_multiple_distributions():
    f = MULTIPLE_DISTRIBUTIONS_125PCT
    avg = compute_prior_3yr_average(f["prior_distributions"], f["holding_years_before"])
    assert avg == f["expected_prior_avg"]
    excess = compute_excess_amount(f["distribution"], avg)
    assert excess == f["expected_excess"]


# ── Split ────────────────────────────────────────────────────────────────────

def test_split_distribution():
    non_excess, excess = split_distribution(D("2000"), D("900"))
    # avg=900, threshold=1125; excess = 875; non_excess = 1125
    assert non_excess == D("1125.00")
    assert excess == D("875.00")
    assert non_excess + excess == D("2000.00")


def test_split_no_excess():
    non_excess, excess = split_distribution(D("1000"), D("900"))
    assert excess == D("0.00")
    assert non_excess == D("1000.00")


# ── TC-07: Zero prior distributions (no ZeroDivisionError) ───────────────────

def test_tc07_zero_prior_distributions_no_divide_by_zero():
    avg = compute_prior_3yr_average([], holding_years=2)
    assert avg == D("0")

    non_excess, excess = split_distribution(D("3000.00"), avg)
    assert excess == D("3000.00")
    assert non_excess == D("0.00")
