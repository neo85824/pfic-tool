# PFIC Tool — Verification Plan

**Created:** 2026-05-12  
**Source:** Analysis of 8621calculator.com verification methodology + IRC §1291/§6621/§6622/§7503  
**Goal:** Match then exceed the verification standard of the best publicly available PFIC calculator

---

## Core Principle (from 8621calculator.com)

> "Form 8621 compliance is a **data science problem**. The goal is not to fill a field — it is to produce mathematically deterministic, independently reproducible results."

Every number in the output must have a traceable source: a statutory citation, a rate table entry, or a daily allocation row. No black boxes.

---

## Current Status vs Required

| Area | Status | Gap |
|------|--------|-----|
| §6622 daily compound interest | ✅ Implemented | Needs quarterly breakdown in output |
| §7503 filing deadlines | ✅ Table in `tax_constants.py` | **Needs audit against IRS IRBs** |
| COVID extensions (2019, 2020) | ✅ Implemented | OK |
| §6621 rate table (1987–2025) | ⚠️ In code, unverified | **Must verify each quarter against IRS IRB** |
| 2026 Q2 rate | ❌ Likely wrong (coded as 7%) | IRS IRB 2026-08 confirms **6%** — fix now |
| Per-lot allocation | ✅ FIFO implemented | OK |
| Leap year handling | ✅ Tested | OK |
| Line 16a daily attachment | ✅ Generates PDF | Needs IRC citation on each line |
| Internal consistency checks | ✅ 5 checks in `cross_check.py` | Expand — see Layer 1 below |
| Independent Interest Verifier | ❌ Not built | Build — see Layer 3 |
| Public regression test cases | ❌ Not public | Publish 5 existing cases |
| Dual-currency (Line 15e) | ❌ USD-only MVP | Phase 2A — OANDA spot rate |

---

## Three-Layer Verification Architecture

### Layer 1 — Engine Internal Checks (run on every calculation, auto)

These must ALL pass before a PDF is allowed to generate. If any fail, flag result as `⚠️ Requires Manual Review`.

**Already in `cross_check.py` (keep and expand):**

| Check | Rule |
|-------|------|
| Daily allocation sum | `sum(daily_allocations) ≈ excess_distribution` within $0.01 |
| Year-bucket sum | `sum(year_buckets.amount) ≈ excess_distribution` within $0.01 |
| Classification completeness | `prior_pfic + current_year + pre_pfic = excess_distribution` |
| FIFO lot unit total | `sum(lot.units) = total_reported_units` within 0.000001 |
| Interest positive for multi-year holds | If `years_held > 1` then `total_interest > 0` |

**Add these new checks:**

| Check | Rule | IRC |
|-------|------|-----|
| Filing deadline validity | Each year's due_date must exist in the §7503 table | §7503 |
| Interest rate in range | All quarterly rates must be between 1% and 20% | §6621 |
| Per-lot isolation | No lot's allocation bleeds into another lot's calculation | §1291(a)(1)(A) |
| Current-year bucket = ordinary income | Current year amount must not have tax/interest applied | §1291(a)(1)(C) |

---

### Layer 2 — Workpaper Auditability (output quality)

Every generated document must include:

- [ ] **Line 16a attachment**: daily row-by-row allocation (already generates — confirm format)
- [ ] **IRC citation on each computed value** — e.g. `§1291(c)(2)` next to each year's tax rate
- [ ] **Engine version number** on every export (already in output)
- [ ] **Calculation timestamp** (UTC) on every export
- [ ] **§6501(c)(8) warning** on Line 16a attachment — missing/defective attachment keeps IRS audit clock from starting
- [ ] **Quarterly interest breakdown** in Excel workpaper — show each quarter's rate, days, and interest amount (see Interest Verifier format below)

**Line 16a format target:**

```
Line 16a Supporting Statement — [Client] [PFIC Name] Tax Year YYYY
═══════════════════════════════════════════════════════════════════

Holding Period: YYYY-MM-DD → YYYY-MM-DD (Total: X,XXX days)   [§1291(a)(1)(A)]
Excess Distribution: $XX,XXX.XX                                [§1291(b)(2)(A)]
Daily Amount: $XX,XXX.XX ÷ X,XXX = $X.XXXXXX per day

Year   Days   Amount        Classification   Rate    Tax
────────────────────────────────────────────────────────
YYYY   365    $X,XXX.XX    prior_pfic       37.0%   $X,XXX.XX   [§1291(c)(2)]
YYYY   366    $X,XXX.XX    prior_pfic       39.6%   $X,XXX.XX
YYYY   365    $X,XXX.XX    current_year     —       (ordinary)  [§1291(a)(1)(C)]
────────────────────────────────────────────────────────
Total  X,XXX  $XX,XXX.XX

Verification: year-bucket sum $XX,XXX.XX = Excess Distribution $XX,XXX.XX ✓
```

