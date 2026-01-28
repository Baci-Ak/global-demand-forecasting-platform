from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

import sqlalchemy_redshift  # noqa: F401

from config.config import settings


# -------------------------------------------------------------------
# Engines
# -------------------------------------------------------------------
# Audit DB is always Postgres (local now; RDS later)
audit_engine = create_engine(settings.POSTGRES_DSN)

# Warehouse DB can be Postgres (local) or Redshift (AWS)
warehouse_dsn = settings.WAREHOUSE_DSN or settings.POSTGRES_DSN
warehouse_engine = create_engine(warehouse_dsn)

# -------------------------------------------------------------------
# Sessions
# -------------------------------------------------------------------
AuditSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=audit_engine)
WarehouseSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=warehouse_engine)

# Base class all ORM models inherits from here (audit tables)
Base = declarative_base()

audit_schema = settings.AUDIT_SCHEMA

# -------------------------------------------------------------------
# DB initialization helpers (audit DB only)
# -------------------------------------------------------------------
def init_db() -> None:
    """
    Idempotent initialization for the audit DB:
    1) Ensure audit schema exists
    2) Create audit tables + indexes declared on Base
    """
    with audit_engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {audit_schema}"))

    # Import models so they register themselves with Base.metadata
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=audit_engine)


def get_db():
    """
    FastAPI dependency / generator for the audit DB session.
    """
    db = AuditSessionLocal()
    try:
        yield db
    finally:
        db.close()
