"""FastAPI dependency injection: DB session and no-auth default user."""
from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from api.db.models import User, get_engine, create_tables

DEFAULT_USER_EMAIL = "default@pfictool.local"

_engine = None


def get_engine_once():
    global _engine
    if _engine is None:
        _engine = get_engine()
        create_tables(_engine)
    return _engine


def get_db() -> Generator[Session, None, None]:
    engine = get_engine_once()
    with Session(engine) as session:
        yield session


def get_current_user(db: Session = Depends(get_db)) -> User:
    """Return the single shared user — no login required."""
    user = db.query(User).filter_by(email=DEFAULT_USER_EMAIL).first()
    if not user:
        user = User(
            email=DEFAULT_USER_EMAIL,
            hashed_password="no-auth",
            role="preparer",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
