"""Tests for FIFO lot matching and LotTracker."""
import pytest
from datetime import date
from decimal import Decimal

from pfic_engine.lot.fifo import Lot, match_fifo
from pfic_engine.lot.lot_tracker import LotTracker
from tests.fixtures.known_cases import MULTI_LOT_FIFO, PARTIAL_SALE_LOT_SPLIT


def D(s):
    return Decimal(str(s))


def make_lot(lot_id, acq_date, units, cost_per_unit):
    return Lot(
        lot_id=lot_id,
        acquisition_date=acq_date,
        units=D(str(units)),
        cost_basis_per_unit=D(str(cost_per_unit)),
    )


# ── FIFO matching ────────────────────────────────────────────────────────────

def test_fifo_single_lot_full_sale():
    lot = make_lot("L1", date(2020, 1, 1), 100, 50)
    result, remaining = match_fifo([lot], D("100"), date(2023, 1, 1))
    assert len(result.matches) == 1
    assert result.matches[0].units_sold == D("100")
    assert len(remaining) == 0


def test_fifo_multi_lot_oldest_first():
    f = MULTI_LOT_FIFO
    lots = [
        make_lot("L1", f["lots"][0]["date"], f["lots"][0]["units"], 80),
        make_lot("L2", f["lots"][1]["date"], f["lots"][1]["units"], 100),
    ]
    result, remaining = match_fifo(lots, f["sale_units"], f["sale_date"])

    # L1 (100 units, oldest) consumed fully, 20 from L2
    assert "L1" in result.lots_exhausted
    assert len(remaining) == f["expected_lots_after"]
    assert remaining[0].units == f["expected_remaining_units"]
    assert remaining[0].acquisition_date == f["lots"][1]["date"]


def test_fifo_partial_sale_preserves_acquisition_date():
    f = PARTIAL_SALE_LOT_SPLIT
    lots = [make_lot("L1", f["lots"][0]["date"], f["lots"][0]["units"], 100)]
    result, remaining = match_fifo(lots, f["sale_units"], f["sale_date"])

    assert len(remaining) == 1
    residual = remaining[0]
    assert residual.units == f["expected_remaining_units"]
    assert residual.acquisition_date == f["expected_residual_acquisition_date"]
    assert residual.cost_basis_per_unit == f["expected_residual_cost_per_unit"]


def test_fifo_oversale_raises():
    lot = make_lot("L1", date(2020, 1, 1), 50, 100)
    with pytest.raises(ValueError, match="exceeds available"):
        match_fifo([lot], D("100"), date(2023, 1, 1))


def test_fifo_lot_units_invariant():
    """After a sale, sum of remaining units = original - sold."""
    lots = [
        make_lot("L1", date(2019, 1, 1), 200, 40),
        make_lot("L2", date(2020, 6, 1), 100, 60),
    ]
    result, remaining = match_fifo(lots, D("150"), date(2023, 1, 1))
    total_remaining = sum(l.units for l in remaining)
    assert total_remaining == D("150")  # 300 - 150


# ── LotTracker ───────────────────────────────────────────────────────────────

def test_lot_tracker_purchase_and_sale():
    tracker = LotTracker(first_pfic_year=1987)
    tracker.process_purchase(date(2020, 3, 1), D("100"), D("10000"))
    tracker.process_purchase(date(2021, 6, 1), D("50"), D("6000"))
    assert tracker.total_units() == D("150")

    event = tracker.process_sale(date(2024, 1, 15), D("80"), D("12000"))
    assert tracker.total_units() == D("70")


def test_lot_tracker_cost_basis_per_unit():
    tracker = LotTracker()
    lot = tracker.process_purchase(date(2022, 1, 1), D("200"), D("10000"))
    assert lot.cost_basis_per_unit == D("50")


def test_lot_tracker_fifo_order():
    tracker = LotTracker()
    tracker.process_purchase(date(2018, 1, 1), D("100"), D("5000"))   # cheaper lot
    tracker.process_purchase(date(2021, 1, 1), D("100"), D("15000"))  # expensive lot
    event = tracker.process_sale(date(2023, 6, 1), D("100"), D("12000"))
    # FIFO: oldest (2018) lot consumed first
    assert event.fifo_result.matches[0].lot.acquisition_date == date(2018, 1, 1)
    assert date(2018, 1, 1) in [m.lot.acquisition_date for m in event.fifo_result.matches]


# ── TC-08: FIFO partial sale ──────────────────────────────────────────────────

def test_tc08_fifo_partial_sale():
    lots = [
        make_lot("L1", date(2020, 1, 1), 100, "100.00"),   # cost basis $10,000
        make_lot("L2", date(2021, 1, 1), 100, "120.00"),   # cost basis $12,000
    ]
    result, remaining = match_fifo(lots, D("150"), date(2022, 12, 31))

    # L1 fully consumed
    assert result.matches[0].lot.lot_id == "L1"
    assert result.matches[0].units_sold == D("100")

    # L2 partially consumed: 50 sold
    assert result.matches[1].lot.lot_id == "L2"
    assert result.matches[1].units_sold == D("50")

    # Residual: 50 units of L2, original acquisition date preserved
    assert len(remaining) == 1
    assert remaining[0].units == D("50")
    assert remaining[0].acquisition_date == date(2021, 1, 1)

    # Gain: L1=$5,000, L2=$1,500 → total $6,500
    total_proceeds = D("22500")
    l1_proceeds = total_proceeds * (D("100") / D("150"))
    l2_proceeds = total_proceeds * (D("50") / D("150"))
    l1_gain = l1_proceeds - D("10000.00")
    l2_gain = l2_proceeds - D("6000.00")
    assert abs(l1_gain + l2_gain - D("6500.00")) < D("0.01")
