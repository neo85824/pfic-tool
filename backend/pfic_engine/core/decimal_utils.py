"""
High-precision Decimal utilities for PFIC calculations.
All monetary arithmetic must use Decimal — never float.
"""
from decimal import Decimal, ROUND_HALF_UP, getcontext

getcontext().prec = 28


CENT = Decimal("0.01")
EIGHT_PLACES = Decimal("0.00000001")
SIX_PLACES = Decimal("0.000001")


def to_decimal(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def round_cents(amount: Decimal) -> Decimal:
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def round_rate(rate: Decimal) -> Decimal:
    return rate.quantize(EIGHT_PLACES, rounding=ROUND_HALF_UP)


def safe_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == Decimal("0"):
        return Decimal("0")
    return numerator / denominator
