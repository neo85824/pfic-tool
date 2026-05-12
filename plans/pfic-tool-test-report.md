# PFIC Tool — Test Case Report

**Date:** 2026-05-12  
**Engine version:** dev (local SQLite)  
**Method:** §1291 Excess Distribution  
**All calculations use:** Python `Decimal` precision, §6622 daily compound interest, FIFO lot matching, §7503-adjusted filing deadlines

---

## Summary Table

| Case | Scenario | Excess Dist. | Add. Tax | §6621 Interest | **Grand Total** |
|------|----------|-------------|----------|---------------|----------------|
| 1 | Simple excess — 3-year hold | $1,562.50 | $383.10 | $27.95 | **$411.06** |
| 2 | COVID-year 2019 distribution | $4,875.00 | $1,205.70 | $105.97 | **$1,311.67** |
| 3 | One cent over 125% threshold | $0.01 | $0.00 | $0.00 | **$0.00** |
| 4 | Multi-lot FIFO + large distribution | $2,937.50 | $783.81 | $97.05 | **$880.87** |
| 5 | 7-year hold, zero prior distributions | $8,000.00 | $2,668.27 | $521.11 | **$3,189.38** |

---

## Case 1 — Simple Excess Distribution (3-Year Hold)

**Scenario:** US taxpayer holds a UCITS ETF (Vanguard FTSE All-World, Ireland-domiciled) starting 2020. Prior distributions are modest ($300 in 2020, $400 in 2021). In 2022 the fund pays a large $2,000 distribution.

**Transactions:**

| Date | Type | Units | Amount |
|------|------|-------|--------|
| 2020-01-15 | Purchase | 100 | $10,000.00 |
| 2020-12-31 | Distribution | — | $300.00 |
| 2021-06-30 | Distribution | — | $400.00 |
| 2022-06-30 | Distribution | — | $2,000.00 |

**125% Test (IRC §1291(b)(2)(A)):**
- Prior 2-year average (only 2 years of history): ($300 + $400) ÷ 2 = **$350.00**
- 125% threshold: $350.00 × 1.25 = **$437.50**
- Current distribution: $2,000.00
- **Excess: $2,000.00 − $437.50 = $1,562.50**
- Non-excess ordinary income: $437.50

**Daily Allocation (IRC §1291(a)(1)(A)):**
- Holding period: 2020-01-15 → 2022-12-31 = **1,082 days**
- Daily amount: $1,562.50 ÷ 1,082 = **$1.4440/day**

**Year-by-Year Results:**

| Year | Classification | Days | Allocated | Tax Rate | Tax | Interest | Total |
|------|----------------|------|-----------|----------|-----|----------|-------|
| 2020 | prior_pfic | 352 | $508.32 | 37% | $188.08 | $16.61 | $204.69 |
| 2021 | prior_pfic | 365 | $527.09 | 37% | $195.02 | $11.35 | $206.37 |
| 2022 | current_year | 365 | $527.09 | — | — | — | ordinary income |

**Final Numbers (Form 8621 Part V):**

| Line | Description | Amount |
|------|-------------|--------|
| 15e(1) | Non-excess ordinary income (Line 16b) | $437.50 |
| 15e(2) | Excess distribution | $1,562.50 |
| 16c | Additional tax | $383.10 |
| 16f | §6621 interest | $27.95 |
| **16e+16f** | **Grand total additional liability** | **$411.06** |

**Key observations:**
- Because the holding is only 2 years old, the 125% test uses a 2-year denominator (not 3), making the threshold lower and the excess larger.
- Interest is relatively low because the excess was allocated to recent years (2020–2021), meaning fewer years of compounding.

---

## Case 2 — COVID Tax Year 2019 (Interest Starts 2020-07-15)

**Scenario:** Investor holds an iShares World ETF since 2017 and receives a large $6,000 distribution in June 2019 — a tax year directly affected by the COVID filing extension (Notice 2020-23). Filing deadline shifted from 2020-04-15 to **2020-07-15**, meaning interest starts 3 months later than normal.

**Transactions:**

| Date | Type | Units | Amount |
|------|------|-------|--------|
| 2017-03-01 | Purchase | 1,000 | $50,000.00 |
| 2017-12-31 | Distribution | — | $800.00 |
| 2018-12-31 | Distribution | — | $900.00 |
| 2018-12-31 | Reinvestment | — | $100.00 |
| 2019-06-30 | Distribution | — | $6,000.00 |

**125% Test:**
- Prior avg (2017 + 2018 combined, 2 years held): ($800 + $900) ÷ 2 = **$850** — but reinvestment adds $100 to 2018 total, so ($800 + $1,000) ÷ 2 = **$900.00**
- 125% threshold: $900 × 1.25 = **$1,125.00**
- **Excess: $6,000 − $1,125 = $4,875.00**

