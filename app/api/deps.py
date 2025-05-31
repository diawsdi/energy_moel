from typing import Generator
from sqlalchemy.orm import Session

from app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user() -> str:
    """Get current user (placeholder for auth)."""
    return "system"  # Placeholder for actual auth 