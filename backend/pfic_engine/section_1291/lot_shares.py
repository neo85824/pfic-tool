"""
Proportional excess distribution split across lots.

IRC §1291(a)(1): each lot's share of the excess is proportional to the number
of units held in that lot relative to total units across all eligible lots.
"""
from decimal import Decimal, ROUND_HALF_UP


def compute_lot_shares(excess: Decimal, units: list[Decimal]) -> list[Decimal]:
    """
    Split excess proportionally by units. Last lot absorbs residual to ensure
    sum(result) == excess exactly.

    Args:
        excess: Total excess distribution amount to split.
        units: Per-lot unit counts (must all be positive; ordering preserved).

    Returns:
        List of per-lot excess amounts, same length and order as units.
    """
    if not units:
        return []

    total_units = sum(units)
    shares: list[Decimal] = []
    running = Decimal("0")

    for i, lot_units in enumerate(units):
        if i < len(units) - 1:
            share = (lot_units / total_units * excess).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            share = excess - running
        shares.append(share)
        running += share

    return shares
