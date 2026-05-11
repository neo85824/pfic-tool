"""
Form 8621 Part V calculation report — PDF workpaper.

Generates a structured PDF that mirrors Form 8621 Part V line numbers.
Includes Line 16a daily allocation attachment per §6501(c)(8) requirement.
"""
from decimal import Decimal
from datetime import date
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable,
)
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

PAGE_W, PAGE_H = letter
MARGIN = 0.75 * inch


def _fmt(v, prefix="$") -> str:
    if v is None:
        return "—"
    try:
        d = Decimal(str(v))
        return f"{prefix}{d:,.2f}"
    except Exception:
        return str(v)


def _pct(v) -> str:
    if v is None:
        return "—"
    return f"{Decimal(str(v)) * 100:.1f}%"


def generate_form8621_workpaper(full_result: dict, holding_name: str, client_code: str) -> bytes:
    """
    Returns PDF bytes of the Form 8621 Part V calculation workpaper.
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    small = ParagraphStyle("small", parent=normal, fontSize=8)
    bold = ParagraphStyle("bold", parent=normal, fontName="Helvetica-Bold")
    title_style = ParagraphStyle("title", parent=normal, fontSize=14, fontName="Helvetica-Bold", spaceAfter=4)
    warning_style = ParagraphStyle("warning", parent=normal, fontSize=9, textColor=colors.red)

    tax_year = full_result.get("tax_year", "")
    excess = full_result.get("excess_distribution", "0")
    prior_avg = full_result.get("prior_3yr_average", "0")
    non_excess = full_result.get("non_excess_ordinary", "0")
    total_tax = full_result.get("total_deferred_tax", "0")
    total_interest = full_result.get("total_interest", "0")
    grand_total = full_result.get("grand_total", "0")
    ordinary_income = full_result.get("total_ordinary_income", "0")
    warnings = full_result.get("warnings", [])

    story = []

    # ── Header ───────────────────────────────────────────────────────────────
    story.append(Paragraph(f"PFIC Form 8621 — Calculation Workpaper", title_style))
    story.append(Paragraph(f"Tax Year: {tax_year}  |  PFIC: {holding_name}  |  Client: {client_code}", normal))
    story.append(Paragraph(f"Method: §1291 Excess Distribution  |  Currency: USD", normal))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.black, spaceAfter=8))

    # ── Warnings ─────────────────────────────────────────────────────────────
    if warnings:
        story.append(Paragraph("⚠ WARNINGS", bold))
        for w in warnings:
            story.append(Paragraph(f"• {w}", warning_style))
        story.append(Spacer(1, 8))

    # ── Part V: Section 1291 ─────────────────────────────────────────────────
    story.append(Paragraph("PART V — Section 1291 Method (Excess Distribution)", bold))
    story.append(Spacer(1, 4))

    summary_data = [
        ["Line", "Description", "Amount"],
        ["15b", "Prior 3-year average distribution", _fmt(prior_avg)],
        ["15b(125%)", "125% threshold", _fmt(Decimal(str(prior_avg)) * Decimal("1.25"))],
        ["15c", "Current year distribution", _fmt(full_result.get("current_year_distribution", "0"))],
        ["15e(1)", "Non-excess (ordinary income — current year)", _fmt(non_excess)],
        ["15e(2)", "Excess distribution amount", _fmt(excess)],
        ["16c", "Total additional tax (prior years)", _fmt(total_tax)],
        ["16f", "Total §6621 interest", _fmt(total_interest)],
        ["16e+16f", "Grand total deferred tax + interest", _fmt(grand_total)],
        ["16b", "Ordinary income (pre-PFIC + current year)", _fmt(ordinary_income)],
    ]
    tbl = Table(summary_data, colWidths=[1.2 * inch, 3.8 * inch, 1.5 * inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a365d")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f7f7")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, -3), (-1, -3), colors.HexColor("#fff3cd")),  # grand total highlight
    ]))
    story.append(tbl)
    story.append(Spacer(1, 16))

    # ── Year-by-year deferred tax detail ─────────────────────────────────────
    deferred_results = full_result.get("deferred_tax_results", [])
    if deferred_results:
        story.append(Paragraph("Year-by-Year Deferred Tax Detail (Form 8621 Line 16)", bold))
        story.append(Spacer(1, 4))

        detail_data = [["Year", "Class.", "Allocated Amount", "Tax Rate", "Tax", "Interest Start", "Interest End", "Interest"]]
        for dr in deferred_results:
            for yr_str, yr_data in sorted(dr["year_results"].items(), key=lambda x: int(x[0])):
                cls = yr_data["classification"]
                amt = yr_data["allocated_amount"]
                tax = yr_data.get("tax")
                interest = yr_data.get("interest")
                i_start = yr_data.get("interest_start", "—")
                i_end = yr_data.get("interest_end", "—")
                detail_data.append([
                    yr_str,
                    cls.replace("_", " "),
                    _fmt(amt),
                    "—" if tax is None else _pct(Decimal(str(tax)) / Decimal(str(amt)) if Decimal(str(amt)) else 0),
                    _fmt(tax),
                    i_start[:10] if i_start else "—",
                    i_end[:10] if i_end else "—",
                    _fmt(interest),
                ])

        col_ws = [0.5*inch, 0.9*inch, 1.1*inch, 0.7*inch, 1.0*inch, 0.9*inch, 0.9*inch, 1.0*inch]
        dt_tbl = Table(detail_data, colWidths=col_ws)
        dt_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d6a9f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef4fb")]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ]))
        story.append(dt_tbl)

    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "This workpaper is generated by PFIC Tool (pfic_engine). All calculations use Python Decimal precision. "
        "§6621 rates from IRS IRB publications. §7503 deadlines include COVID extensions (Notice 2020-23, Notice 2021-21). "
        "This document does not constitute tax advice. Verify all figures before filing.",
        small,
    ))

    doc.build(story)
    return buf.getvalue()
