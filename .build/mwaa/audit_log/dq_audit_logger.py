"""
DQ audit logger.

Purpose
-------
Create and update audit rows in `audit_schema.dq_runs` using SQLAlchemy ORM.

Design
------
- This module does not create sessions and does not commit/rollback transactions.
- The caller owns transaction boundaries (commit/rollback) to support bundling
  multiple actions into a single unit of work.

Status lifecycle
----------------
STARTED -> PASSED | FAILED
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from database import models


def _utcnow() -> datetime:
    """UTC timestamp helper for ended_at / started_at values when needed."""
    return datetime.now(timezone.utc)


def start_run(db: Session, dataset_name: str, suite_name: str) -> UUID:
    """
    Create a DQ run in STARTED state.

    Returns
    -------
    UUID
        The generated dq_run_id.
    """
    dq_run_id = uuid4()

    row = models.DqRun(
        dq_run_id=dq_run_id,
        dataset_name=dataset_name,
        suite_name=suite_name,
        status="STARTED",
        started_at=_utcnow(),
    )

    db.add(row)
    db.flush()

    return dq_run_id


def pass_run(db: Session, dq_run_id: UUID, details_json: str | None = None) -> None:
    """
    Mark a DQ run as PASSED.
    """
    row = db.get(models.DqRun, dq_run_id)
    if row is None:
        raise ValueError(f"DqRun not found: {dq_run_id}")

    ended_at = _utcnow()

    row.status = "PASSED"
    row.ended_at = ended_at
    row.details_json = details_json
    row.error_message = None

    if row.started_at is not None:
        row.run_duration_seconds = int((ended_at - row.started_at).total_seconds())

    db.flush()


def fail_run(
    db: Session,
    dq_run_id: UUID,
    error_message: str,
    details_json: str | None = None,
) -> None:
    """
    Mark a DQ run as FAILED.
    """
    row = db.get(models.DqRun, dq_run_id)
    if row is None:
        raise ValueError(f"DqRun not found: {dq_run_id}")

    ended_at = _utcnow()
    msg = (error_message or "")[:5000]

    row.status = "FAILED"
    row.ended_at = ended_at
    row.details_json = details_json
    row.error_message = msg

    if row.started_at is not None:
        row.run_duration_seconds = int((ended_at - row.started_at).total_seconds())

    db.flush()
