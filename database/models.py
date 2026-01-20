"""
SQLAlchemy ORM models for operational/audit metadata.

These models are intended to mirror the SQL Data definition language (DDL) for the postgres database:
- Schema: audit
- Tables: audit.ingestion_runs, audit.dq_runs
- Status constraints enforced via CHECK constraints
- Indexes for common query patterns
"""

from sqlalchemy import (Column, Text, Date, BigInteger, Index,Integer, CheckConstraint,)
from sqlalchemy.sql import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID

from .database import Base, audit_schema


# ------------------------------------------------------------------------------
# IngestionRun
# ------------------------------------------------------------------------------
# Tracks every ingestion job run:
# - what source was ingested
# - the ingest date 
# - status and metadata (row counts, schema version, landing path, errors)
# - timestamps for traceability (started_at/ended_at)

# ------------------------------------------------------------------------------

class IngestionRun(Base):
    # Table name 
    __tablename__ = "ingestion_runs"

    # Primary key for the ingestion run (UUID).
    run_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)

    # Identifies the upstream source/system feeding the ingestion.
    source_name = Column(Text, nullable=False)

    # date of the ingestion
    ingest_date = Column(Date, nullable=False)

    # Status is restricted to STARTED/SUCCEEDED/FAILED by a CHECK constraint below.
    status = Column(Text, nullable=False)

    # Optional metadata fields
    s3_path = Column(Text, nullable=True)           # Where the data landed
    row_count = Column(BigInteger, nullable=True)   # Record count produced/loaded
    schema_version = Column(Text, nullable=True)    # Schema/version marker for the payload

    # Operational timestamps
    started_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"),)
    ended_at = Column(TIMESTAMP(timezone=True), nullable=True,)

    # Error details (if any)
    error_message = Column(Text, nullable=True)

    # Table-level configuration:
    # - Create index for fast lookup by (source_name, ingest_date)
    # - Place the table in schema "audit"
    __table_args__ = (
        CheckConstraint("status IN ('STARTED','SUCCEEDED','FAILED')",name="chk_ingestion_runs_status",),
        Index("idx_ingestion_runs_source_date", "source_name", "ingest_date",),
        {"schema": audit_schema},)


# ------------------------------------------------------------------------------
# DqRun
# ------------------------------------------------------------------------------
# Tracks data quality (DQ) runs (e.g., Great Expectations checks):
# - dataset name and suite name identify what was checked
# - status tracks outcome: STARTED/PASSED/FAILED
# - details_json stores additional info about the run (JSON serialized as TEXT)
# - timestamps and error_message provide traceability

# ------------------------------------------------------------------------------
class DqRun(Base):
    __tablename__ = "dq_runs"
    dq_run_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)

    # Identifies what dataset was checked.
    dataset_name = Column(Text, nullable=False)

    # Identifies which suite of checks ran.
    suite_name = Column(Text, nullable=False)

    # Status restricted to STARTED/PASSED/FAILED by CHECK constraint below.
    status = Column(Text, nullable=False)

    # Run timestamps
    started_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"),)
    ended_at = Column(TIMESTAMP(timezone=True),nullable=True,)

    # NEW: duration in seconds (optional)
    run_duration_seconds = Column(Integer, nullable=True)

    # Additional run details 
    details_json = Column(Text, nullable=True)

    # Error details (if any)
    error_message = Column(Text, nullable=True)

    # Table-level configuration:
    # - Enforce allowed status values 
    # - Create index for fast lookup by dataset and most-recent runs first
    # - Place the table in schema "audit"
    __table_args__ = (
        CheckConstraint("status IN ('STARTED','PASSED','FAILED')", name="chk_dq_runs_status",),
        Index("idx_dq_runs_dataset_time", "dataset_name", started_at.desc(),),
        {"schema": audit_schema},)
