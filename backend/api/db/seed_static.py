"""
Seed static reference data from the engine's tax_constants into the database.

Run once at deploy (idempotent — upserts, safe to re-run):
    python -m api.db.seed_static
    python -m api.db.seed_static --db sqlite:///./pfic_tool_dev.db

Data sources:
    IRS6621Rate      ← pfic_engine.core.tax_constants.IRS_6621_RATES
    MaxTaxRate       ← pfic_engine.core.tax_constants._MAX_TAX_RATE_TABLE
    FilingDeadline   ← pfic_engine.core.tax_constants._FILING_DEADLINES
"""
import sys
import os
from datetime import date

# Allow running as a script from the backend/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from api.db.models import (
    IRS6621Rate, MaxTaxRate, FilingDeadline,
    get_engine, create_tables,
)
from pfic_engine.core.tax_constants import (
    IRS_6621_RATES,
    _MAX_TAX_RATE_TABLE,
    _FILING_DEADLINES,
)


def _upsert_rate(session: Session, entry) -> None:
    existing = session.get(IRS6621Rate, (entry.year, entry.quarter))
    if existing:
        existing.rate = entry.rate
        existing.effective_from = entry.effective_from
        existing.effective_to = entry.effective_to
    else:
        session.add(IRS6621Rate(
            year=entry.year,
            quarter=entry.quarter,
            rate=entry.rate,
            effective_from=entry.effective_from,
            effective_to=entry.effective_to,
            source_bulletin=None,
        ))


def _upsert_max_rate(session: Session, year: int, rate) -> None:
    existing = session.get(MaxTaxRate, year)
    if existing:
        existing.rate = rate
    else:
        session.add(MaxTaxRate(year=year, rate=rate))


def _upsert_deadline(session: Session, tax_year: int, actual: date) -> None:
    statutory = date(actual.year, 4, 15)
    actual_str = actual.strftime("%Y-%m-%d")
    statutory_str = statutory.strftime("%Y-%m-%d")

    if actual == date(2020, 7, 15):
        reason = "covid_notice_2020_23"
    elif actual == date(2021, 5, 17):
        reason = "covid_notice_2021_21"
    elif actual.month == 4 and actual.day == 15:
        reason = "normal"
    else:
        reason = "weekend_shift"

    existing = session.get(FilingDeadline, tax_year)
    if existing:
        existing.statutory_date = statutory
        existing.actual_date = actual
        existing.adjustment_reason = reason
    else:
        session.add(FilingDeadline(
            tax_year=tax_year,
            statutory_date=statutory,
            actual_date=actual,
            adjustment_reason=reason,
        ))


def seed(db_url: str = None) -> dict:
    engine = get_engine(db_url) if db_url else get_engine()
    create_tables(engine)

    counts = {}
    with Session(engine) as session:
        # §6621 rates
        for entry in IRS_6621_RATES:
            _upsert_rate(session, entry)
        counts["irs_6621_rates"] = len(IRS_6621_RATES)

        # Max tax rates
        for year, rate in _MAX_TAX_RATE_TABLE.items():
            _upsert_max_rate(session, year, rate)
        counts["max_tax_rates"] = len(_MAX_TAX_RATE_TABLE)

        # Filing deadlines
        for tax_year, actual in _FILING_DEADLINES.items():
            _upsert_deadline(session, tax_year, actual)
        counts["filing_deadlines"] = len(_FILING_DEADLINES)

        session.commit()

    return counts


def verify(db_url: str = None) -> list[str]:
    """Spot-check seeded data. Returns list of failures (empty = all passed)."""
    from decimal import Decimal
    engine = get_engine(db_url) if db_url else get_engine()
    failures = []

    with Session(engine) as session:
        # 2022 Q1 = 3%
        r = session.get(IRS6621Rate, (2022, 1))
        if r is None or r.rate != Decimal("0.0300"):
            failures.append(f"2022 Q1 rate: expected 0.03, got {r.rate if r else None}")

        # 2023 Q4 = 8%
        r = session.get(IRS6621Rate, (2023, 4))
        if r is None or r.rate != Decimal("0.0800"):
            failures.append(f"2023 Q4 rate: expected 0.08, got {r.rate if r else None}")

        # 1989 Q2 = 12%
        r = session.get(IRS6621Rate, (1989, 2))
        if r is None or r.rate != Decimal("0.1200"):
            failures.append(f"1989 Q2 rate: expected 0.12, got {r.rate if r else None}")

        # COVID 2019 deadline = 2020-07-15
        d = session.get(FilingDeadline, 2019)
        if d is None or d.actual_date != date(2020, 7, 15):
            failures.append(f"2019 deadline: expected 2020-07-15, got {d.actual_date if d else None}")

        # COVID 2020 deadline = 2021-05-17
        d = session.get(FilingDeadline, 2020)
        if d is None or d.actual_date != date(2021, 5, 17):
            failures.append(f"2020 deadline: expected 2021-05-17, got {d.actual_date if d else None}")

        # 2018 max rate = 37%
        m = session.get(MaxTaxRate, 2018)
        if m is None or m.rate != Decimal("0.3700"):
            failures.append(f"2018 max rate: expected 0.37, got {m.rate if m else None}")

        # Count checks
        total_rates = session.query(IRS6621Rate).count()
        if total_rates != 157:
            failures.append(f"IRS6621Rate count: expected 157, got {total_rates}")

    return failures


if __name__ == "__main__":
    db_url = sys.argv[1] if len(sys.argv) > 1 else None
    print("Seeding static data...")
    counts = seed(db_url)
    for table, n in counts.items():
        print(f"  {table}: {n} rows")

    print("Verifying...")
    failures = verify(db_url)
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  ✗ {f}")
        sys.exit(1)
    else:
        print("All spot-checks passed.")
