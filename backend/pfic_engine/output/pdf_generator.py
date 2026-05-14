"""
Form 8621 Part V calculation workpaper PDF.
Mirrors the FE Result page structure:
  1. 125% Test
  2. Excess Distribution by Lot
  3. Step 2 — Year-by-Year Allocation & Tax
  4. Step 3 — §6621 Interest
  5. Form 8621 Part V Summary
"""
from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable,
)
from reportlab.lib.enums import TA_RIGHT

MARGIN = 0.75 * inch
DARK_BLUE  = colors.HexColor("#1A365D")
MID_BLUE   = colors.HexColor("#2D6A9F")
LIGHT_BLUE = colors.HexColor("#EEF4FB")
ORANGE     = colors.HexColor("#FFF3CD")
GREY       = colors.HexColor("#F7F7F7")
WHITE      = colors.white


def _D(v):
    try:
        return Decimal(str(v))
    except Exception:
        return Decimal("0")


def _fmt(v) -> str:
    if v is None:
        return "—"
    try:
        return f"${_D(v):,.2f}"
    except Exception:
        return str(v)


def _pct(rate_decimal) -> str:
    try:
        return f"{_D(rate_decimal) * 100:.1f}%"
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


_HDR_STYLE = TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
    ("TEXTCOLOR",  (0, 0), (-1, 0), WHITE),
    ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE",   (0, 0), (-1, -1), 8),
    ("GRID",       (0, 0), (-1, -1), 0.4, colors.grey),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BLUE]),
])


