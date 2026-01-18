-- 001_create_audit_ingestion_runs.sql
-- Purpose:
--   Create the audit schema and the ingestion_runs table used to track every ingestion job.
-- Why:
--   Production pipelines need traceability (what ran, when, status, where data landed, errors).
-- Notes:
--   - MLflow uses the public schema in this database; project operational metadata lives in audit.*.
--   - This table will be written by ingestion code and orchestration (Airflow) later.


CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE IF NOT EXISTS audit.ingestion_runs (
  run_id           UUID PRIMARY KEY,
  source_name      TEXT NOT NULL,
  ingest_date      DATE NOT NULL,
  status           TEXT NOT NULL CHECK (status IN ('STARTED','SUCCEEDED','FAILED')),
  s3_path          TEXT,
  row_count        BIGINT,
  schema_version   TEXT,
  started_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ended_at         TIMESTAMPTZ,
  error_message    TEXT
);

CREATE INDEX IF NOT EXISTS idx_ingestion_runs_source_date
  ON audit.ingestion_runs (source_name, ingest_date);
