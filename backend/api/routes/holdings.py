from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from api.db.models import PFICHolding, Client, User
from api.deps import get_db, get_current_user

router = APIRouter(prefix="/clients/{client_id}/holdings", tags=["holdings"])


class HoldingCreate(BaseModel):
    pfic_name: str
    reference_id: Optional[str] = None
    share_class: Optional[str] = None
    currency: str = "USD"
    method: str = "1291"
    first_pfic_year: Optional[int] = None


class HoldingUpdate(BaseModel):
    pfic_name: Optional[str] = None
    reference_id: Optional[str] = None
    first_pfic_year: Optional[int] = None


class HoldingOut(BaseModel):
    id: str
    pfic_name: str
    reference_id: Optional[str]
    share_class: Optional[str]
    currency: str
    method: str
    first_pfic_year: Optional[int]

    class Config:
        from_attributes = True


def _get_client(client_id: str, user: User, db: Session) -> Client:
    c = db.query(Client).filter_by(id=client_id, user_id=user.id).first()
    if not c:
        raise HTTPException(404, "Client not found")
    return c


@router.get("/", response_model=list[HoldingOut])
def list_holdings(client_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_client(client_id, user, db)
    return db.query(PFICHolding).filter_by(client_id=client_id).all()


@router.post("/", response_model=HoldingOut, status_code=201)
def create_holding(client_id: str, req: HoldingCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_client(client_id, user, db)
    h = PFICHolding(client_id=client_id, **req.model_dump())
    db.add(h)
    db.commit()
    db.refresh(h)
    return h


@router.get("/{holding_id}", response_model=HoldingOut)
def get_holding(client_id: str, holding_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_client(client_id, user, db)
    h = db.query(PFICHolding).filter_by(id=holding_id, client_id=client_id).first()
    if not h:
        raise HTTPException(404, "Holding not found")
    return h


@router.patch("/{holding_id}", response_model=HoldingOut)
def update_holding(client_id: str, holding_id: str, req: HoldingUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_client(client_id, user, db)
    h = db.query(PFICHolding).filter_by(id=holding_id, client_id=client_id).first()
    if not h:
        raise HTTPException(404, "Holding not found")
    if req.pfic_name is not None:
        h.pfic_name = req.pfic_name
    if req.reference_id is not None:
        h.reference_id = req.reference_id
    if req.first_pfic_year is not None:
        h.first_pfic_year = req.first_pfic_year
    db.commit()
    db.refresh(h)
    return h


@router.delete("/{holding_id}", status_code=204)
def delete_holding(client_id: str, holding_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_client(client_id, user, db)
    h = db.query(PFICHolding).filter_by(id=holding_id, client_id=client_id).first()
    if not h:
        raise HTTPException(404, "Holding not found")
    db.delete(h)
    db.commit()
