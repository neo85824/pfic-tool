from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from api.db.models import Client, User
from api.deps import get_db, get_current_user

router = APIRouter(prefix="/clients", tags=["clients"])


class ClientCreate(BaseModel):
    client_code: str
    tax_year_start: Optional[int] = None
    notes: Optional[str] = None


class ClientUpdate(BaseModel):
    client_code: Optional[str] = None
    tax_year_start: Optional[int] = None
    notes: Optional[str] = None


class ClientOut(BaseModel):
    id: str
    client_code: str
    tax_year_start: Optional[int]
    notes: Optional[str]

    class Config:
        from_attributes = True


@router.get("/", response_model=list[ClientOut])
def list_clients(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Client).filter_by(user_id=user.id).all()


@router.post("/", response_model=ClientOut, status_code=201)
def create_client(req: ClientCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if db.query(Client).filter_by(user_id=user.id, client_code=req.client_code).first():
        raise HTTPException(400, "Client code already exists")
    c = Client(user_id=user.id, **req.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = db.query(Client).filter_by(id=client_id, user_id=user.id).first()
    if not c:
        raise HTTPException(404, "Client not found")
    return c


@router.patch("/{client_id}", response_model=ClientOut)
def update_client(client_id: str, req: ClientUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = db.query(Client).filter_by(id=client_id, user_id=user.id).first()
    if not c:
        raise HTTPException(404, "Client not found")
    if req.client_code is not None:
        if req.client_code != c.client_code and db.query(Client).filter_by(user_id=user.id, client_code=req.client_code).first():
            raise HTTPException(400, "Client code already exists")
        c.client_code = req.client_code
    if req.tax_year_start is not None:
        c.tax_year_start = req.tax_year_start
    if req.notes is not None:
        c.notes = req.notes
    db.commit()
    db.refresh(c)
    return c


@router.delete("/{client_id}", status_code=204)
def delete_client(client_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = db.query(Client).filter_by(id=client_id, user_id=user.id).first()
    if not c:
        raise HTTPException(404, "Client not found")
    db.delete(c)
    db.commit()
