"""Tests for proportional per-lot excess distribution splitting."""
from decimal import Decimal

import pytest

from pfic_engine.section_1291.lot_shares import compute_lot_shares
from tests.fixtures.known_cases import TC_MAIN_2022


def D(s):
    return Decimal(str(s))


# ── TC-MAIN Phase 3: 6-lot proportional split ────────────────────────────────

def test_tc_main_6lot_shares():
    expected = TC_MAIN_2022["expected_lot_excess"]
    units = [t["units"] for t in TC_MAIN_2022["transactions"] if t["type"] == "purchase"]
    excess = TC_MAIN_2022["expected_excess"]

    shares = compute_lot_shares(excess, units)

    assert len(shares) == 6
    assert shares[0] == expected[0], f"L1: {shares[0]} != {expected[0]}"
    assert shares[1] == expected[1], f"L2: {shares[1]} != {expected[1]}"
    assert shares[2] == expected[2], f"L3: {shares[2]} != {expected[2]}"
    assert shares[3] == expected[3], f"L4: {shares[3]} != {expected[3]}"
    assert shares[4] == expected[4], f"L5: {shares[4]} != {expected[4]}"
    assert shares[5] == expected[5], f"L6: {shares[5]} != {expected[5]}"


def test_tc_main_6lot_sum_conservation():
    units = [t["units"] for t in TC_MAIN_2022["transactions"] if t["type"] == "purchase"]
    excess = TC_MAIN_2022["expected_excess"]
    shares = compute_lot_shares(excess, units)
    assert sum(shares) == excess


# ── TC-03: Decimal residual conservation (3 equal lots) ──────────────────────

def test_tc03_residual_conservation():
    excess = D("1.00")
    units = [D("1"), D("1"), D("1")]
    shares = compute_lot_shares(excess, units)

    assert shares[0] == D("0.33")
    assert shares[1] == D("0.33")
    assert shares[2] == D("0.34")  # last lot absorbs residual
    assert sum(shares) == D("1.00")


def test_single_lot_gets_full_excess():
    shares = compute_lot_shares(D("500.00"), [D("100")])
    assert shares == [D("500.00")]


def test_two_equal_lots_split_evenly():
    shares = compute_lot_shares(D("100.00"), [D("50"), D("50")])
    assert shares[0] == D("50.00")
    assert shares[1] == D("50.00")
    assert sum(shares) == D("100.00")


def test_empty_lots_returns_empty():
    assert compute_lot_shares(D("1000.00"), []) == []
