"""
Line 16a Daily Allocation Statement — required attachment per §6501(c)(8).
Mirrors FE Step 2 (Year Allocation) and Step 3 (Interest Detail).
"""
from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)

DARK_BLUE  = colors.HexColor("#1A365D")
LIGHT_BLUE = colors.HexColor("#EEF4FB")
ORANGE     = colors.HexColor("#FFF3CD")
WHITE      = colors.white
GREY       = colors.HexColor("#F7F7F7")

_HDR = TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
    ("TEXTCOLOR",  (0, 0), (-1, 0), WHITE),
    ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE",   (0, 0), (-1, -1), 8),
    ("GRID",       (0, 0), (-1, -1), 0.4, colors.grey),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BLUE]),
])


def _D(v):
    try:
        return Decimal(str(v))
    except Exception:
        return Decimal("0")


def _fmt(v) -> str:
    try:
        return f"${_D(v):,.2f}"
    except Exception:
        return "—"


def _merged_year_results(deferred_tax_results):
    merged = {}
    for dr in deferred_tax_results:
        for yr_key, yr_data in dr["year_results"].items():
            yr = int(yr_key)
            if yr not in merged:
                merged[yr] = {
                    "classification": yr_data["classification"],
                    "allocated_amount": _D(yr_data["allocated_amount"]),
                    "tax":      _D(yr_data.get("tax") or 0),
                    "interest": _D(yr_data.get("interest") or 0),
                    "interest_start": yr_data.get("interest_start", ""),
                    "interest_end":   yr_data.get("interest_end", ""),
                }
            else:
                merged[yr]["allocated_amount"] += _D(yr_data["allocated_amount"])
                merged[yr]["tax"]              += _D(yr_data.get("tax") or 0)
                merged[yr]["interest"]         += _D(yr_data.get("interest") or 0)
    return merged


def generate_line16a_statement(full_result: dict, holding_name: str, client_code: str) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    small  = ParagraphStyle("small", parent=normal, fontSize=8)
    bold   = ParagraphStyle("bold",  parent=normal, fontName="Helvetica-Bold")
    title  = ParagraphStyle("title", parent=normal, fontSize=13, fontName="Helvetica-Bold", textColor=DARK_BLUE, spaceAfter=4)
    sec    = ParagraphStyle("sec",   parent=normal, fontSize=10, fontName="Helvetica-Bold", textColor=DARK_BLUE, spaceBefore=12, spaceAfter=4)
    irc    = ParagraphStyle("irc",   parent=normal, fontSize=9,  textColor=DARK_BLUE)

    tax_year   = full_result.get("tax_year", "")
    excess     = _D(full_result.get("excess_distribution", "0"))
    year_bkts  = full_result.get("year_buckets", {})
    deferred   = full_result.get("deferred_tax_results", [])
    merged     = _merged_year_results(deferred)

    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("Form 8621 — Line 16a Attachment", title))
    story.append(Paragraph("Daily Ratable Allocation of Excess Distribution", bold))
    story.append(Paragraph("IRC §1291(a)(1)(A) — Required Attachment per §6501(c)(8)", irc))
    story.append(HRFlowable(width="100%", thickness=1.5, color=DARK_BLUE, spaceAfter=6))
    story.append(Paragraph(f"Tax Year: {tax_year}  |  PFIC: {holding_name}  |  Client: {client_code}", normal))
    story.append(Paragraph(f"Total Excess Distribution: {_fmt(excess)}", bold))
    story.append(Spacer(1, 8))

    # ── Step 2: Year-by-Year Allocation & Tax ─────────────────────────────────
    story.append(Paragraph("Step 2 — Year-by-Year Allocation & Tax  [§1291(c)(2)]", sec))
    sorted_yrs = sorted(int(y) for y in year_bkts)
    yr_rows = [["Year", "Days", "Allocated Amount", "Rate", "Deferred Tax", "Classification"]]
    tot_days = tot_alloc = tot_tax = Decimal("0")

    for yr in sorted_yrs:
        bkt  = year_bkts[str(yr)]
        days = bkt["days"]
        amt  = _D(bkt["amount"])
        cls  = bkt["classification"]
        is_cur = cls == "current_year"
        is_pre = cls == "pre_pfic"
        yd   = merged.get(yr, {})
        tax  = yd.get("tax", Decimal("0")) if not is_cur and not is_pre else Decimal("0")

        if amt > 0 and not is_cur and not is_pre:
            rate = f"{tax / amt * 100:.1f}%"
        elif is_cur:
            rate = "ordinary"
        else:
            rate = "pre-PFIC"

        tax_cell = "ordinary income" if (is_cur or is_pre) else _fmt(tax)
        yr_rows.append([str(yr), str(days), _fmt(amt), rate, tax_cell, cls.replace("_", " ")])
        tot_days += days; tot_alloc += amt; tot_tax += tax

    yr_rows.append(["Total", str(int(tot_days)), _fmt(tot_alloc), "", _fmt(tot_tax), ""])
    yt = Table(yr_rows, colWidths=[0.5*inch, 0.5*inch, 1.2*inch, 0.7*inch, 1.1*inch, 1.2*inch])
    yt.setStyle(TableStyle([
        *_HDR._cmds,
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (5, 0), (5, -1), "LEFT"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E8EEF4")),
        ("FONTNAME",   (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    story.append(yt)

    # ── Step 3: §6621 Interest ────────────────────────────────────────────────
    prior_yrs = sorted(yr for yr, d in merged.items() if d["classification"] == "prior_pfic")
    if prior_yrs:
        int_end = merged[prior_yrs[0]].get("interest_end", "")[:10]
        story.append(Paragraph(
            f"Step 3 — §6621 Interest  [§6622 daily compound]  |  Interest accrues to: {int_end}", sec
        ))
        int_rows = [["Year", "Deferred Tax", "Filing Deadline (Interest Start)", "§6621 Interest"]]
        tot_it = Decimal("0")
        for yr in prior_yrs:
            d = merged[yr]
            i_start = d.get("interest_start", "")[:10]
            is_covid = i_start and i_start[5:7] not in ("04",)
            label = i_start + (" ⚠ COVID ext." if is_covid else "")
            int_rows.append([str(yr), _fmt(d["tax"]), label, _fmt(d["interest"])])
            tot_it += d["interest"]
        int_rows.append(["Total", "", "", _fmt(tot_it)])
        it = Table(int_rows, colWidths=[0.5*inch, 1.1*inch, 2.2*inch, 1.1*inch])
        it.setStyle(TableStyle([
            *_HDR._cmds,
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("ALIGN", (2, 0), (2, -1), "LEFT"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E8EEF4")),
            ("FONTNAME",   (0, -1), (-1, -1), "Helvetica-Bold"),
        ]))
        story.append(it)

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Per IRC §1291(a)(1)(A): excess distribution allocated ratably to each holding-period day. "
        "Pre-PFIC (pre-1987) and current-year days are ordinary income. "
        "Prior PFIC years bear tax at the historical maximum rate plus §6622 daily compound interest. "
        "Attach to filed Form 8621 — failure to attach leaves PFIC items open to IRS examination indefinitely (§6501(c)(8)).",
        small,
    ))

    doc.build(story)
    return buf.getvalue()
