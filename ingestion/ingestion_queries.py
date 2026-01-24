"""
Ingestion query helpers.

Purpose
-------
Provide read-only query utilities over `audit_schema.ingestion_runs`.

These helpers are used by downstream steps (e.g., DQ) to locate the most recent
successful ingestion partition without hardcoding dates.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from database import models


def get_latest_successful_ingest_date(db: Session, source_name: str) -> date:
    """
    Return the most recent ingest_date for a given source with status='SUCCEEDED'.

    Ordering uses ingest_date first, then ended_at for tie-breaking.
    """
    stmt = (
        select(models.IngestionRun.ingest_date)
        .where(
            models.IngestionRun.source_name == source_name,
            models.IngestionRun.status == "SUCCEEDED",
        )
        .order_by(models.IngestionRun.ingest_date.desc(), models.IngestionRun.ended_at.desc())
        .limit(1)
    )

    latest = db.execute(stmt).scalar_one_or_none()
    if latest is None:
        raise RuntimeError(f"No SUCCEEDED ingestion_runs found for source_name={source_name}")

    return latest
