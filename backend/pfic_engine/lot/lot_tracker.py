"""
LotTracker: manages an ordered portfolio of PFIC lots across transactions.

Handles purchases, sales (FIFO), distributions, and basis adjustments.
Ensures no average-cost basis slippage between lots.
"""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional
import uuid

from pfic_engine.core.decimal_utils import to_decimal
from pfic_engine.lot.fifo import Lot, FIFOResult, match_fifo


@dataclass
class Transaction:
    txn_date: date
    txn_type: str   # 'purchase' | 'sale' | 'distribution' | 'reinvestment' | 'return_of_capital'
    units: Optional[Decimal]
    total_value_usd: Decimal
    notes: str = ""


@dataclass
class SaleEvent:
    """Recorded outcome of a sale transaction."""
    sale_date: date
    fifo_result: FIFOResult
    sale_price_per_unit: Decimal
    total_proceeds: Decimal


class LotTracker:
    """
    Tracks lots for a single PFIC holding across its lifetime.

    Usage:
        tracker = LotTracker(first_pfic_year=1987)
        tracker.process_purchase(date(2020, 1, 15), units=100, total_cost_usd=5000)
        tracker.process_purchase(date(2021, 3, 1),  units=50,  total_cost_usd=3000)
        result = tracker.process_sale(date(2024, 6, 30), units=80, total_proceeds_usd=8000)
    """

    def __init__(self, first_pfic_year: int = 1987):
        self.first_pfic_year = first_pfic_year
        self.lots: list[Lot] = []
        self.sale_events: list[SaleEvent] = []

    def process_purchase(
        self,
        purchase_date: date,
        units: Decimal,
        total_cost_usd: Decimal,
    ) -> Lot:
        units = to_decimal(units)
        total_cost_usd = to_decimal(total_cost_usd)
        cost_per_unit = total_cost_usd / units

        lot = Lot(
            lot_id=str(uuid.uuid4()),
            acquisition_date=purchase_date,
            units=units,
            cost_basis_per_unit=cost_per_unit,
            first_pfic_year=self.first_pfic_year,
        )
        self.lots.append(lot)
        return lot

    def process_sale(
        self,
        sale_date: date,
        units: Decimal,
        total_proceeds_usd: Decimal,
    ) -> SaleEvent:
        units = to_decimal(units)
        total_proceeds_usd = to_decimal(total_proceeds_usd)
        sale_price_per_unit = total_proceeds_usd / units

        fifo_result, self.lots = match_fifo(self.lots, units, sale_date)

        event = SaleEvent(
            sale_date=sale_date,
            fifo_result=fifo_result,
            sale_price_per_unit=sale_price_per_unit,
            total_proceeds=total_proceeds_usd,
        )
        self.sale_events.append(event)
        return event

    def total_units(self) -> Decimal:
        return sum(l.units for l in self.lots)

    def total_cost_basis(self) -> Decimal:
        return sum(l.total_cost_basis for l in self.lots)

    def get_lots_held_at(self, as_of: date) -> list[Lot]:
        """Return lots that were still open as of a given date."""
        return [l for l in self.lots if l.acquisition_date <= as_of]
