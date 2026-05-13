"""
SQLAlchemy ORM models — MVP tables only.

DATABASE_URL env var controls the connection:
  - Production:  postgresql://user:pass@host/pfic_tool
  - Local dev:   sqlite:///./pfic_tool_dev.db  (default fallback)
"""
import os
import uuid
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    Column, String, Integer, Numeric, Date, DateTime, Text,
    ForeignKey, UniqueConstraint, CheckConstraint, Boolean,
    create_engine, event,
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.types import TypeDecorator, TEXT
import json

_db_url = os.getenv("DATABASE_URL", "sqlite:///./pfic_tool_dev.db")
# Render provides postgres:// but SQLAlchemy 2.x requires postgresql://
DATABASE_URL = _db_url.replace("postgres://", "postgresql://", 1)

# ── JSONB compatibility shim (SQLite stores JSON as TEXT) ────────────────────

class JSONType(TypeDecorator):
    """JSONB on PostgreSQL; TEXT+json on SQLite."""
    impl = TEXT
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import JSONB
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(TEXT())

    def process_bind_param(self, value, dialect):
        if dialect.name != "postgresql" and value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if dialect.name != "postgresql" and value is not None:
            return json.loads(value)
        return value


# ── UUID compatibility shim ──────────────────────────────────────────────────

class UUIDType(TypeDecorator):
    """UUID on PostgreSQL; VARCHAR(36) on SQLite."""
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID
            return dialect.type_descriptor(UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return str(value)


def new_uuid() -> str:
    return str(uuid.uuid4())


# ── Base ─────────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── Account tables ───────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(UUIDType, primary_key=True, default=new_uuid)
    email = Column(String(200), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role = Column(String(50), nullable=False, default="preparer")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    clients = relationship("Client", back_populates="user")


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (UniqueConstraint("user_id", "client_code"),)

    id = Column(UUIDType, primary_key=True, default=new_uuid)
    user_id = Column(UUIDType, ForeignKey("users.id"), nullable=False)
    client_code = Column(String(50), nullable=False)
    tax_year_start = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="clients")
    holdings = relationship("PFICHolding", back_populates="client", cascade="all, delete-orphan")


# ── PFIC holding tables ──────────────────────────────────────────────────────

class PFICHolding(Base):
    __tablename__ = "pfic_holdings"

    id = Column(UUIDType, primary_key=True, default=new_uuid)
    client_id = Column(UUIDType, ForeignKey("clients.id"), nullable=False)
    pfic_name = Column(String(300), nullable=False)
    reference_id = Column(String(50))       # IRS Reference ID (alphanumeric)
    share_class = Column(String(100))
    currency = Column(String(3), nullable=False, default="USD")
    method = Column(String(20), nullable=False, default="1291")  # MVP: only '1291'
    first_pfic_year = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="holdings")
    transactions = relationship("Transaction", back_populates="holding",
                                order_by="Transaction.txn_date", cascade="all, delete-orphan")
    calculations = relationship("Calculation", back_populates="holding", cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUIDType, primary_key=True, default=new_uuid)
    holding_id = Column(UUIDType, ForeignKey("pfic_holdings.id"), nullable=False)
    txn_date = Column(Date, nullable=False)
    txn_type = Column(String(30), nullable=False)
    # Valid types: purchase | sale | distribution | reinvestment | return_of_capital
    units = Column(Numeric(20, 8))
    total_value_usd = Column(Numeric(20, 6), nullable=False)
    notes = Column(Text)
    imported_at = Column(DateTime, default=datetime.utcnow)

    holding = relationship("PFICHolding", back_populates="transactions")


class Calculation(Base):
    """Immutable snapshot of a completed calculation run."""
    __tablename__ = "calculations"
    __table_args__ = (UniqueConstraint("holding_id", "tax_year"),)

    id = Column(UUIDType, primary_key=True, default=new_uuid)
    holding_id = Column(UUIDType, ForeignKey("pfic_holdings.id"), nullable=False)
    tax_year = Column(Integer, nullable=False)
    method = Column(String(20), nullable=False, default="1291")
    status = Column(String(20), nullable=False, default="draft")  # draft|final|filed
    engine_version = Column(String(50))     # git describe tag at run time

    # Summary columns — redundant but fast to query without unpacking JSONB
    total_excess_dist = Column(Numeric(20, 2))
    additional_tax = Column(Numeric(20, 2))
    total_interest = Column(Numeric(20, 2))
    ordinary_income = Column(Numeric(20, 2))
    grand_total = Column(Numeric(20, 2))

    full_result = Column(JSONType, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    holding = relationship("PFICHolding", back_populates="calculations")


# ── Static reference tables (seeded at deploy, read-only at runtime) ─────────

class IRS6621Rate(Base):
    """§6621 quarterly underpayment rates 1987–present."""
    __tablename__ = "irs_6621_rates"
    __table_args__ = (
        CheckConstraint("quarter BETWEEN 1 AND 4"),
    )

    year = Column(Integer, primary_key=True)
    quarter = Column(Integer, primary_key=True)
    rate = Column(Numeric(6, 4), nullable=False)     # e.g. 0.0700 = 7%
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=False)
    source_bulletin = Column(String(50))


class MaxTaxRate(Base):
    """Historical maximum ordinary income tax rates by year."""
    __tablename__ = "max_tax_rates"

    year = Column(Integer, primary_key=True)
    rate = Column(Numeric(6, 4), nullable=False)     # e.g. 0.3700 = 37%
    notes = Column(Text)


class FilingDeadline(Base):
    """§7503-adjusted filing deadlines by tax year."""
    __tablename__ = "filing_deadlines"

    tax_year = Column(Integer, primary_key=True)
    statutory_date = Column(Date, nullable=False)    # Usually April 15
    actual_date = Column(Date, nullable=False)        # After §7503 / COVID adjustments
    adjustment_reason = Column(String(100))          # 'normal'|'weekend'|'covid_2020'|etc.


# ── Deferred (created empty, not populated in MVP) ───────────────────────────

class EOYValue(Base):
    """Year-end market values — needed for §1296 MTM (Phase 2B)."""
    __tablename__ = "eoy_values"

    id = Column(UUIDType, primary_key=True, default=new_uuid)
    holding_id = Column(UUIDType, ForeignKey("pfic_holdings.id"), nullable=False)
    tax_year = Column(Integer, nullable=False)
    eoy_price = Column(Numeric(20, 6), nullable=False)
    eoy_date = Column(Date)
    __table_args__ = (UniqueConstraint("holding_id", "tax_year"),)


class FXRateCache(Base):
    """FX rate cache — needed for multi-currency support (Phase 2A)."""
    __tablename__ = "fx_rate_cache"

    currency = Column(String(3), primary_key=True)
    rate_date = Column(Date, primary_key=True)
    source = Column(String(20), primary_key=True)
    rate = Column(Numeric(16, 8), nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow)


# ── Engine factory ───────────────────────────────────────────────────────────

def get_engine(url: str = DATABASE_URL):
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args)

    # Enable WAL mode and foreign keys for SQLite
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(conn, _rec):
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA journal_mode=WAL")

    return engine


def create_tables(engine=None):
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(engine)
    return engine
