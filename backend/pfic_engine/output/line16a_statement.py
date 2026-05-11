"""
Line 16a Daily Allocation Statement.

Required attachment per §6501(c)(8) — without this, the statute of limitations
for IRS audit does not begin to run.

Lists every day in the holding period with its allocated excess distribution amount.
"""
from decimal import Decimal
from datetime import date, timedelta
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)


def generate_line16a_statement(full_result: dict, holding_name: str, client_code: str) -> bytes:
    """
    Generate the Line 16a daily allocation statement PDF.
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    small = ParagraphStyle("small", parent=normal, fontSize=8)
    bold = ParagraphStyle("bold", parent=normal, fontName="Helvetica-Bold")
    title_style = ParagraphStyle("title", parent=normal, fontSize=13, fontName="Helvetica-Bold", spaceAfter=4)

    tax_year = full_result.get("tax_year", "")
    excess = full_result.get("excess_distribution", "0")
    year_buckets = full_result.get("year_buckets", {})

    story = []

    story.append(Paragraph("Form 8621 — Line 16a Attachment", title_style))
    story.append(Paragraph("Daily Ratable Allocation of Excess Distribution", bold))
    story.append(Paragraph(
        f"IRC §1291(a)(1)(A) — Required Attachment (§6501(c)(8))",
        ParagraphStyle("irc", parent=normal, fontSize=9, textColor=colors.HexColor("#1a365d")),
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.black, spaceAfter=6))
    story.append(Paragraph(f"Tax Year: {tax_year}  |  PFIC: {holding_name}  |  Client: {client_code}", normal))
    story.append(Paragraph(f"Total Excess Distribution: ${Decimal(str(excess)):,.2f}", bold))
    story.append(Spacer(1, 10))

    # Summary by year
    story.append(Paragraph("Year Summary", bold))
    summary_data = [["Tax Year", "Days", "Allocated Amount", "Classification"]]
    for yr_str, bucket in sorted(year_buckets.items(), key=lambda x: int(x[0])):
        summary_data.append([
            yr_str,
            str(bucket["days"]),
            f"${Decimal(str(bucket['amount'])):,.2f}",
            bucket["classification"].replace("_", " "),
        ])

    s_tbl = Table(summary_data, colWidths=[1.2*inch, 0.8*inch, 1.8*inch, 2.0*inch])
    s_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a365d")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (2, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
    ]))
    story.append(s_tbl)
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "Per IRC §1291(a)(1)(A) and Form 8621 Instructions (Rev. 12/2025): "
        "The excess distribution is allocated ratably to each day in the taxpayer's holding period. "
        "Days in pre-PFIC years (before 1987) and the current tax year are taxed as ordinary income. "
        "Days in prior PFIC years are subject to the highest applicable tax rate plus §6622 daily compound interest.",
        small,
    ))

    doc.build(story)
    return buf.getvalue()