**Year-by-Year Results:**

| Year | Classification | Days | Allocated | Tax Rate | Tax | Interest Start | Interest |
|------|----------------|------|-----------|----------|-----|----------------|----------|
| 2017 | prior_pfic | 306 | $1,439.91 | 39.6% | $570.21 | 2018-04-17 | $67.33 |
| 2018 | prior_pfic | 365 | $1,717.54 | 37% | $635.49 | **2020-07-15** ⚠️ | $38.65 |
| 2019 | current_year | 365 | $1,717.54 | — | — | — | — |

**COVID impact on Case 2:**
- The **2018 allocation year** has interest starting from the 2018 return's due date (2019-04-15 — normal).
- The **distribution year is 2019**, so interest accrues *through* the 2019 filing deadline of **2020-07-15** (COVID extension) — this is the current-year due date for §1291(c)(3)(A) interest calculation. Interest on both prior-year allocations therefore **stops** at the COVID-extended deadline, resulting in slightly *more* interest than a normal April 15 deadline would produce.

**Final Numbers:**

| Line | Amount |
|------|--------|
| Non-excess ordinary income | $1,125.00 |
| Excess distribution | $4,875.00 |
| Additional tax | $1,205.70 |
| §6621 interest | $105.97 |
| **Grand total** | **$1,311.67** |

---

## Case 3 — Edge Case: One Cent Over the 125% Threshold

**Scenario:** A taxpayer has received exactly $2,000 in distributions each of the past 3 years. In 2022 they receive $2,500.01 — one cent above the $2,500.00 threshold.

**125% Test:**
- Prior 3-year average: ($2,000 + $2,000 + $2,000) ÷ 3 = **$2,000.00**
- 125% threshold: **$2,500.00**
- Distribution: **$2,500.01**
- **Excess: $0.01**

**Result:** Even though the entire §1291 ratable allocation machinery runs, the allocated tax on $0.01 rounds to **$0.00**. Grand total additional liability = **$0.00**.

**What this demonstrates:**
- The engine correctly handles the boundary condition — $2,500.00 exactly would *not* be excess; $2,500.01 technically is.
- In practice, the per-day allocation of $0.01 over 1,461 holding days = $0.0000068/day, which rounds to $0.00 everywhere.
- The non-excess $2,500.00 is still ordinary income at the taxpayer's rate.

---

## Case 4 — Multi-Lot FIFO: Two Purchase Lots, Large 2023 Distribution

**Scenario:** Investor buys two lots of Xtrackers MSCI World ETF in 2018 and 2020 (50 shares each). In 2023 they receive a large $3,500 distribution after modest prior distributions. FIFO matching: Lot 1 (2018) is the oldest.

**Transactions:**

| Date | Type | Units | Amount | Note |
|------|------|-------|--------|------|
| 2018-03-01 | Purchase | 50 | $5,000.00 | Lot 1 |
| 2020-06-01 | Purchase | 50 | $8,000.00 | Lot 2 |
| 2021-12-31 | Distribution | — | $400.00 | — |
| 2022-12-31 | Distribution | — | $500.00 | — |
| 2023-06-30 | Sale | 60 | $15,000.00 | FIFO: all Lot 1 + 10 from Lot 2 |
| 2023-12-31 | Distribution | — | $3,500.00 | Large — triggers excess |

**125% Test for 2023 distribution:**
- Prior avg: ($400 + $500) ÷ 2 = **$450.00** (2 prior years)
- 125% threshold: $450 × 1.25 = **$562.50**
- **Excess: $3,500 − $562.50 = $2,937.50**

**Year-by-Year Results (Lot 2 remaining after sale, acquired 2020-06-01):**

| Year | Classification | Days | Allocated | Tax Rate | Tax | Interest |
|------|----------------|------|-----------|----------|-----|----------|
| 2020 | prior_pfic | 214 | $480.23 | 37% | $177.69 | $30.76 |
| 2021 | prior_pfic | 365 | $819.09 | 37% | $303.06 | $42.62 |
| 2022 | prior_pfic | 365 | $819.09 | 37% | $303.06 | $23.68 |
| 2023 | current_year | 365 | $819.09 | — | — | — |

**Final Numbers:**

| Line | Amount |
|------|--------|
| Non-excess ordinary income | $562.50 |
| Excess distribution | $2,937.50 |
| Additional tax | $783.81 |
| §6621 interest | $97.05 |
| **Grand total** | **$880.87** |

**FIFO note:** The sale consumed all 50 shares of Lot 1 (acquired 2018-03-01) and 10 shares of Lot 2. The remaining 40 shares of Lot 2 (acquired 2020-06-01) are what the distribution is allocated against — hence the holding period starts 2020-06-01 (214 days in 2020 remaining after purchase date).

