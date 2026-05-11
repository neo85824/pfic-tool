"""
Known-answer test fixtures for §1291 regression suite.

Each fixture defines inputs and the pre-verified expected outputs.
Any change to the engine that alters these numbers requires explicit review.
"""
from datetime import date
from decimal import Decimal


# ── Fixture helpers ──────────────────────────────────────────────────────────

def D(s: str) -> Decimal:
    return Decimal(s)


# ── Test cases ───────────────────────────────────────────────────────────────

SIMPLE_SINGLE_LOT = {
    "description": "Single lot, single distribution, USD, no complexity",
    "acquisition_date": date(2020, 1, 15),
    "current_tax_year": 2022,
    "distribution_date": date(2022, 6, 30),
    "distribution_amount": D("5000.00"),
    "prior_distributions": [D("1000.00"), D("1200.00")],  # 2020, 2021
    "holding_years_before": 2,
    # 125% test: avg = (1000+1200)/2 = 1100; threshold = 1375; 5000 > 1375 → excess = 3625
    "expected_excess": D("3625.00"),
    # Holding: 2020-01-15 to 2022-06-30 = 897 days
    # daily = 3625/897 ≈ 4.04123...
    # Classification: 2020=prior, 2021=prior, 2022=current
}


MULTI_LOT_FIFO = {
    "description": "Two purchase lots, FIFO sale matching",
    "lots": [
        {"date": date(2019, 3, 1),  "units": D("100"), "cost_usd": D("8000.00")},
        {"date": date(2020, 7, 1),  "units": D("50"),  "cost_usd": D("5000.00")},
    ],
    "sale_date": date(2023, 4, 15),
    "sale_units": D("120"),
    "expected_lots_after": 1,          # 30 units remain from lot 2
    "expected_remaining_units": D("30"),
    "expected_lot2_units": D("30"),
}


PARTIAL_SALE_LOT_SPLIT = {
    "description": "Partial sale splits a lot; residual retains original acquisition date",
    "lots": [
        {"date": date(2021, 1, 1), "units": D("100"), "cost_usd": D("10000.00")},
    ],
    "sale_date": date(2024, 6, 15),
    "sale_units": D("60"),
    "expected_remaining_units": D("40"),
    "expected_residual_acquisition_date": date(2021, 1, 1),
    "expected_residual_cost_per_unit": D("100.00"),  # 10000/100
}


COVID_YEAR_2019 = {
    "description": "2019 tax year — COVID extension: deadline is 2020-07-15",
    "tax_year": 2019,
    "expected_deadline": date(2020, 7, 15),
    # Interest for 2019 allocation starts 2020-07-15 (not 2020-04-15)
}


COVID_YEAR_2020 = {
    "description": "2020 tax year — COVID extension: deadline is 2021-05-17",
    "tax_year": 2020,
    "expected_deadline": date(2021, 5, 17),
}


THRESHOLD_EXACT_125PCT = {
    "description": "Distribution equals exactly 125% of prior average — NOT excess",
    "prior_distributions": [D("2000.00"), D("2000.00"), D("2000.00")],
    "holding_years_before": 3,
    # avg = 2000; threshold = 2500; distribution = 2500 exactly → not excess
    "distribution": D("2500.00"),
    "expected_is_excess": False,
    "expected_excess_amount": D("0.00"),
}


THRESHOLD_ONE_CENT_OVER = {
    "description": "Distribution is one cent above 125% threshold — IS excess",
    "prior_distributions": [D("2000.00"), D("2000.00"), D("2000.00")],
    "holding_years_before": 3,
    "distribution": D("2500.01"),
    "expected_is_excess": True,
    "expected_excess_amount": D("0.01"),
}


HOLDING_UNDER_3_YEARS = {
    "description": "Holding period < 3 years: denominator = actual holding years",
    # Only 1 prior year of distributions
    "prior_distributions": [D("1000.00")],
    "holding_years_before": 1,
    # avg = 1000/1 = 1000; threshold = 1250
    "distribution": D("2000.00"),
    "expected_prior_avg": D("1000.00"),
    "expected_excess": D("750.00"),  # 2000 - 1250
}


PRE_PFIC_YEARS = {
    "description": "Holding started before 1987: pre-1987 days are ordinary income",
    "acquisition_date": date(1985, 6, 1),
    "distribution_date": date(1990, 12, 31),
    "current_tax_year": 1990,
    # 1985, 1986 days → pre_pfic (ordinary income)
    # 1987, 1988, 1989 → prior_pfic (deferred + interest)
    # 1990 → current_year (ordinary income)
    "excess_amount": D("10000.00"),
    "expected_classifications": {
        1985: "pre_pfic",
        1986: "pre_pfic",
        1987: "prior_pfic",
        1988: "prior_pfic",
        1989: "prior_pfic",
        1990: "current_year",
    },
}


ZERO_PRIOR_DISTRIBUTIONS = {
    "description": "No prior distributions: prior_avg = 0, entire distribution is excess",
    "prior_distributions": [],
    "holding_years_before": 2,
    "distribution": D("5000.00"),
    "expected_prior_avg": D("0.00"),
    "expected_excess": D("5000.00"),  # 5000 - 0 = 5000
}


MULTIPLE_DISTRIBUTIONS_125PCT = {
    "description": "Multiple years of distributions; 125% test uses most recent 3",
    # Prior distributions: year-3=$800, year-2=$900, year-1=$1000
    "prior_distributions": [D("800.00"), D("900.00"), D("1000.00")],
    "holding_years_before": 3,
    # avg = (800+900+1000)/3 = 900; threshold = 1125
    "distribution": D("2000.00"),
    "expected_prior_avg": D("900.00"),
    "expected_excess": D("875.00"),  # 2000 - 1125
}


# ── Interest calculation spot-check ─────────────────────────────────────────
# Verifiable independently: $1,000 deferred tax, 2022 Q1 rate = 3%, one quarter only

INTEREST_SINGLE_QUARTER = {
    "description": "Interest on $1,000 for 90 days at 3% annual (2022 Q1)",
    "principal": D("1000.00"),
    # Q1 2022: Jan 1 – Mar 31 = 90 days at 3% annual, daily compounding
    "start": date(2022, 1, 1),
    "end": date(2022, 3, 31),
    # P * ((1 + 0.03/365)^90 - 1)
    # daily_rate = 0.03/365 ≈ 0.00008219178...
    # factor = (1.00008219178)^90 ≈ 1.007402...
    # interest ≈ $7.40
    "expected_interest_approx": D("7.40"),
    "tolerance": D("0.10"),
}
