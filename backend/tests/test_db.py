"""
Tests for database models and seed data.
Uses an in-memory SQLite database — no PostgreSQL required for local dev.
"""
import pytest
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from api.db.models import (
    User, Client, PFICHolding, Transaction, Calculation,
    IRS6621Rate, MaxTaxRate, FilingDeadline,
    get_engine, create_tables,
)
from api.db.seed_static import seed, verify


@pytest.fixture(scope="module")
def engine():
    eng = get_engine("sqlite:///:memory:")
    create_tables(eng)
    return eng


@pytest.fixture(scope="module")
def seeded_engine(engine):
    seed("sqlite:///:memory:")
    # Re-use same engine — seed the in-memory engine directly
    from api.db.seed_static import _upsert_rate, _upsert_max_rate, _upsert_deadline
    from pfic_engine.core.tax_constants import IRS_6621_RATES, _MAX_TAX_RATE_TABLE, _FILING_DEADLINES
    with Session(engine) as session:
        for entry in IRS_6621_RATES:
            _upsert_rate(session, entry)
        for year, rate in _MAX_TAX_RATE_TABLE.items():
            _upsert_max_rate(session, year, rate)
        for tax_year, actual in _FILING_DEADLINES.items():
            _upsert_deadline(session, tax_year, actual)
        session.commit()
    return engine


# ── Table creation ───────────────────────────────────────────────────────────

def test_tables_created(engine):
    from sqlalchemy import inspect
    insp = inspect(engine)
    tables = insp.get_table_names()
    for expected in [
        "users", "clients", "pfic_holdings", "transactions", "calculations",
        "irs_6621_rates", "max_tax_rates", "filing_deadlines",
        "eoy_values", "fx_rate_cache",
    ]:
        assert expected in tables, f"Table '{expected}' not found"


# ── Static data counts ───────────────────────────────────────────────────────

def test_seed_rate_count(seeded_engine):
    with Session(seeded_engine) as s:
        assert s.query(IRS6621Rate).count() == 157


def test_seed_max_tax_rates(seeded_engine):
    with Session(seeded_engine) as s:
        assert s.query(MaxTaxRate).count() > 0


def test_seed_filing_deadlines(seeded_engine):
    with Session(seeded_engine) as s:
        assert s.query(FilingDeadline).count() > 0


# ── Spot-check values ────────────────────────────────────────────────────────

def test_spot_2022_q1_rate(seeded_engine):
    with Session(seeded_engine) as s:
        r = s.get(IRS6621Rate, (2022, 1))
        assert r is not None
        assert r.rate == Decimal("0.0300")


def test_spot_2023_q4_rate(seeded_engine):
    with Session(seeded_engine) as s:
        r = s.get(IRS6621Rate, (2023, 4))
        assert r.rate == Decimal("0.0800")


def test_spot_covid_2019_deadline(seeded_engine):
    with Session(seeded_engine) as s:
        d = s.get(FilingDeadline, 2019)
        assert d.actual_date == date(2020, 7, 15)
        assert d.adjustment_reason == "covid_notice_2020_23"


def test_spot_covid_2020_deadline(seeded_engine):
    with Session(seeded_engine) as s:
        d = s.get(FilingDeadline, 2020)
        assert d.actual_date == date(2021, 5, 17)
        assert d.adjustment_reason == "covid_notice_2021_21"


def test_spot_max_rate_2018(seeded_engine):
    with Session(seeded_engine) as s:
        m = s.get(MaxTaxRate, 2018)
        assert m.rate == Decimal("0.3700")


def test_seed_idempotent(seeded_engine):
    """Running seed twice must not raise or duplicate rows."""
    from api.db.seed_static import _upsert_rate
    from pfic_engine.core.tax_constants import IRS_6621_RATES
    with Session(seeded_engine) as s:
        for entry in IRS_6621_RATES:
            _upsert_rate(s, entry)
        s.commit()
        assert s.query(IRS6621Rate).count() == 157


# ── CRUD: User / Client / Holding / Transaction ──────────────────────────────

def test_create_user(engine):
    with Session(engine) as s:
        user = User(email="tax@example.com", hashed_password="hashed_pw_here")
        s.add(user)
        s.commit()
        s.refresh(user)
        assert user.id is not None
        assert user.role == "preparer"


def test_create_client_and_holding(engine):
    with Session(engine) as s:
        user = User(email="cpa2@example.com", hashed_password="pw")
        s.add(user)
        s.flush()

        client = Client(user_id=user.id, client_code="CLIENT-001")
        s.add(client)
        s.flush()

        holding = PFICHolding(
            client_id=client.id,
            pfic_name="Example UCITS Fund",
            currency="USD",
            method="1291",
            first_pfic_year=2018,
        )
        s.add(holding)
        s.flush()

        txn = Transaction(
            holding_id=holding.id,
            txn_date=date(2020, 3, 15),
            txn_type="purchase",
            units=Decimal("100.0"),
            total_value_usd=Decimal("10000.00"),
        )
        s.add(txn)
        s.commit()

        fetched = s.query(Transaction).filter_by(holding_id=holding.id).first()
        assert fetched is not None
        assert fetched.txn_type == "purchase"


def test_calculation_jsonb(engine):
    """Calculation.full_result survives a round-trip through JSONType."""
    with Session(engine) as s:
        user = User(email="cpa3@example.com", hashed_password="pw")
        s.add(user)
        s.flush()
        client = Client(user_id=user.id, client_code="CLIENT-002")
        s.add(client)
        s.flush()
        holding = PFICHolding(client_id=client.id, pfic_name="Test Fund", currency="USD", method="1291")
        s.add(holding)
        s.flush()

        payload = {
            "year_buckets": {"2020": {"amount": "1234.56", "classification": "prior_pfic"}},
            "total_deferred_tax": "456.79",
        }
        calc = Calculation(
            holding_id=holding.id,
            tax_year=2022,
            method="1291",
            engine_version="v0.1.0",
            full_result=payload,
            grand_total=Decimal("500.00"),
        )
        s.add(calc)
        s.commit()
        s.refresh(calc)

        assert calc.full_result["total_deferred_tax"] == "456.79"


def test_unique_constraint_client_code(engine):
    """Two clients with the same code under the same user must fail."""
    import sqlalchemy.exc
    with Session(engine) as s:
        user = User(email="cpa4@example.com", hashed_password="pw")
        s.add(user)
        s.flush()
        s.add(Client(user_id=user.id, client_code="DUP-001"))
        s.flush()
        s.add(Client(user_id=user.id, client_code="DUP-001"))
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            s.flush()
