"""
FIFO lot matching for PFIC share tracking.

IRS mandates FIFO (first-in, first-out) for PFIC share identification.
Average cost basis is NOT permitted. IRC §1012 + PFIC regulations.
"""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional

from pfic_engine.core.decimal_utils import to_decimal


@dataclass
class Lot:
    """A single tax lot acquired on one date."""
    lot_id: str
    acquisition_date: date
    units: Decimal
    cost_basis_per_unit: Decimal  # USD per unit
    first_pfic_year: Optional[int] = None

    @property
    def total_cost_basis(self) -> Decimal:
        return self.units * self.cost_basis_per_unit


@dataclass
class SaleMatch:
    """Records how many units from one lot were consumed by a sale."""
    lot: Lot
    units_sold: Decimal
    original_lot_units: Decimal  # units in lot before this sale


@dataclass
class FIFOResult:
    """Result of a FIFO match operation."""
    matches: list[SaleMatch]
    remaining_units: Decimal      # units of the sale NOT matched (should be 0)
    lots_exhausted: list[str]     # lot_ids fully consumed
    lot_split: Optional[Lot] = None  # residual lot if a lot was partially consumed


def match_fifo(
    lots: list[Lot],
    sale_units: Decimal,
    sale_date: date,
) -> tuple[FIFOResult, list[Lot]]:
    """
    Apply FIFO matching: consume lots from oldest to newest.

    Returns (FIFOResult, remaining_lots_after_sale).
    Raises ValueError if sale_units exceeds total available units.
    """
    sale_units = to_decimal(sale_units)
    sorted_lots = sorted(lots, key=lambda l: (l.acquisition_date, l.lot_id))

    total_available = sum(l.units for l in sorted_lots)
    if sale_units > total_available:
        raise ValueError(
            f"Sale of {sale_units} units exceeds available {total_available} units."
        )

    matches: list[SaleMatch] = []
    lots_exhausted: list[str] = []
    remaining_sale = sale_units
    updated_lots: list[Lot] = []
    lot_split: Optional[Lot] = None

    for lot in sorted_lots:
        if remaining_sale <= Decimal("0"):
            updated_lots.append(lot)
            continue

        if lot.units <= remaining_sale:
            # Fully consume this lot
            matches.append(SaleMatch(
                lot=lot,
                units_sold=lot.units,
                original_lot_units=lot.units,
            ))
            lots_exhausted.append(lot.lot_id)
            remaining_sale -= lot.units
        else:
            # Partially consume — split the lot
            units_used = remaining_sale
            units_kept = lot.units - units_used

            matches.append(SaleMatch(
                lot=lot,
                units_sold=units_used,
                original_lot_units=lot.units,
            ))
            # Residual lot retains original acquisition date and basis
            residual = Lot(
                lot_id=lot.lot_id,
                acquisition_date=lot.acquisition_date,
                units=units_kept,
                cost_basis_per_unit=lot.cost_basis_per_unit,
                first_pfic_year=lot.first_pfic_year,
            )
            lot_split = residual
            updated_lots.append(residual)
            remaining_sale = Decimal("0")

    result = FIFOResult(
        matches=matches,
        remaining_units=remaining_sale,
        lots_exhausted=lots_exhausted,
        lot_split=lot_split,
    )
    return result, updated_lots