---

## Case 5 — 7-Year Hold, No Prior Distributions

**Scenario:** Investor buys a Templeton Emerging Markets fund in 2015 and receives no distributions for 7 years. In 2022 the fund pays an $8,000 distribution — the first ever. Because the prior 3-year average is $0, the **entire $8,000 is excess**.

**Transactions:**

| Date | Type | Units | Amount |
|------|------|-------|--------|
| 2015-01-01 | Purchase | 200 | $20,000.00 |
| 2022-12-31 | Distribution | — | $8,000.00 |

**125% Test:**
- Prior 3-year average: $0.00 ÷ 3 = **$0.00**
- 125% threshold: **$0.00**
- **Entire $8,000 is excess distribution**

**Year-by-Year Results (holding period 2015-01-01 → 2022-12-31 = 2,922 days):**

| Year | Classification | Days | Allocated | Tax Rate | Tax | Interest |
|------|----------------|------|-----------|----------|-----|----------|
| 2015 | prior_pfic | 365 | $999.32 | 39.6% | $395.73 | $139.32 |
| 2016 | prior_pfic | 366 | $1,002.05 | 39.6% | $396.81 | $118.66 |
| 2017 | prior_pfic | 365 | $999.32 | 39.6% | $395.73 | $98.02 |
| 2018 | prior_pfic | 365 | $999.32 | **37.0%** | $369.75 | $67.96 |
| 2019 | prior_pfic | 365 | $999.32 | 37% | $369.75 | $42.90 |
| 2020 | prior_pfic | 366 | $1,002.05 | 37% | $370.76 | $32.74 |
| 2021 | prior_pfic | 365 | $999.32 | 37% | $369.75 | $21.51 |
| 2022 | current_year | 365 | $999.32 | — | — | — |

**Note:** Years 2015–2017 use the 39.6% max rate; 2018 onward uses 37% (TCJA rate reduction). The engine applies the correct historical rate to each year — it does **not** use the current year's rate retroactively.

**Final Numbers:**

| Line | Amount |
|------|--------|
| Non-excess ordinary income | $0.00 |
| Excess distribution | $8,000.00 |
| Additional tax | $2,668.27 |
| §6621 interest | $521.11 |
| **Grand total additional liability** | **$3,189.38** |

**Key takeaway:** A 7-year hold with no prior distributions is the most expensive PFIC scenario. The $521 interest bill on top of $2,668 in tax — totaling **39.9% effective burden on the $8,000 distribution** — demonstrates why PFIC rules are so punitive for long-held foreign funds.

---

## Engine Behavior Notes

### What worked correctly
- **125% threshold boundary** (Case 3): $0.01 over threshold correctly triggers excess but rounds to $0 tax — no false positives.
- **Historical max tax rates** (Case 5): 2015–2017 allocations taxed at 39.6%; 2018+ at 37%. Rate change applied per-year, not uniformly.
- **COVID filing deadline** (Case 2): 2019 tax year interest correctly accrues through 2020-07-15, not 2020-04-15.
- **FIFO lot matching** (Case 4): Acquisition date of the surviving lot (2020-06-01) correctly determines the holding period start, affecting how many days fall in 2020.
- **Zero prior average** (Case 5): When prior avg = $0, entire distribution is excess. Engine handles the divide-by-zero path via `safe_divide()`.
- **Holding < 3 years** (Cases 1, 2, 4): Denominator correctly reduces to actual number of prior years rather than always dividing by 3.

### Cross-validation
All 5 cases passed the internal `run_all_checks()` assertions:
- Year-bucket amounts sum to total excess distribution (within $0.02 rounding tolerance)
- Per-year tax sum matches `total_deferred_tax`
- `total_interest > 0` for all cases with prior_pfic years

### Known limitation
The §6621 rate table was compiled from historical knowledge and should be verified against official IRS IRB publications before production filing use.

---

## Practical Interpretation for Taxpayers

| Holding length | Prior distributions | Risk level | Why |
|----------------|---------------------|------------|-----|
| Short (1–2 yr) | Modest | Low | Few prior-PFIC years to allocate to; lower interest |
| Medium (3–5 yr) | Regular | Medium | 125% test more likely passed; interest accumulates |
| Long (7+ yr) | None | **Very high** | Entire distribution is excess; interest on 7+ years of deferred tax |
| Any | Large single spike | High | 125% test fails; triggers full §1291 regime |

**The most important compliance action:** Always attach the Line 16a daily allocation statement to the filed Form 8621. Without it, §6501(c)(8) prevents the IRS audit clock from starting — the return is effectively always open to audit on the PFIC items.
