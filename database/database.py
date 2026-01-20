from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from config.config import settings 


# -------------------------------------------------------------------
# SQLAlchemy engine + session
# -------------------------------------------------------------------
engine = create_engine(settings.POSTGRES_DSN)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class all ORM models inherits from here
Base = declarative_base()

# Ensure schema exists (Postgres requires schema before CREATE TABLE schema.table)
audit_schema = settings.AUDIT_SCHEMA


# -------------------------------------------------------------------
# DB initialization helpers
# -------------------------------------------------------------------
def init_db() -> None:
    """
    Idempotent initialization:
    1) Ensure required schema exists (e.g., audit/audit_testing)
    2) Create tables + indexes declared on Base (models must be imported first)
    """
    
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {audit_schema}"))

    # Import models so they register themselves with Base.metadata
    from . import models 

    # Create tables + indexes
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Dependency / generator that yields a DB session and always closes it.
    Works with FastAPI but can also be used manually in scripts.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
