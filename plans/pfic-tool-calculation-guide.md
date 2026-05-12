# PFIC Tool — Calculation Methodology & Input Guide

**Date:** 2026-05-13  
**Method covered:** IRC §1291 — Excess Distribution  
**Engine:** Python `Decimal` precision, §6622 daily compound interest, FIFO lot matching, §7503 filing deadlines

---

## Overview

Under IRC §1291, if a U.S. taxpayer receives an **excess distribution** from a Passive Foreign Investment Company (PFIC), the tax is calculated by spreading that excess back over every year the taxpayer held the fund — and charging the **highest tax rate in effect for each of those past years**, plus **interest** as if the tax had been unpaid since each year's filing deadline.

The result is almost always higher than ordinary capital gains rates, and the longer the hold with no distributions, the more punitive the outcome.

---

## What Inputs You Need

### 1. Client / Taxpayer Information

| Field | Why Needed |
|-------|-----------|
| Client code or name | Identifies the workpaper |
| Tax year being filed | Determines which distribution triggers the §1291 test and which filing deadline ends the interest accrual |

### 2. PFIC Holding Information

| Field | Why Needed |
|-------|-----------|
| PFIC name | Identifies the fund on Form 8621 |
| First PFIC year | The year the fund was classified as a PFIC — prior years may be pre-PFIC (different treatment) |
| Method | Must be "1291" (Excess Distribution) for this calculator |
| Currency | USD for now; FX conversion planned for Phase 2 |

### 3. Transaction History (every event since purchase)

You need **all** of the following event types, in chronological order:

#### a. Purchase(s)

| Field | Example | Why Needed |
|-------|---------|-----------|
| Date | 2015-09-15 | Start of holding period — determines how many days each calendar year the fund was held |
| Units | 996.819 | Number of shares/units acquired |
| Cost | $9,400.00 | Acquisition cost (for capital gain tracking, not used in §1291 excess calculation) |

If you bought in multiple batches (different dates), enter each lot separately. The engine uses **FIFO** (first-in, first-out) to match lots against sales.

#### b. Additional Purchases / Reinvestments

Same fields as above. Each reinvestment creates a new lot with its own acquisition date and unit count.

#### c. Distributions (every year)

| Field | Example | Why Needed |
|-------|---------|-----------|
| Date | 2022-12-31 | Identifies which tax year the distribution falls in |
| Amount | $18,013.71 | Total USD amount received |

Distributions are the core of the §1291 calculation. You need **every distribution from every prior year**, not just the year being filed — because the prior years are used to compute the 125% threshold.

> **Why prior years matter:** The test is: is the current year's distribution more than 125% of the average of the prior 3 years? If yes, only the excess above that threshold is subject to §1291. You cannot compute the threshold without the prior years' amounts.

#### d. Sales (if any)

| Field | Example | Why Needed |
|-------|---------|-----------|
| Date | 2023-06-30 | Determines which lots are consumed (FIFO) before the distribution event |
| Units | 60 | How many units were sold — removes the oldest lot(s) first |
| Proceeds | $15,000.00 | For capital gain reporting |

If units were sold before the distribution, the remaining lot determines the holding period start date and unit count for the §1291 allocation.

---

## How the Calculation Works — Step by Step

### Step 0: FIFO Lot Matching

Before any §1291 calculation, the engine resolves which shares are still held on the distribution date:

- Purchases create lots: `{acquisition_date, units, cost}`
- Sales consume lots starting from the oldest (FIFO)
- The **acquisition date of the remaining lot** is what determines the holding period start

**Example (CINDY / BOT):**
- Purchase 2015-09-15: 996.819 units — this lot is never sold, so holding period starts 2015-09-15

---

### Step 1: The 125% Test (IRC §1291(b)(2)(A))

**Formula:**

```
Prior 3-year average = sum of distributions in prior 3 years ÷ 3
Benchmark = Prior 3-year average × 1.25
Excess distribution = Current distribution − Benchmark
```

If the taxpayer has held the fund for fewer than 3 years, use the actual number of prior years as the denominator (not always 3).

If there are no prior distributions, the prior average is $0 and the **entire** current distribution is excess.

**The non-excess portion** (i.e., the benchmark amount) is ordinary income at the taxpayer's current rate. Only the excess goes through the §1291 machinery.

