"""
TC-MAIN Ground Truth Script — Independent SSoT for all expected values.

Uses only stdlib (decimal, datetime). No pfic_engine imports.
Run: python tests/ground_truth.py

Reproduces every number from PFIC_Test_Plan_v2.md TC-MAIN scenario from scratch.
Compare output against hand-worked numbers in the test plan.
"""
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP, getcontext

getcontext().prec = 28

# ── Inputs ───────────────────────────────────────────────────────────────────

LOTS = [
    {"acq": date(2021, 9, 6),  "units": Decimal("2496.45")},
    {"acq": date(2021, 9, 7),  "units": Decimal("2127.66")},
    {"acq": date(2021, 9, 8),  "units": Decimal("2130.68")},
    {"acq": date(2022, 10, 26), "units": Decimal("127.04")},
    {"acq": date(2022, 11, 27), "units": Decimal("123.46")},
    {"acq": date(2022, 11, 28), "units": Decimal("123.24")},
]

DIST_2021 = Decimal("658.59")
DIST_2022 = Decimal("2483.45")
DIST_DATE_2022 = date(2022, 12, 31)
TAX_YEAR = 2022
MAX_RATE = Decimal("0.37")
FILING_DEADLINE_2021 = date(2022, 4, 18)  # §7503 weekend shift
FILING_DEADLINE_2022 = date(2023, 4, 18)

# §6621 rates (quarterly) used in 2022-04-18 → 2023-04-18
RATES_2022_Q2 = Decimal("0.04")
RATES_2022_Q3 = Decimal("0.05")
RATES_2022_Q4 = Decimal("0.06")
RATES_2023_Q1 = Decimal("0.07")
RATES_2023_Q2 = Decimal("0.07")


def R(x):
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def check(label, actual, expected, tol=Decimal("0.01")):
    ok = abs(actual - expected) <= tol
    marker = "✓" if ok else "✗ FAIL"
    print(f"  {label}: {actual:.4f}  (expected {expected})  {marker}")
    return ok


# ── Phase 2: 125% Test ───────────────────────────────────────────────────────
print("\n[TC-MAIN Phase 2 — 125% Test]")
prior_avg = DIST_2021 / Decimal("1")
threshold = R(prior_avg * Decimal("1.25"))
excess = R(DIST_2022 - threshold)
non_excess = DIST_2022 - excess
print(f"  Prior avg: {prior_avg}")
check("Threshold", threshold, Decimal("823.24"), Decimal("0.00"))
check("Excess", excess, Decimal("1660.21"), Decimal("0.00"))
check("Non-excess", non_excess, Decimal("823.24"), Decimal("0.00"))

# ── Phase 3: Lot proportional shares ────────────────────────────────────────
print("\n[TC-MAIN Phase 3 — Lot Shares]")
total_units = sum(lot["units"] for lot in LOTS)
shares = []
running = Decimal("0")
for i, lot in enumerate(LOTS):
    if i < len(LOTS) - 1:
        s = R(lot["units"] / total_units * excess)
    else:
        s = excess - running
    shares.append(s)
    running += s

EXPECTED_SHARES = [Decimal("581.41"), Decimal("495.52"), Decimal("496.23"),
                   Decimal("29.59"),  Decimal("28.75"),  Decimal("28.71")]
for i, (s, e) in enumerate(zip(shares, EXPECTED_SHARES)):
    check(f"L{i+1} share", s, e, Decimal("0.00"))
print(f"  Sum: {sum(shares)}", "✓" if sum(shares) == excess else "✗ FAIL")

# ── Phase 4: Daily allocation ────────────────────────────────────────────────
print("\n[TC-MAIN Phase 4 — Daily Allocation]")

def year_days_in_range(start, end_excl):
    """Days per year from start through end_excl-1 (end_excl is excluded)."""
    result = {}
    cur = start
    while cur < end_excl:
        year = cur.year
        year_end = min(date(year, 12, 31), end_excl - timedelta(days=1))
        days = (year_end - cur).days + 1
        result[year] = result.get(year, 0) + days
        cur = date(year + 1, 1, 1)
        if cur >= end_excl:
            break
        # Check remaining
        if year_end < end_excl - timedelta(days=1):
            pass
    return result

def allocate(acq, dist_date, share, tax_year):
    total_days = (dist_date - acq).days  # exclusive
    buckets = {}
    cur = acq
    years_done = []
    while cur < dist_date:
        yr = cur.year
        yr_end = min(date(yr, 12, 31), dist_date - timedelta(days=1))
        days = (yr_end - cur).days + 1
        buckets[yr] = days
        years_done.append(yr)
        cur = date(yr + 1, 1, 1)
        if cur >= dist_date:
            break
        if yr_end >= dist_date - timedelta(days=1):
            break
    # Ensure last bucket covers remaining
    if cur < dist_date:
        yr = cur.year
        yr_end = dist_date - timedelta(days=1)
        days = (yr_end - cur).days + 1
        buckets[yr] = buckets.get(yr, 0) + days

    return total_days, buckets

EXPECTED_LOT_DATA = [
    (481, 117, 364, Decimal("141.42"), Decimal("439.99")),
    (480, 116, 364, Decimal("119.75"), Decimal("375.77")),
    (479, 115, 364, Decimal("119.14"), Decimal("377.09")),
    ( 66,   0,  66, Decimal("0.00"),   Decimal("29.59")),
    ( 34,   0,  34, Decimal("0.00"),   Decimal("28.75")),
    ( 33,   0,  33, Decimal("0.00"),   Decimal("28.71")),
]

prior_total = Decimal("0")
current_total = Decimal("0")
lot_prior_amounts = []

