from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# echo=True prints generated SQL to console - useful while learning/debugging
engine = create_engine(settings.SQLALCHEMY_DATABASE_URL, echo=False, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for typed SQLAlchemy ORM models."""

    pass


# Dependency used inside route functions to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
