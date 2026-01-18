-- 002_create_audit_dq_runs.sql
-- Purpose:
--   Create audit.dq_runs to track data quality checks (Great Expectations later).
-- Why:
--   Production pipelines need traceability of DQ execution and outcomes.

CREATE TABLE IF NOT EXISTS audit.dq_runs (
  dq_run_id        UUID PRIMARY KEY,
  dataset_name     TEXT NOT NULL,
  suite_name       TEXT NOT NULL,
  status           TEXT NOT NULL CHECK (status IN ('STARTED','PASSED','FAILED')),
  started_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ended_at         TIMESTAMPTZ,
  details_json     TEXT,
  error_message    TEXT
);

CREATE INDEX IF NOT EXISTS idx_dq_runs_dataset_time
  ON audit.dq_runs (dataset_name, started_at DESC);
