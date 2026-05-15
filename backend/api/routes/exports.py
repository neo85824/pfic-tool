"""Export endpoints — PDF workpaper, Line 16a attachment, Excel workpapers."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from api.db.models import Calculation, PFICHolding, Client, User
from api.deps import get_db, get_current_user
from pfic_engine.output.pdf_generator import generate_form8621_workpaper
from pfic_engine.output.line16a_statement import generate_line16a_statement
from pfic_engine.output.excel_workpaper import generate_workpapers

router = APIRouter(prefix="/holdings/{holding_id}/calculations/{tax_year}", tags=["exports"])


def _get_calc(holding_id: str, tax_year: int, user: User, db: Session) -> tuple[Calculation, PFICHolding]:
    h = (
        db.query(PFICHolding)
        .join(Client)
        .filter(PFICHolding.id == holding_id, Client.user_id == user.id)
        .first()
    )
    if not h:
        raise HTTPException(404, "Holding not found")
    c = db.query(Calculation).filter_by(holding_id=holding_id, tax_year=tax_year).first()
    if not c:
        raise HTTPException(404, "No calculation found for this year — run calculation first")
    return c, h


@router.get("/export/pdf")
def export_pdf(
    holding_id: str,
    tax_year: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    calc, holding = _get_calc(holding_id, tax_year, user, db)
    client = db.get(Client, holding.client_id)
    pdf_bytes = generate_form8621_workpaper(
        calc.full_result, holding.pfic_name, client.client_code
    )
    filename = f"Form8621_Workpaper_{client.client_code}_{tax_year}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/line16a")
def export_line16a(
    holding_id: str,
    tax_year: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    calc, holding = _get_calc(holding_id, tax_year, user, db)
    client = db.get(Client, holding.client_id)
    pdf_bytes = generate_line16a_statement(
        calc.full_result, holding.pfic_name, client.client_code
    )
    filename = f"Form8621_Line16a_{client.client_code}_{tax_year}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/excel")
def export_excel(
    holding_id: str,
    tax_year: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    calc, holding = _get_calc(holding_id, tax_year, user, db)
    client = db.get(Client, holding.client_id)
    xlsx_bytes = generate_workpapers(
        calc.full_result, holding.pfic_name, client.client_code
    )
    filename = f"Form8621_Workpapers_{client.client_code}_{tax_year}.xlsx"
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