for i, (lot, share, (exp_total, exp_2021, exp_2022, exp_pa, exp_ca)) in enumerate(
    zip(LOTS, shares, EXPECTED_LOT_DATA)
):
    total_days, buckets = allocate(lot["acq"], DIST_DATE_2022, share, TAX_YEAR)
    daily = share / Decimal(str(total_days))

    days_2021 = buckets.get(2021, 0)
    days_2022 = buckets.get(2022, 0)

    # Allocate: all years except last get daily×days, last gets remainder
    years = sorted(buckets.keys())
    running_amt = Decimal("0")
    amounts = {}
    for j, yr in enumerate(years):
        if j < len(years) - 1:
            amt = daily * Decimal(str(buckets[yr]))
        else:
            amt = share - running_amt
        amounts[yr] = amt
        running_amt += amt

    prior_amt = amounts.get(2021, Decimal("0"))
    curr_amt = amounts.get(2022, Decimal("0"))
    lot_prior_amounts.append(prior_amt)
    prior_total += prior_amt
    current_total += curr_amt

    ok_total = total_days == exp_total
    ok_2021 = days_2021 == exp_2021
    ok_2022 = days_2022 == exp_2022
    ok_pa = abs(prior_amt - exp_pa) < Decimal("0.01")
    ok_ca = abs(curr_amt - exp_ca) < Decimal("0.01")
    all_ok = all([ok_total, ok_2021, ok_2022, ok_pa, ok_ca])
    print(f"  L{i+1}: total={total_days} ({'✓' if ok_total else '✗'})  "
          f"2021={days_2021} ({'✓' if ok_2021 else '✗'})  "
          f"2022={days_2022} ({'✓' if ok_2022 else '✗'})  "
          f"prior_amt={prior_amt:.2f} ({'✓' if ok_pa else '✗'})  "
          f"curr_amt={curr_amt:.2f} ({'✓' if ok_ca else '✗'})")

check("Prior year total (2021)", prior_total, Decimal("380.31"))
check("Current year total (2022)", current_total, Decimal("1279.90"))
sum_check = prior_total + current_total
print(f"  Prior + Current = {sum_check:.2f}  {'✓' if abs(sum_check - excess) < Decimal('0.01') else '✗ FAIL (should == ' + str(excess) + ')'}")

# ── Phase 5: §6621 Interest ───────────────────────────────────────────────────
print("\n[TC-MAIN Phase 5 — §6621 Interest]")

def daily_compound_interest(principal, annual_rate, n_days):
    """P × ((1 + r/365)^n - 1)"""
    daily_rate = annual_rate / Decimal("365")
    factor = (Decimal("1") + daily_rate) ** n_days
    return principal * (factor - Decimal("1"))

def l_interest(prior_amt, tax_rate=MAX_RATE):
    if prior_amt == Decimal("0"):
        return Decimal("0"), Decimal("0")
    tax = prior_amt * tax_rate
    # Period: 2022-04-18 → 2023-04-18 (5 quarters, inclusive counting)
    # Q2 2022: 74d@4%, Q3: 92d@5%, Q4: 92d@6%, Q1 2023: 90d@7%, Q2 2023 18d@7%
    balance = tax
    for rate, days in [(RATES_2022_Q2, 74), (RATES_2022_Q3, 92), (RATES_2022_Q4, 92),
                       (RATES_2023_Q1, 90), (RATES_2023_Q2, 18)]:
        balance = balance * ((Decimal("1") + rate / Decimal("365")) ** days)
    interest = balance - tax
    return tax, interest

EXPECTED_INTEREST = [Decimal("3.04"), Decimal("2.58"), Decimal("2.56"),
                     Decimal("0.00"), Decimal("0.00"), Decimal("0.00")]
total_tax = Decimal("0")
total_interest = Decimal("0")
for i, (prior_amt, exp_i) in enumerate(zip(lot_prior_amounts, EXPECTED_INTEREST)):
    tax, interest = l_interest(prior_amt)
    total_tax += tax
    total_interest += interest
    if i < 3:
        check(f"L{i+1} interest", interest, exp_i, Decimal("0.02"))
    else:
        ok = interest == Decimal("0")
        print(f"  L{i+1} interest: 0 {'✓' if ok else '✗'}")

check("Total interest", total_interest, Decimal("8.19"), Decimal("0.05"))

# ── Phase 6: Grand Total ──────────────────────────────────────────────────────
print("\n[TC-MAIN Phase 6 — Grand Total]")
check("Total deferred tax", total_tax, Decimal("140.72"), Decimal("0.02"))
check("Total interest", total_interest, Decimal("8.19"), Decimal("0.05"))
grand_total = total_tax + total_interest
check("Grand total", grand_total, Decimal("148.90"), Decimal("0.05"))

# ── Phase 7: Cross-checks ─────────────────────────────────────────────────────
print("\n[TC-MAIN Phase 7 — Cross-checks]")
print(f"  Check 1 — lot excess sum = {sum(shares):.2f} == {excess} {'✓' if sum(shares)==excess else '✗'}")
sum_allocs = prior_total + current_total
print(f"  Check 2 — year alloc sum = {sum_allocs:.2f} (vs excess {excess}) {'✓' if abs(sum_allocs-excess)<Decimal('0.01') else '✗'}")
print(f"  Check 3 — prior + current = {prior_total:.2f} + {current_total:.2f} = {sum_allocs:.2f} {'✓' if abs(sum_allocs-excess)<Decimal('0.01') else '✗'}")
print(f"  Check 4 — interest > 0: {total_interest:.4f} {'✓' if total_interest > 0 else '✗'}")
print(f"  Check 5 — 2021 deadline = {FILING_DEADLINE_2021} {'✓' if FILING_DEADLINE_2021 == date(2022,4,18) else '✗'}")

print()
