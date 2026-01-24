"""
Ingestion audit logger.

Purpose
-------
Create and update audit rows in `audit_schema.ingestion_runs` using SQLAlchemy ORM.

Design
------
- This module does not create sessions and does not commit/rollback transactions.
- The caller owns transaction boundaries (commit/rollback) to support bundling
  multiple actions into a single unit of work.

Status lifecycle
----------------
STARTED -> SUCCEEDED | FAILED
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from database import models


def _utcnow() -> datetime:
    """UTC timestamp helper for ended_at / started_at values when needed."""
    return datetime.now(timezone.utc)


def start_run(db: Session, source_name: str, ingest_date: date, 
              schema_version: str = "v1",) -> UUID:
    """
    Create an ingestion run in STARTED state.

    Returns
    -------
    UUID
        The generated run_id.
    """
    run_id = uuid4()

    row = models.IngestionRun(
        run_id=run_id,
        source_name=source_name,
        ingest_date=ingest_date,
        status="STARTED",
        schema_version=schema_version,
        started_at=_utcnow(),  # keeps consistent even if DB default exists
    )

    db.add(row)
    db.flush()  # ensures the row is sent to DB within the current transaction

    return run_id


def succeed_run(db: Session, run_id: UUID, s3_path: str, row_count: int | None = None,
                file_count: int | None = None,) -> None:
    """
    Mark an ingestion run as SUCCEEDED.
    """
    row = db.get(models.IngestionRun, run_id)
    if row is None:
        raise ValueError(f"IngestionRun not found: {run_id}")

    row.status = "SUCCEEDED"
    row.s3_path = s3_path
    row.row_count = row_count
    row.file_count = file_count
    row.error_message = None
    row.ended_at = _utcnow()

    db.flush()


def fail_run(db: Session, run_id: UUID, error_message: str) -> None:
    """
    Mark an ingestion run as FAILED.
    """
    row = db.get(models.IngestionRun, run_id)
    if row is None:
        raise ValueError(f"IngestionRun not found: {run_id}")

    msg = (error_message or "")[:5000]

    row.status = "FAILED"
    row.error_message = msg
    row.ended_at = _utcnow()

    db.flush()