---

### Layer 3 — External Verification Tools (build these)

#### 3a. Interest Verifier Tool (P1)

A standalone page/panel where a tax practitioner can:
1. Select distribution year and filing year
2. Engine auto-fills the §7503 due date (including COVID dates)
3. Enter a deferred tax amount
4. Get back a **quarterly interest breakdown**:

```
Distribution Year: 2019   Filing Year: 2025
Due Date: 2020-07-15 (COVID — Notice 2020-23)
Payment Date: 2026-04-15
Deferred Tax: $1,850.00

Quarter                  Rate   Days   Interest   Running Total
──────────────────────────────────────────────────────────────
2020-07-15 → 2020-09-30   3%     77    $11.68     $1,861.68
2020-10-01 → 2020-12-31   3%     92    $14.07     $1,875.75
...
──────────────────────────────────────────────────────────────
Total Interest: $XXX.XX
Grand Total: $X,XXX.XX
```

This lets practitioners independently verify any single year's interest without re-running the full calculation. Also useful for cross-checking against competitor tools.

#### 3b. Public Regression Test Cases (P1)

Publish the 5 existing test cases (from `pfic-tool-test-report.md`) as a public document with:
- Full inputs (all transactions)
- Expected outputs (all intermediate values, not just grand total)
- IRC citation for each expected value

Any user can run these against the engine and verify it produces identical results.

#### 3c. Defect Reporting Mechanism (P2)

Allow users to report calculation errors with:
- Their input data
- The IRC section they believe is violated
- Their expected result and why

Commit to 48-hour acknowledgment. A confirmed mathematical error = recalculation at no charge.

---

## Immediate Action Items (before next release)

### P0 — Fix Now

- [ ] **Verify and patch 2026 Q2 §6621 rate**: IRS IRB 2026-08 shows **6%**, not 7% — check `tax_constants.py`
- [ ] **Audit entire §6621 rate table** against IRS quarterly interest rate announcements (irs.gov/payments/quarterly-interest-rates) — every row from 1987 to present
- [ ] **Audit §7503 deadline table** against the actual calendar — verify every weekend/holiday shift year by year

### P1 — Next Sprint

- [ ] Add quarterly interest breakdown to Excel workpaper Sheet 2 (currently only yearly totals)
- [ ] Add IRC citation annotations to Line 16a PDF output
- [ ] Build Interest Verifier panel in the UI (can reuse the engine's `compute_deferred_tax_with_interest` logic)
- [ ] Add the 4 new Layer 1 checks to `cross_check.py`

### P2 — Phase 2A (with multi-currency)

- [ ] OANDA spot rate integration for Line 15e dual-currency reporting
- [ ] FRED as fallback FX source
- [ ] FX source logged in every workpaper (`oanda` / `fred` / `manual`)
- [ ] Warning when annual average rate is detected instead of spot rate

---

## Key IRC Citations Reference

| Calculation Step | Statutory Basis |
|-----------------|-----------------|
| Excess distribution definition | §1291(a)(1)(A) |
| 125% threshold test | §1291(b)(2)(A) |
| Three-period classification | §1291(a)(1)(B), §1291(a)(1)(C) |
| Historical max rate | §1291(c)(2) |
| Interest calculation period | §1291(c)(3)(A), §1291(c)(3)(B) |
| Daily compounding | §6622 |
| Quarterly underpayment rate | §6621(a)(2) |
| Filing deadline adjustment | §7503 |
| COVID 2019 extension | Notice 2020-23 |
| COVID 2020 extension | Notice 2021-21 |
| Statute of limitations | §6501(c)(8) |
| Line 16a attachment requirement | Form 8621 Instructions (Rev. 12/2025) |
| FX rate (Phase 2) | Rev. Rul. 2008-7, Reg. §1.988-1(d) |

---

## Key Difference vs 8621calculator.com

Their **one known data error**: §6621 rate table shows 2026 Q2 = 7%, but IRS IRB 2026-08 confirmed **6%**. Their table is manually maintained and lags IRS announcements.

Our target: automate the quarterly rate update so the table is always current. This is the single most impactful accuracy advantage we can build.