**Example (CINDY 2022):**
```
2019 distribution:  $9,203.35
2020 distribution: $14,533.19
2021 distribution: $17,747.52
                   ──────────
3-year total:      $41,484.06
Prior average:     $13,828.02

Benchmark (×1.25): $17,285.03
Current (2022):    $18,013.71
                   ──────────
Excess:               $728.68  →  rounded to $728.69
Ordinary income:   $17,285.03  (taxed at current rate, Line 16b)
```

**2023, 2024, 2025 would not trigger §1291** — those distributions are all below the benchmark, so no excess and no §1291 tax for those years.

---

### Step 2: Daily Allocation (IRC §1291(a)(1)(A))

The excess distribution is spread evenly across the **entire holding period**, one day at a time.

**Formula:**

```
Total holding days = sum of days in each calendar year from acquisition to tax year end
Daily amount = Excess distribution ÷ Total holding days
```

Each calendar year gets allocated: `daily_amount × days_in_that_year`

The **current tax year** (the year the distribution was received) is classified as `current_year` — it receives ordinary income treatment, no deferred tax, no interest.

Every **prior year** from the acquisition year onward is classified as `prior_pfic` — each one gets deferred tax + interest calculated separately.

**Example (CINDY 2022):**
```
Acquisition: 2015-09-15
Tax year end: 2022-12-31
Total holding days: 2,664

Daily amount: $728.69 ÷ 2,664 = $0.27353/day

Year   Days   Allocated     Class
2015   108    $  29.54      prior_pfic
2016   366    $ 100.08      prior_pfic
2017   365    $  99.80      prior_pfic
2018   365    $  99.80      prior_pfic
2019   365    $  99.80      prior_pfic
2020   366    $ 100.08      prior_pfic
2021   365    $  99.80      prior_pfic
2022   365    $  99.80      current_year
       ────   ─────────
       2,664  $ 728.70  ✓ (matches excess within rounding)
```

**Note on 2015:** The purchase was on September 15, 2015 (day 258 of 365). Days remaining in 2015 = 365 − 258 + 1 = 108 days. (The engine counts from purchase date inclusive through December 31.)

---

### Step 3: Deferred Tax Per Year (IRC §1291(c)(2))

For each `prior_pfic` year, the deferred tax is:

```
Deferred tax = Allocated amount × Highest marginal rate in effect for that year
```

The engine applies the **historical top ordinary income rate** for each year — not the current year's rate:

| Years | Highest Rate | Law |
|-------|-------------|-----|
| 2015–2017 | 39.6% | Pre-TCJA |
| 2018–present | 37.0% | TCJA (Tax Cuts and Jobs Act) |

This is the most common error in manual calculations — using a flat 37% for all years back to 2015 is wrong. The pre-TCJA rate of 39.6% applies to 2015, 2016, and 2017.

**Example (CINDY 2022):**
```
2015: $29.54 × 39.6% = $11.70
2016: $100.08 × 39.6% = $39.63
2017: $99.80 × 39.6% = $39.52
2018: $99.80 × 37.0% = $36.93
2019: $99.80 × 37.0% = $36.93
2020: $100.08 × 37.0% = $37.03
2021: $99.80 × 37.0% = $36.93
                       ───────
Total deferred tax:   $238.67  (engine: $238.65, minor rounding)
```

---

### Step 4: §6621 Interest Per Year (IRC §1291(c)(3), §6622)

For each prior year, interest accrues on the deferred tax from that **year's filing deadline** to the **current year's filing deadline**.

```
Interest start = Filing deadline of the prior year's return
Interest end   = Filing deadline of the current tax year's return
```

The filing deadline is **April 15** of the following year (§7503), adjusted for weekends/holidays. Special COVID extensions apply:
- **2019 returns** (normally due 2020-04-15) → extended to **2020-07-15** (Notice 2020-23)
- **2020 returns** (normally due 2021-04-15) → extended to **2021-05-17** (Notice 2021-21)

Interest compounds **daily** (§6622) using the **IRS underpayment rate** (§6621(a)(2)) which changes quarterly. The engine looks up the exact rate for each quarter the interest spans.

**Formula:**
```
For each quarter:
  daily_rate = annual_rate / 365
  interest = principal × ((1 + daily_rate) ^ days_in_quarter − 1)
  principal = principal + interest   (compounds into next quarter)

Total interest = final_balance − original_tax
```

