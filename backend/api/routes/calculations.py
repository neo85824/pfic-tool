"""
Calculation trigger and retrieval.
POST /holdings/{id}/calculate  → runs §1291 engine, stores result
GET  /holdings/{id}/calculations/{tax_year} → retrieve stored result
"""
import subprocess
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.db.models import Calculation, PFICHolding, Transaction, Client, User
from api.deps import get_db, get_current_user
from pfic_engine.section_1291.excess_dist import (
    compute_prior_3yr_average,
    split_distribution,
)
from pfic_engine.section_1291.lot_shares import compute_lot_shares
from pfic_engine.section_1291.daily_allocation import allocate_excess_distribution
from pfic_engine.section_1291.deferred_tax import compute_deferred_tax_with_interest
from pfic_engine.lot.lot_tracker import LotTracker
from pfic_engine.verification.cross_check import run_all_checks

router = APIRouter(prefix="/holdings/{holding_id}", tags=["calculations"])


class HoldingContext(BaseModel):
    pfic_name: str
    client_code: str


@router.get("/info", response_model=HoldingContext)
def get_holding_info(
    holding_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    h = _get_holding(holding_id, user, db)
    return HoldingContext(pfic_name=h.pfic_name, client_code=h.client.client_code)


def _get_holding(holding_id: str, user: User, db: Session) -> PFICHolding:
    h = (
        db.query(PFICHolding)
        .join(Client)
        .filter(PFICHolding.id == holding_id, Client.user_id == user.id)
        .first()
    )
    if not h:
        raise HTTPException(404, "Holding not found")
    return h


def _engine_version() -> str:
    try:
        return subprocess.check_output(
            ["git", "describe", "--tags", "--always"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return "dev"


class CalculateRequest(BaseModel):
    tax_year: int
    marginal_rate_override: Optional[float] = None  # Not used in MVP (engine uses max rate)


class CalculationSummary(BaseModel):
    id: str
    tax_year: int
    method: str
    status: str
    engine_version: Optional[str]
    total_excess_dist: Optional[float]
    additional_tax: Optional[float]
    total_interest: Optional[float]
    ordinary_income: Optional[float]
    grand_total: Optional[float]
    warnings: list[str]

    class Config:
        from_attributes = True


class CalculationDetail(CalculationSummary):
    full_result: dict


@router.post("/calculate", response_model=CalculationDetail)
def run_calculation(
    holding_id: str,
    req: CalculateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    holding = _get_holding(holding_id, user, db)
    tax_year = req.tax_year
    first_pfic_year = holding.first_pfic_year or 1987

    txns = (
        db.query(Transaction)
        .filter_by(holding_id=holding_id)
        .order_by(Transaction.txn_date)
        .all()
    )
    if not txns:
        raise HTTPException(400, "No transactions found for this holding")

    # Separate distributions and build lot tracker
    tracker = LotTracker(first_pfic_year=first_pfic_year)
    distributions_by_year: dict[int, Decimal] = {}
    dispositions = []

    for t in txns:
        if t.txn_type == "purchase":
            tracker.process_purchase(
                t.txn_date,
                Decimal(str(t.units or 0)),
                Decimal(str(t.total_value_usd)),
            )
        elif t.txn_type == "sale":
            sale_event = tracker.process_sale(
                t.txn_date,
                Decimal(str(t.units or 0)),
                Decimal(str(t.total_value_usd)),
            )
            dispositions.append((t, sale_event))
        elif t.txn_type in ("distribution", "reinvestment"):
            yr = t.txn_date.year
            distributions_by_year[yr] = (
                distributions_by_year.get(yr, Decimal("0"))
                + Decimal(str(t.total_value_usd))
            )

    current_year_dist = distributions_by_year.get(tax_year, Decimal("0"))

    # Build prior 3-year list (years before current tax year, sorted)
    prior_years = sorted(y for y in distributions_by_year if y < tax_year)
    prior_distributions = [distributions_by_year[y] for y in prior_years[-3:]]
    holding_years_before = len(prior_years)

    prior_avg = compute_prior_3yr_average(prior_distributions, holding_years_before)
    non_excess, excess = split_distribution(current_year_dist, prior_avg)

    all_year_buckets: dict = {}
    all_deferred_results = []
    warnings: list[str] = []

    # Process each lot that was held during this distribution / sale
    if excess > Decimal("0"):
        eligible_lots = [l for l in tracker.lots if l.acquisition_date.year <= tax_year]
        total_units = sum(l.units for l in eligible_lots)

        lot_excess_amounts = compute_lot_shares(
            excess, [l.units for l in eligible_lots]
        )

        for lot, lot_excess in zip(eligible_lots, lot_excess_amounts):
            disposition_date = date(tax_year, 12, 31)
            alloc = allocate_excess_distribution(
                excess_amount=lot_excess,
                acquisition_date=lot.acquisition_date,
                disposition_date=disposition_date,
                current_tax_year=tax_year,
            )
            deferred = compute_deferred_tax_with_interest(
                alloc["year_buckets"], current_tax_year=tax_year
            )
            try:
                check_warnings = run_all_checks(
                    alloc["year_buckets"], lot_excess, deferred
                )
                warnings.extend(check_warnings)
            except Exception as e:
                warnings.append(f"Cross-check failed: {e}")

            for yr, bucket in alloc["year_buckets"].items():
                if yr in all_year_buckets:
                    all_year_buckets[yr]["days"] += bucket["days"]
                    all_year_buckets[yr]["amount"] += bucket["amount"]
                else:
                    all_year_buckets[yr] = dict(bucket)
            all_deferred_results.append({
                "acquisition_date": str(lot.acquisition_date),
                "units": str(lot.units),
                "lot_excess": str(lot_excess),
                "year_results": deferred["year_results"],
                "ordinary_income": deferred["ordinary_income"],
                "total_deferred_tax": deferred["total_deferred_tax"],
                "total_interest": deferred["total_interest"],
                "grand_total": deferred["grand_total"],
            })

    # Aggregate totals
    total_tax = sum(Decimal(d["total_deferred_tax"]) for d in all_deferred_results)
    total_interest = sum(Decimal(d["total_interest"]) for d in all_deferred_results)
    total_ordinary = non_excess + sum(Decimal(d["ordinary_income"]) for d in all_deferred_results)
    grand_total = total_tax + total_interest

    full_result = {
        "tax_year": tax_year,
        "current_year_distribution": str(current_year_dist),
        "prior_3yr_average": str(prior_avg),
        "non_excess_ordinary": str(non_excess),
        "excess_distribution": str(excess),
        "year_buckets": {
            str(k): {
                "days": v["days"],
                "amount": str(v["amount"]),
                "classification": v["classification"],
            }
            for k, v in all_year_buckets.items()
        },
        "deferred_tax_results": all_deferred_results,
        "total_deferred_tax": str(total_tax),
        "total_interest": str(total_interest),
        "total_ordinary_income": str(total_ordinary),
        "grand_total": str(grand_total),
        "warnings": warnings,
    }

    # Upsert calculation record
    existing = db.query(Calculation).filter_by(
        holding_id=holding_id, tax_year=tax_year
    ).first()
    if existing:
        db.delete(existing)
        db.flush()

    calc = Calculation(
        holding_id=holding_id,
        tax_year=tax_year,
        method="1291",
        status="draft",
        engine_version=_engine_version(),
        total_excess_dist=float(excess),
        additional_tax=float(total_tax),
        total_interest=float(total_interest),
        ordinary_income=float(total_ordinary),
        grand_total=float(grand_total),
        full_result=full_result,
    )
    db.add(calc)
    db.commit()
    db.refresh(calc)

    return CalculationDetail(
        id=calc.id,
        tax_year=calc.tax_year,
        method=calc.method,
        status=calc.status,
        engine_version=calc.engine_version,
        total_excess_dist=calc.total_excess_dist,
        additional_tax=calc.additional_tax,
        total_interest=calc.total_interest,
        ordinary_income=calc.ordinary_income,
        grand_total=calc.grand_total,
        warnings=warnings,
        full_result=full_result,
    )


@router.get("/calculations", response_model=list[CalculationSummary])
def list_calculations(
    holding_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_holding(holding_id, user, db)
    calcs = db.query(Calculation).filter_by(holding_id=holding_id).all()
    return [
        CalculationSummary(
            id=c.id, tax_year=c.tax_year, method=c.method, status=c.status,
            engine_version=c.engine_version, total_excess_dist=c.total_excess_dist,
            additional_tax=c.additional_tax, total_interest=c.total_interest,
            ordinary_income=c.ordinary_income, grand_total=c.grand_total,
            warnings=c.full_result.get("warnings", []) if c.full_result else [],
        )
        for c in calcs
    ]


@router.get("/calculations/{tax_year}", response_model=CalculationDetail)
def get_calculation(
    holding_id: str,
    tax_year: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_holding(holding_id, user, db)
    c = db.query(Calculation).filter_by(holding_id=holding_id, tax_year=tax_year).first()
    if not c:
        raise HTTPException(404, "Calculation not found for this year")
    return CalculationDetail(
        id=c.id, tax_year=c.tax_year, method=c.method, status=c.status,
        engine_version=c.engine_version, total_excess_dist=c.total_excess_dist,
        additional_tax=c.additional_tax, total_interest=c.total_interest,
        ordinary_income=c.ordinary_income, grand_total=c.grand_total,
        warnings=c.full_result.get("warnings", []) if c.full_result else [],
        full_result=c.full_result or {},
    )
