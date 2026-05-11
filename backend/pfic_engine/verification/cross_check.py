"""
Internal cross-validation for §1291 calculation results.

IRC §6501(c)(8): the statute of limitations does not begin to run unless
the taxpayer attaches a complete and accurate statement to the return.
These checks help ensure the calculation is internally consistent.
"""
from decimal import Decimal


TOLERANCE = Decimal("0.02")  # 2-cent tolerance for rounding accumulation


def _d(v) -> Decimal:
    return Decimal(str(v))


class ValidationError(Exception):
    pass


def check_year_buckets_sum(
    year_buckets: dict,
    excess_distribution: Decimal,
) -> None:
    """
    Sum of all year-bucket amounts must equal the total excess distribution.
    """
    total = sum(_d(b["amount"]) for b in year_buckets.values())
    diff = abs(total - _d(excess_distribution))
    if diff > TOLERANCE:
        raise ValidationError(
            f"Year-bucket sum {total} differs from excess distribution "
            f"{excess_distribution} by {diff} (tolerance {TOLERANCE})."
        )


def check_deferred_tax_sum(result: dict) -> None:
    """
    Sum of individual year taxes must match total_deferred_tax.
    """
    year_results = result["year_results"]
    computed = sum(
        _d(r["tax"]) for r in year_results.values() if r["tax"] is not None
    )
    declared = _d(result["total_deferred_tax"])
    diff = abs(computed - declared)
    if diff > TOLERANCE:
        raise ValidationError(
            f"Sum of year taxes {computed} != total_deferred_tax {declared} "
            f"(diff {diff})."
        )


def check_interest_positive(result: dict) -> bool:
    """
    If there are any prior-PFIC years in the result, total_interest must be > 0.
    Returns False (does not raise) because zero interest is possible in edge cases.
    """
    has_prior = any(
        r["classification"] == "prior_pfic"
        for r in result["year_results"].values()
    )
    if has_prior and _d(result["total_interest"]) <= Decimal("0"):
        return False
    return True


def check_lot_units(lots, expected_total: Decimal) -> None:
    """
    Sum of remaining lot units must equal expected_total.
    """
    total = sum(_d(l.units) for l in lots)
    diff = abs(total - _d(expected_total))
    if diff > TOLERANCE:
        raise ValidationError(
            f"Lot units sum {total} != expected {expected_total} (diff {diff})."
        )


def run_all_checks(
    year_buckets: dict,
    excess_distribution: Decimal,
    deferred_tax_result: dict,
) -> list[str]:
    """
    Run all cross-checks. Returns list of warning strings (empty = all passed).
    Raises ValidationError on hard failures.
    """
    warnings = []

    check_year_buckets_sum(year_buckets, excess_distribution)
    check_deferred_tax_sum(deferred_tax_result)

    if not check_interest_positive(deferred_tax_result):
        warnings.append(
            "Prior PFIC years present but total_interest is zero. "
            "Verify interest calculation and filing deadlines."
        )

    return warnings
