"""
Module: quality.run_calendar_dq

Purpose
-------
Run a lake-native Data Quality (DQ) gate for the M5 `calendar.csv` dataset and
persist an auditable record of the outcome in Postgres.

Why this exists
---------------
Production-grade pipelines need automated “quality gates” so that:
- broken / incomplete data does not flow into downstream modeling
- failures are visible and traceable (who/what/when/why)
- downstream steps can depend on a PASS signal (or block on FAIL)

What this module does (high-level)
----------------------------------
1) Creates an audit.dq_runs row (status=STARTED) in Postgres
2) Queries Postgres for the latest SUCCEEDED ingest_date for the source
   (from audit.ingestion_runs) 
3) Downloads the target artifact from Bronze (MinIO locally / S3 in AWS) into a temp file:
      source=<source_name>/ingest_date=<YYYY-MM-DD>/calendar.csv
4) Runs dataset checks (schema, keys, date parsing, basic domain rules)
5) Updates audit.dq_runs to PASSED/FAILED with JSON details and failure summary
6) Cleans up local temp file

Inputs (from config.config.settings / .env)
-------------------------------------------
- BRONZE_BUCKET: Bronze bucket name
- M5_SOURCE_NAME: ingestion source to validate (default: "m5_sales")
- MLFLOW_S3_ENDPOINT_URL / AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_REGION:
  for MinIO/S3 connectivity (via ingestion.s3_client.get_s3_client)
- POSTGRES_DSN / AUDIT_SCHEMA: for audit logging (via SQLAlchemy)

Outputs
-------
- One audit row written/updated in audit.dq_runs
- Exit code:
    - 0 on PASS
    - non-zero (SystemExit) on FAIL to support CI/CD and Airflow task failure semantics

Ownership / future evolution
----------------------------
- Expectations for calendar.csv live in quality/specs/m5_calendar.py
- As we add more datasets, we add new specs + run_*_dq modules following this same pattern.
- In orchestration, this becomes a required gate before Silver/Gold transforms.
"""


from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from app_config.config import settings
from database.database import AuditSessionLocal
from audit_log.dq_audit_logger import fail_run, pass_run, start_run
from ingestion.ingestion_queries import get_latest_successful_ingest_date
from quality.specs.m5_calendar import (
    BRONZE_FILENAME,
    DATASET_NAME,
    DATE_COLUMN,
    PRIMARY_KEY_COLUMN,
    REQUIRED_COLUMNS,
    SUITE_NAME,
)
from ingestion.bronze_io import (download_bronze_object_to_tempfile, 
                                 get_bronze_bucket, 
                                 build_bronze_key,
                                 )




def _safe_col(df: pd.DataFrame, col: str) -> pd.Series | None:
    """Return df[col] if present, otherwise None."""
    return df[col] if col in df.columns else None