def generate_form8621_workpaper(full_result: dict, holding_name: str, client_code: str) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    small  = ParagraphStyle("small",  parent=normal, fontSize=8)
    bold   = ParagraphStyle("bold",   parent=normal, fontName="Helvetica-Bold")
    title  = ParagraphStyle("title",  parent=normal, fontSize=13, fontName="Helvetica-Bold", spaceAfter=4, textColor=DARK_BLUE)
    sec    = ParagraphStyle("sec",    parent=normal, fontSize=10, fontName="Helvetica-Bold", textColor=DARK_BLUE, spaceBefore=12, spaceAfter=4)
    warn   = ParagraphStyle("warn",   parent=normal, fontSize=8, textColor=colors.HexColor("#C0392B"))

    tax_year   = full_result.get("tax_year", "")
    prior_avg  = _D(full_result.get("prior_3yr_average", "0"))
    cur_dist   = _D(full_result.get("current_year_distribution", "0"))
    non_excess = _D(full_result.get("non_excess_ordinary", "0"))
    excess     = _D(full_result.get("excess_distribution", "0"))
    total_tax  = _D(full_result.get("total_deferred_tax", "0"))
    total_int  = _D(full_result.get("total_interest", "0"))
    grand      = _D(full_result.get("grand_total", "0"))
    ordinary   = _D(full_result.get("total_ordinary_income", "0"))
    deferred   = full_result.get("deferred_tax_results", [])
    year_bkts  = full_result.get("year_buckets", {})
    warnings   = full_result.get("warnings", [])

    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("PFIC Form 8621 — Calculation Workpaper", title))
    story.append(Paragraph(f"Tax Year: {tax_year}  |  PFIC: {holding_name}  |  Client: {client_code}", normal))
    story.append(Paragraph("Method: §1291 Excess Distribution  |  Currency: USD", normal))
    story.append(HRFlowable(width="100%", thickness=2, color=DARK_BLUE, spaceAfter=8))

    if warnings:
        story.append(Paragraph("WARNINGS", bold))
        for w in warnings:
            story.append(Paragraph(f"• {w}", warn))
        story.append(Spacer(1, 6))

    # ── 1. 125% Test ──────────────────────────────────────────────────────────
    story.append(Paragraph("125% Test  [IRC §1291(b)(2)(A)]", sec))
    threshold = prior_avg * Decimal("1.25")
    test_data = [
        ["Item", "Amount"],
        ["15c — Current year distribution",          _fmt(cur_dist)],
        ["15b — Prior 3-year average",               _fmt(prior_avg)],
        ["Benchmark — 125% threshold",               _fmt(threshold)],
        ["15e(2) — Excess distribution",             _fmt(excess)],
        ["15e(1) — Non-excess ordinary income",      _fmt(non_excess)],
    ]
    t = Table(test_data, colWidths=[4.5 * inch, 1.8 * inch])
    t.setStyle(TableStyle([
        *_HDR_STYLE._cmds,
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("BACKGROUND", (0, 4), (-1, 4), ORANGE),
        ("FONTNAME",   (0, 4), (-1, 4), "Helvetica-Bold"),
    ]))
    story.append(t)

    # ── 2. Excess Distribution by Lot ─────────────────────────────────────────
    if deferred:
        story.append(Paragraph("Excess Distribution by Lot  [§1291(a)(1) proportional allocation]", sec))
        lot_data = [["Lot", "Acquired", "Units", "Excess Share", "Deferred Tax", "Interest", "Grand Total"]]
        tot_e = tot_t = tot_i = tot_g = Decimal("0")
        for i, dr in enumerate(deferred, 1):
            le = _D(dr.get("lot_excess", 0))
            tx = _D(dr.get("total_deferred_tax", 0))
            it = _D(dr.get("total_interest", 0))
            gt = _D(dr.get("grand_total", 0))
            units = _D(dr.get("units", 0))
            lot_data.append([
                f"L{i}", dr.get("acquisition_date", ""),
                f"{units:,.2f}", _fmt(le), _fmt(tx), _fmt(it), _fmt(gt),
            ])
            tot_e += le; tot_t += tx; tot_i += it; tot_g += gt
        lot_data.append(["Total", "", "", _fmt(tot_e), _fmt(tot_t), _fmt(tot_i), _fmt(tot_g)])

        cw = [0.45*inch, 0.85*inch, 0.75*inch, 0.9*inch, 0.9*inch, 0.8*inch, 0.9*inch]
        lt = Table(lot_data, colWidths=cw)
        lt.setStyle(TableStyle([
            *_HDR_STYLE._cmds,
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E8EEF4")),
            ("FONTNAME",   (0, -1), (-1, -1), "Helvetica-Bold"),
        ]))
        story.append(lt)

    # ── 3. Year-by-Year Allocation & Tax ──────────────────────────────────────
    story.append(Paragraph("Step 2 — Year-by-Year Allocation & Tax  [§1291(c)(2)]", sec))
    merged = _merged_year_results(deferred)
    sorted_yrs = sorted(int(y) for y in year_bkts)

    yr_data_rows = [["Year", "Days", "Allocated Amount", "Rate", "Deferred Tax"]]
    tot_days = tot_alloc = tot_tax_yr = Decimal("0")
    for yr in sorted_yrs:
        bkt  = year_bkts[str(yr)]
        days = bkt["days"]
        amt  = _D(bkt["amount"])
        cls  = bkt["classification"]
        is_cur = cls == "current_year"
        is_pre = cls == "pre_pfic"
        yd   = merged.get(yr, {})
        tax  = yd.get("tax", Decimal("0")) if not is_cur and not is_pre else Decimal("0")
        rate = _pct(tax / amt) if amt > 0 and not is_cur and not is_pre else ("ordinary" if is_cur else "pre-PFIC")
        yr_data_rows.append([
            str(yr), str(days), _fmt(amt), rate,
            "ordinary income" if (is_cur or is_pre) else _fmt(tax),
        ])
        tot_days += days; tot_alloc += amt; tot_tax_yr += tax

    yr_data_rows.append(["Total", str(int(tot_days)), _fmt(tot_alloc), "", _fmt(tot_tax_yr)])
    yt = Table(yr_data_rows, colWidths=[0.55*inch, 0.5*inch, 1.3*inch, 0.8*inch, 1.2*inch])
    yt.setStyle(TableStyle([
        *_HDR_STYLE._cmds,
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E8EEF4")),
        ("FONTNAME",   (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    story.append(yt)

    # ── 4. §6621 Interest ─────────────────────────────────────────────────────
    prior_yrs = sorted(yr for yr, d in merged.items() if d["classification"] == "prior_pfic")
    if prior_yrs:
        int_end = merged[prior_yrs[0]].get("interest_end", "")[:10]
        story.append(Paragraph(
            f"Step 3 — §6621 Interest  [§6622 daily compound]  |  Interest end: {int_end}", sec
        ))
        int_rows = [["Year", "Deferred Tax", "Filing Deadline", "§6621 Interest"]]
        tot_it = Decimal("0")
        for yr in prior_yrs:
            d = merged[yr]
            i_start = d.get("interest_start", "")[:10]
            is_covid = i_start and i_start[5:7] not in ("04",)
            label = i_start + (" ⚠ COVID" if is_covid else "")
            int_rows.append([str(yr), _fmt(d["tax"]), label, _fmt(d["interest"])])
            tot_it += d["interest"]
        int_rows.append(["Total", "", "", _fmt(tot_it)])
        it = Table(int_rows, colWidths=[0.5*inch, 1.2*inch, 1.4*inch, 1.2*inch])
        it.setStyle(TableStyle([
            *_HDR_STYLE._cmds,
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E8EEF4")),
            ("FONTNAME",   (0, -1), (-1, -1), "Helvetica-Bold"),
        ]))
        story.append(it)

    # ── 5. Form 8621 Part V Summary ───────────────────────────────────────────
    story.append(Paragraph("Form 8621 Part V — Summary", sec))
    sum_data = [
        ["Line", "Description", "Amount"],
        ["15e(1)", "Non-excess ordinary income (Line 16b)",        _fmt(non_excess)],
        ["15e(2)", "Excess distribution",                          _fmt(excess)],
        ["16c",    "Additional tax — prior PFIC years",            _fmt(total_tax)],
        ["16f",    "§6621 interest",                               _fmt(total_int)],
        ["16c+16f","Grand total additional liability",             _fmt(grand)],
        ["16b",    "Total ordinary income (pre-PFIC + current yr)",_fmt(ordinary)],
    ]
    st = Table(sum_data, colWidths=[0.9*inch, 4.0*inch, 1.4*inch])
    st.setStyle(TableStyle([
        *_HDR_STYLE._cmds,
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("BACKGROUND", (0, 5), (-1, 5), ORANGE),
        ("FONTNAME",   (0, 5), (-1, 5), "Helvetica-Bold"),
    ]))
    story.append(st)

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Generated by PFIC Tool (pfic_engine). §6621 rates from IRS IRB publications. "
        "§7503 deadlines include COVID extensions (Notice 2020-23, Notice 2021-21). "
        "This document does not constitute tax advice. Verify all figures before filing.",
        small,
    ))

    doc.build(story)
    return buf.getvalue()
