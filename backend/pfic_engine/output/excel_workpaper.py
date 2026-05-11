"""
Excel calculation workpapers — one sheet per computation area.
"""
from decimal import Decimal
from io import BytesIO

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


DARK_BLUE = "1A365D"
LIGHT_BLUE = "EEF4FB"
YELLOW = "FFF3CD"
WHITE = "FFFFFF"
GREY = "F7F7F7"


def _header_style(ws, row, cols):
    fill = PatternFill("solid", fgColor=DARK_BLUE)
    font = Font(bold=True, color="FFFFFF", size=10)
    for col in range(1, cols + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal="center")


def _border():
    thin = Side(style="thin", color="CCCCCC")
    return Border(left=thin, right=thin, top=thin, bottom=thin)


def generate_workpapers(full_result: dict, holding_name: str, client_code: str) -> bytes:
    wb = openpyxl.Workbook()

    # ── Sheet 1: Summary ─────────────────────────────────────────────────────
    ws = wb.active
    ws.title = "Summary"
    ws.column_dimensions["A"].width = 40
    ws.column_dimensions["B"].width = 20

    tax_year = full_result.get("tax_year", "")
    rows = [
        ("PFIC Form 8621 Calculation Workpaper", None),
        (f"Tax Year: {tax_year}", None),
        (f"PFIC: {holding_name}", None),
        (f"Client: {client_code}", None),
        (f"Method: §1291 Excess Distribution", None),
        (None, None),
        ("Line", "Amount (USD)"),
        ("15b — Prior 3-year average distribution", full_result.get("prior_3yr_average")),
        ("15b(125%) — Threshold", str(Decimal(str(full_result.get("prior_3yr_average","0"))) * Decimal("1.25"))),
        ("15c — Current year distribution", full_result.get("current_year_distribution")),
        ("15e(1) — Non-excess ordinary income", full_result.get("non_excess_ordinary")),
        ("15e(2) — Excess distribution", full_result.get("excess_distribution")),
        ("16c — Additional tax (prior PFIC years)", full_result.get("total_deferred_tax")),
        ("16f — §6621 interest", full_result.get("total_interest")),
        ("16e+16f — Grand total", full_result.get("grand_total")),
        ("16b — Ordinary income (pre-PFIC + current)", full_result.get("total_ordinary_income")),
    ]
    for i, (label, value) in enumerate(rows, start=1):
        ws.cell(row=i, column=1, value=label)
        if value is not None:
            try:
                ws.cell(row=i, column=2, value=float(Decimal(str(value))))
                ws.cell(row=i, column=2).number_format = '#,##0.00'
            except Exception:
                ws.cell(row=i, column=2, value=value)
    _header_style(ws, 7, 2)

    # ── Sheet 2: Year Detail ─────────────────────────────────────────────────
    ws2 = wb.create_sheet("Year Detail")
    ws2.column_dimensions["A"].width = 8
    ws2.column_dimensions["B"].width = 16
    ws2.column_dimensions["C"].width = 18
    ws2.column_dimensions["D"].width = 16
    ws2.column_dimensions["E"].width = 16
    ws2.column_dimensions["F"].width = 16
    ws2.column_dimensions["G"].width = 16
    ws2.column_dimensions["H"].width = 16

    headers2 = ["Year", "Classification", "Allocated Amount", "Tax", "Interest Start", "Interest End", "Interest", "Total"]
    for col, h in enumerate(headers2, start=1):
        ws2.cell(row=1, column=col, value=h)
    _header_style(ws2, 1, len(headers2))

    row_num = 2
    deferred_results = full_result.get("deferred_tax_results", [])
    for dr in deferred_results:
        for yr_str, yr_data in sorted(dr["year_results"].items(), key=lambda x: int(x[0])):
            tax = yr_data.get("tax")
            interest = yr_data.get("interest")
            total = (Decimal(str(tax or 0)) + Decimal(str(interest or 0))) if tax else None

            ws2.cell(row=row_num, column=1, value=int(yr_str))
            ws2.cell(row=row_num, column=2, value=yr_data["classification"].replace("_", " "))
            ws2.cell(row=row_num, column=3, value=float(Decimal(str(yr_data["allocated_amount"])))).number_format = '#,##0.00'
            if tax:
                ws2.cell(row=row_num, column=4, value=float(Decimal(str(tax)))).number_format = '#,##0.00'
            ws2.cell(row=row_num, column=5, value=yr_data.get("interest_start", ""))
            ws2.cell(row=row_num, column=6, value=yr_data.get("interest_end", ""))
            if interest:
                ws2.cell(row=row_num, column=7, value=float(Decimal(str(interest)))).number_format = '#,##0.00'
            if total:
                ws2.cell(row=row_num, column=8, value=float(total)).number_format = '#,##0.00'
            fill_color = WHITE if row_num % 2 == 0 else LIGHT_BLUE
            for col in range(1, 9):
                ws2.cell(row=row_num, column=col).fill = PatternFill("solid", fgColor=fill_color)
                ws2.cell(row=row_num, column=col).border = _border()
            row_num += 1

    # ── Sheet 3: Year Bucket Summary ─────────────────────────────────────────
    ws3 = wb.create_sheet("Daily Allocation Summary")
    ws3.column_dimensions["A"].width = 10
    ws3.column_dimensions["B"].width = 8
    ws3.column_dimensions["C"].width = 20
    ws3.column_dimensions["D"].width = 18

    headers3 = ["Year", "Days", "Amount Allocated", "Classification"]
    for col, h in enumerate(headers3, start=1):
        ws3.cell(row=1, column=col, value=h)
    _header_style(ws3, 1, len(headers3))

    year_buckets = full_result.get("year_buckets", {})
    for r, (yr_str, bucket) in enumerate(sorted(year_buckets.items(), key=lambda x: int(x[0])), start=2):
        ws3.cell(row=r, column=1, value=int(yr_str))
        ws3.cell(row=r, column=2, value=bucket["days"])
        ws3.cell(row=r, column=3, value=float(Decimal(str(bucket["amount"])))).number_format = '#,##0.00'
        ws3.cell(row=r, column=4, value=bucket["classification"].replace("_", " "))
        fill_color = WHITE if r % 2 == 0 else GREY
        for col in range(1, 5):
            ws3.cell(row=r, column=col).fill = PatternFill("solid", fgColor=fill_color)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