def run_calendar_checks(csv_path: Path) -> dict[str, Any]:
    """
    Calendar DQ checks.

    Checks
    ------
    - Required columns exist
    - Primary key column has no nulls and is unique
    - Date column has no nulls and is parseable
    - Date column is monotonic non-decreasing after parsing
    - Optional domain checks when columns exist:
      - weekday values are valid names
      - wm_yr_wk has no nulls
    """
    df = pd.read_csv(csv_path)

    missing_required = sorted(list(REQUIRED_COLUMNS - set(df.columns)))

    pk = _safe_col(df, PRIMARY_KEY_COLUMN)
    dt = _safe_col(df, DATE_COLUMN)

    pk_nulls = int(pk.isna().sum()) if pk is not None else None
    pk_unique = bool(pk.is_unique) if pk is not None else False

    dt_nulls = int(dt.isna().sum()) if dt is not None else None

    parsed_dates = None
    date_parse_failures = None
    date_monotonic_non_decreasing = None
    if dt is not None:
        parsed_dates = pd.to_datetime(dt, errors="coerce")
        date_parse_failures = int(parsed_dates.isna().sum())
        try:
            # monotonic check only makes sense if parsing succeeded for all rows
            if date_parse_failures == 0:
                date_monotonic_non_decreasing = bool(parsed_dates.is_monotonic_increasing)
            else:
                date_monotonic_non_decreasing = None
        except Exception:
            date_monotonic_non_decreasing = None

    # Optional domain checks (only if columns exist)
    weekday_col = _safe_col(df, "weekday")
    weekday_invalid_count = None
    if weekday_col is not None:
        allowed = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
        weekday_invalid_count = int((~weekday_col.isin(allowed)).sum())

    wm_yr_wk_col = _safe_col(df, "wm_yr_wk")
    wm_yr_wk_nulls = int(wm_yr_wk_col.isna().sum()) if wm_yr_wk_col is not None else None

    checks: dict[str, Any] = {
        "file": str(csv_path),
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "required_columns": sorted(list(REQUIRED_COLUMNS)),
        "missing_required_columns": missing_required,
        "primary_key_column": PRIMARY_KEY_COLUMN,
        "pk_nulls": pk_nulls,
        "pk_unique": pk_unique,
        "date_column": DATE_COLUMN,
        "date_nulls": dt_nulls,
        "date_parse_failures": date_parse_failures,
        "date_monotonic_non_decreasing": date_monotonic_non_decreasing,
        "weekday_invalid_count": weekday_invalid_count,
        "wm_yr_wk_nulls": wm_yr_wk_nulls,
    }

    # Pass criteria: core checks must pass. Optional checks only apply if the column exists.
    passed = True

    # Required columns must exist
    if missing_required:
        passed = False

    # PK rules
    if pk_nulls != 0 or pk_unique is not True:
        passed = False

    # Date rules
    if dt_nulls != 0 or (date_parse_failures is None) or (date_parse_failures != 0):
        passed = False

    # Monotonic date rule (only enforce when we can compute it)
    if date_monotonic_non_decreasing is False:
        passed = False

    # Optional rules
    if weekday_invalid_count is not None and weekday_invalid_count != 0:
        passed = False

    if wm_yr_wk_nulls is not None and wm_yr_wk_nulls != 0:
        passed = False

    checks["passed"] = bool(passed)
    return checks


def main() -> None:
    dataset_name = DATASET_NAME
    suite_name = SUITE_NAME

    source_name = settings.M5_SOURCE_NAME or "m5_sales"
    bronze_bucket = get_bronze_bucket()

    db = AuditSessionLocal()
    dq_run_id = None
    csv_path: Path | None = None

    try:
        dq_run_id = start_run(db, dataset_name=dataset_name, suite_name=suite_name)
        db.commit()

        latest_ingest_date = get_latest_successful_ingest_date(db, source_name=source_name)
        bronze_key = build_bronze_key(source_name=source_name, ingest_date=latest_ingest_date.isoformat(),filename=BRONZE_FILENAME,)
        #bronze_key = (f"source={source_name}/ingest_date={latest_ingest_date.isoformat()}/{BRONZE_FILENAME}")

        csv_path = download_bronze_object_to_tempfile(bucket=bronze_bucket, key=bronze_key)
        results = run_calendar_checks(csv_path)
        details_json = json.dumps(results, default=str)

        if results["passed"]:
            pass_run(db, dq_run_id=dq_run_id, details_json=details_json)
            db.commit()
            print("DQ PASSED:", results)
            return

        failure_summary = (
            "Calendar checks failed"
            f"; missing_required_columns={results.get('missing_required_columns')}"
            f"; pk_nulls={results.get('pk_nulls')}"
            f"; pk_unique={results.get('pk_unique')}"
            f"; date_nulls={results.get('date_nulls')}"
            f"; date_parse_failures={results.get('date_parse_failures')}"
            f"; date_monotonic_non_decreasing={results.get('date_monotonic_non_decreasing')}"
            f"; weekday_invalid_count={results.get('weekday_invalid_count')}"
            f"; wm_yr_wk_nulls={results.get('wm_yr_wk_nulls')}"
        )

        fail_run(
            db,
            dq_run_id=dq_run_id,
            error_message=failure_summary,
            details_json=details_json,
        )
        db.commit()
        raise SystemExit(f"DQ FAILED: {results}")


    except Exception as e:
        db.rollback()
        if dq_run_id is not None:
            try:
                fail_run(db, dq_run_id=dq_run_id, error_message=str(e))
                db.commit()
            except Exception:
                db.rollback()
        raise

    finally:
        db.close()
        if csv_path is not None:
            try:
                csv_path.unlink(missing_ok=True)
            except Exception:
                pass


if __name__ == "__main__":
    main()