**Example (CINDY 2022, year 2019 allocation):**
```
Deferred tax: $36.93
Interest start: 2020-07-15  (COVID extension — not the normal 2020-04-15)
Interest end:   2023-04-18  (2022 return due date)

Accrual period: ~2.75 years, across multiple IRS rate quarters
Interest: ~$4.28
```

**Why the COVID extension matters for interest:**
- The 2019 COVID extension (to 2020-07-15) *delays* the interest start for the 2018-year allocation. The interest clock doesn't start running until the extended due date — meaning slightly *less* interest than under a normal April 15 date.
- Conversely, interest on all prior years *stops* at the current tax year's filing deadline — so a later deadline (COVID) means interest accrues slightly *longer* into the current year.

---

### Step 5: Verification Checks

Before producing any output, the engine runs 5 internal consistency checks:

| Check | Rule |
|-------|------|
| Daily sum | `sum(year_buckets.amount) ≈ excess_distribution` within $0.02 |
| Tax sum | `sum(year_results.tax) ≈ total_deferred_tax` |
| Classification completeness | `prior_pfic + current_year amounts = excess` |
| FIFO unit total | `sum(lot.units) = total_held_units` |
| Interest positive | If any prior_pfic years exist, total_interest > 0 |

If any check fails, the result is flagged `⚠ Requires Manual Review` and no PDF is generated.

---

### Step 6: Form 8621 Part V Summary

| Line | Description | CINDY 2022 |
|------|-------------|-----------|
| 15e(1) | Non-excess ordinary income (Line 16b) | $17,285.03 |
| 15e(2) | Excess distribution | $728.69 |
| 16c | Additional deferred tax | $238.65 |
| 16f | §6621 interest | $42.25 |
| **16c+f** | **Grand total additional liability** | **$280.90** |

The non-excess portion ($17,285.03) goes on Line 16b as ordinary income — it's taxed at the taxpayer's current marginal rate, not the §1291 historical rates.

---

## Common Input Mistakes

| Mistake | Consequence |
|---------|------------|
| Wrong units (e.g. 996,819 instead of 996.819) | Holding period correct but daily allocation per unit is wildly wrong |
| Missing prior-year distributions | Prior 3-year average understated → benchmark too low → excess overstated |
| Using a flat 37% for all years | 2015–2017 allocations undertaxed (should be 39.6%) |
| Treating the current year as taxable (not ordinary income) | Double-counting — current year has no deferred tax in §1291 |
| Wrong acquisition date | Holding period days miscounted for the acquisition year |
| Ignoring reinvestments | Reinvestments are distributions + repurchases — both the income and the new lot must be recorded |

---

## Output Documents

After running a calculation, three documents can be exported:

| Document | Purpose | Required for Filing |
|----------|---------|-------------------|
| **Form 8621 Workpaper (PDF)** | Part V line-by-line summary with all computed values | No — supporting workpaper |
| **Line 16a Attachment (PDF)** | Day-by-day allocation statement required by Form 8621 Instructions | **Yes** — must be attached to return |
| **Excel Workpaper** | 3-sheet workbook: summary, year-by-year detail, transaction log | No — for review and audit file |

> **Critical:** The Line 16a attachment must be physically attached to the filed Form 8621. Without it, IRC §6501(c)(8) prevents the IRS audit statute of limitations from starting — the PFIC items on that return remain open to audit indefinitely.

---

## Quick Reference: Does This Year Trigger §1291?

| Year | Distribution | Benchmark | Excess | §1291? |
|------|-------------|-----------|--------|--------|
| 2019 | $9,203.35 | n/a (first year) | — | No — first year, no prior average |
| 2020 | $14,533.19 | ~$11,504 | — | No (below benchmark) |
| 2021 | $17,747.52 | ~$14,671 | — | No (below benchmark) |
| **2022** | **$18,013.71** | **$17,285.03** | **$728.69** | **Yes** |
| 2023 | $18,599.68 | $20,956.01 | — | No |
| 2024 | $20,977.73 | $22,650.38 | — | No |
| 2025 | $22,486.62 | $23,996.30 | — | No |

Only 2022 exceeds the 125% benchmark — all other years are below it and do not trigger §1291 excess distribution treatment.
