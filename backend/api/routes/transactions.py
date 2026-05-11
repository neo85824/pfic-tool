"""
Transaction CRUD + CSV bulk import.
CSV columns (auto-detected, case-insensitive):
  date, type, units, amount_usd, notes
"""
import csv
import io
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.db.models import Transaction, PFICHolding, Client, User
from api.deps import get_db, get_current_user

router = APIRouter(prefix="/holdings/{holding_id}/transactions", tags=["transactions"])

VALID_TYPES = {"purchase", "sale", "distribution", "reinvestment", "return_of_capital"}


class TxnCreate(BaseModel):
    txn_date: date
    txn_type: str
    units: Optional[float] = None
    total_value_usd: float
    notes: Optional[str] = None


class TxnOut(BaseModel):
    id: str
    txn_date: date
    txn_type: str
    units: Optional[float]
    total_value_usd: float
    notes: Optional[str]

    class Config:
        from_attributes = True


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


@router.get("/", response_model=list[TxnOut])
def list_transactions(holding_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_holding(holding_id, user, db)
    return db.query(Transaction).filter_by(holding_id=holding_id).order_by(Transaction.txn_date).all()


@router.post("/", response_model=TxnOut, status_code=201)
def create_transaction(holding_id: str, req: TxnCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_holding(holding_id, user, db)
    if req.txn_type not in VALID_TYPES:
        raise HTTPException(400, f"Invalid txn_type. Valid: {VALID_TYPES}")
    t = Transaction(holding_id=holding_id, **req.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/{txn_id}", status_code=204)
def delete_transaction(holding_id: str, txn_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_holding(holding_id, user, db)
    t = db.query(Transaction).filter_by(id=txn_id, holding_id=holding_id).first()
    if not t:
        raise HTTPException(404, "Transaction not found")
    db.delete(t)
    db.commit()


@router.delete("/", status_code=204)
def clear_transactions(holding_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_holding(holding_id, user, db)
    db.query(Transaction).filter_by(holding_id=holding_id).delete()
    db.commit()


# ── CSV import ───────────────────────────────────────────────────────────────

_COL_MAP = {
    "date": "txn_date", "txn_date": "txn_date",
    "type": "txn_type", "txn_type": "txn_type", "transaction_type": "txn_type",
    "units": "units", "shares": "units", "quantity": "units",
    "amount": "total_value_usd", "amount_usd": "total_value_usd",
    "total_value_usd": "total_value_usd", "value": "total_value_usd",
    "notes": "notes", "note": "notes", "description": "notes",
}


def _map_header(raw_headers: list[str]) -> dict[int, str]:
    mapping = {}
    for i, h in enumerate(raw_headers):
        normalized = h.strip().lower().replace(" ", "_")
        if normalized in _COL_MAP:
            mapping[i] = _COL_MAP[normalized]
    return mapping


class CSVPreview(BaseModel):
    preview_rows: list[dict]
    total_rows: int
    detected_columns: dict
    errors: list[str]


@router.post("/csv-preview", response_model=CSVPreview)
async def csv_preview(
    holding_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Parse CSV and return first 10 rows for user review before committing."""
    _get_holding(holding_id, user, db)
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    headers = next(reader, None)
    if not headers:
        raise HTTPException(400, "CSV file is empty")

    col_map = _map_header(headers)
    detected = {headers[i]: internal for i, internal in col_map.items()}

    rows, errors = [], []
    for row_num, row in enumerate(reader, start=2):
        if len(row) == 0:
            continue
        parsed = {}
        for i, val in enumerate(row):
            internal = col_map.get(i)
            if internal:
                parsed[internal] = val.strip()
        rows.append(parsed)
        if row_num > 11:
            break

    return CSVPreview(
        preview_rows=rows[:10],
        total_rows=len(rows),
        detected_columns=detected,
        errors=errors,
    )


class CSVImportResult(BaseModel):
    imported: int
    skipped: int
    errors: list[str]


@router.post("/csv-import", response_model=CSVImportResult)
async def csv_import(
    holding_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Bulk import transactions from CSV. Clears existing transactions first."""
    _get_holding(holding_id, user, db)
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    headers = next(reader, None)
    if not headers:
        raise HTTPException(400, "CSV is empty")

    col_map = _map_header(headers)
    imported, skipped, errors = 0, 0, []

    db.query(Transaction).filter_by(holding_id=holding_id).delete()

    for row_num, row in enumerate(reader, start=2):
        if not any(v.strip() for v in row):
            continue
        parsed = {col_map[i]: row[i].strip() for i in col_map if i < len(row)}
        try:
            txn_date = date.fromisoformat(parsed["txn_date"])
            txn_type = parsed["txn_type"].lower().replace(" ", "_")
            if txn_type not in VALID_TYPES:
                errors.append(f"Row {row_num}: unknown type '{txn_type}'")
                skipped += 1
                continue
            units_raw = parsed.get("units", "").strip()
            units = Decimal(units_raw) if units_raw else None
            value = Decimal(parsed["total_value_usd"])

            db.add(Transaction(
                holding_id=holding_id,
                txn_date=txn_date,
                txn_type=txn_type,
                units=units,
                total_value_usd=value,
                notes=parsed.get("notes"),
            ))
            imported += 1
        except Exception as e:
            errors.append(f"Row {row_num}: {e}")
            skipped += 1

    db.commit()
    return CSVImportResult(imported=imported, skipped=skipped, errors=errors)
