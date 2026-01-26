"""
Module: quality.run_sales_train_validation_dq

Purpose
-------
Run a DQ gate for M5 `sales_train_validation.csv` and log the outcome in Postgres.

Core checks (fast + high-signal)
--------------------------------
- Required metadata columns exist
- Primary key `id` has no nulls and is unique
- There is at least one "d_*" sales column
- All "d_*" columns are numeric and non-negative (sampled for speed)
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from config.config import settings
from database.database import AuditSessionLocal
from audit_log.dq_audit_logger import fail_run, pass_run, start_run
from ingestion.ingestion_queries import get_latest_successful_ingest_date
from ingestion.bronze_io import build_bronze_key, download_bronze_object_to_tempfile, get_bronze_bucket
from quality.specs.m5_sales_train_validation import (
    BRONZE_FILENAME,
    DATASET_NAME,
    PRIMARY_KEY_COLUMN,
    REQUIRED_COLUMNS,
    SUITE_NAME,
)


_D_COL_PATTERN = re.compile(r"^d_\d+$")


def _d_cols(columns: list[str]) -> list[str]:
    return [c for c in columns if _D_COL_PATTERN.match(c)]


def run_sales_train_validation_checks(csv_path: Path) -> dict[str, Any]:
    df = pd.read_csv(csv_path)

    missing_required = sorted(list(REQUIRED_COLUMNS - set(df.columns)))

    pk = df[PRIMARY_KEY_COLUMN] if PRIMARY_KEY_COLUMN in df.columns else None
    pk_nulls = int(pk.isna().sum()) if pk is not None else None
    pk_unique = bool(pk.is_unique) if pk is not None else False

    dcols = _d_cols(list(df.columns))
    dcol_count = len(dcols)

    # For speed: validate numeric/non-negative on a sample of up to 10 d_* columns
    sample_dcols = dcols[:10]
    d_non_numeric = None
    d_negative = None
    if sample_dcols:
        non_numeric = 0
        negative = 0
        for c in sample_dcols:
            s = pd.to_numeric(df[c], errors="coerce")
            non_numeric += int(s.isna().sum())  # includes original nulls, but M5 should be 0/ints
            negative += int((s < 0).sum())
        d_non_numeric = non_numeric
        d_negative = negative

    checks: dict[str, Any] = {
        "file": str(csv_path),
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "required_columns": sorted(list(REQUIRED_COLUMNS)),
        "missing_required_columns": missing_required,
        "primary_key_column": PRIMARY_KEY_COLUMN,
        "pk_nulls": pk_nulls,
        "pk_unique": pk_unique,
        "d_column_count": dcol_count,
        "d_columns_sampled": sample_dcols,
        "d_non_numeric_in_sample": d_non_numeric,
        "d_negative_in_sample": d_negative,
    }

    passed = True

    if missing_required:
        passed = False
    if pk_nulls != 0 or pk_unique is not True:
        passed = False
    if dcol_count == 0:
        passed = False
    if d_non_numeric is None or d_non_numeric != 0:
        passed = False
    if d_negative is None or d_negative != 0:
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
        bronze_key = build_bronze_key(
            source_name=source_name,
            ingest_date=latest_ingest_date.isoformat(),
            filename=BRONZE_FILENAME,
        )

        csv_path = download_bronze_object_to_tempfile(bucket=bronze_bucket, key=bronze_key)
        results = run_sales_train_validation_checks(csv_path)
        details_json = json.dumps(results, default=str)

        if results["passed"]:
            pass_run(db, dq_run_id=dq_run_id, details_json=details_json)
            db.commit()
            print("DQ PASSED:", results)
            return

        failure_summary = (
            "Sales train validation checks failed"
            f"; missing_required_columns={results.get('missing_required_columns')}"
            f"; pk_nulls={results.get('pk_nulls')}"
            f"; pk_unique={results.get('pk_unique')}"
            f"; d_column_count={results.get('d_column_count')}"
            f"; d_non_numeric_in_sample={results.get('d_non_numeric_in_sample')}"
            f"; d_negative_in_sample={results.get('d_negative_in_sample')}"
        )

        fail_run(db, dq_run_id=dq_run_id, error_message=failure_summary, details_json=details_json)
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
