"""
Module: quality.run_sell_prices_dq

Purpose
-------
Run a lake-native Data Quality (DQ) gate for the M5 `sell_prices.csv` dataset and
persist an auditable record of the outcome in Postgres.

Flow (high-level)
-----------------
1) Create audit.dq_runs row (status=STARTED)
2) Lookup latest SUCCEEDED ingest_date for the source (audit.ingestion_runs)
3) Download Bronze artifact to temp:
      source=<source_name>/ingest_date=<YYYY-MM-DD>/sell_prices.csv
4) Run checks (schema, composite key uniqueness/nulls, numeric rules)
5) Update audit.dq_runs to PASSED/FAILED with JSON details
6) Clean up temp file
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from config.config import settings
from database.database import AuditSessionLocal
from audit_log.dq_audit_logger import fail_run, pass_run, start_run
from ingestion.ingestion_queries import get_latest_successful_ingest_date
from ingestion.bronze_io import build_bronze_key, download_bronze_object_to_tempfile, get_bronze_bucket
from quality.specs.m5_sell_prices import (
    BRONZE_FILENAME,
    DATASET_NAME,
    PRIMARY_KEY_COLUMNS,
    REQUIRED_COLUMNS,
    SUITE_NAME,
)


def run_sell_prices_checks(csv_path: Path) -> dict[str, Any]:
    """
    Sell prices DQ checks.

    Checks
    ------
    - Required columns exist
    - Composite key columns have no nulls
    - Composite key (store_id, item_id, wm_yr_wk) is unique
    - wm_yr_wk has no nulls
    - sell_price is numeric, non-null, and > 0
    """
    df = pd.read_csv(csv_path)

    missing_required = sorted(list(REQUIRED_COLUMNS - set(df.columns)))

    # Composite key null checks
    pk_null_counts: dict[str, int] = {}
    for col in PRIMARY_KEY_COLUMNS:
        pk_null_counts[col] = int(df[col].isna().sum()) if col in df.columns else -1

    pk_any_nulls = None
    pk_unique = None
    if all(col in df.columns for col in PRIMARY_KEY_COLUMNS):
        pk_any_nulls = int(df[list(PRIMARY_KEY_COLUMNS)].isna().any(axis=1).sum())
        pk_unique = bool(df.duplicated(subset=list(PRIMARY_KEY_COLUMNS)).sum() == 0)

    # wm_yr_wk nulls
    wm_yr_wk_nulls = int(df["wm_yr_wk"].isna().sum()) if "wm_yr_wk" in df.columns else None

    # sell_price numeric & domain
    sell_price_nulls = int(df["sell_price"].isna().sum()) if "sell_price" in df.columns else None
    sell_price_non_numeric = None
    sell_price_non_positive = None
    if "sell_price" in df.columns:
        sell_price_num = pd.to_numeric(df["sell_price"], errors="coerce")
        sell_price_non_numeric = int(sell_price_num.isna().sum())  # includes original nulls
        sell_price_non_positive = int((sell_price_num <= 0).sum())

    checks: dict[str, Any] = {
        "file": str(csv_path),
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "required_columns": sorted(list(REQUIRED_COLUMNS)),
        "missing_required_columns": missing_required,
        "primary_key_columns": list(PRIMARY_KEY_COLUMNS),
        "pk_null_counts": pk_null_counts,
        "pk_any_nulls": pk_any_nulls,
        "pk_unique": pk_unique,
        "wm_yr_wk_nulls": wm_yr_wk_nulls,
        "sell_price_nulls": sell_price_nulls,
        "sell_price_non_numeric": sell_price_non_numeric,
        "sell_price_non_positive": sell_price_non_positive,
    }

    passed = True

    if missing_required:
        passed = False

    # Key rules
    if pk_any_nulls is None or pk_any_nulls != 0:
        passed = False
    if pk_unique is not True:
        passed = False

    # Domain rules
    if wm_yr_wk_nulls is None or wm_yr_wk_nulls != 0:
        passed = False
    if sell_price_nulls is None or sell_price_nulls != 0:
        passed = False
    if sell_price_non_positive is None or sell_price_non_positive != 0:
        passed = False
    # sell_price_non_numeric includes nulls; since we already require no nulls,
    # require non-numeric == 0 as well.
    if sell_price_non_numeric is None or sell_price_non_numeric != 0:
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
        results = run_sell_prices_checks(csv_path)
        details_json = json.dumps(results, default=str)

        if results["passed"]:
            pass_run(db, dq_run_id=dq_run_id, details_json=details_json)
            db.commit()
            print("DQ PASSED:", results)
            return

        failure_summary = (
            "Sell prices checks failed"
            f"; missing_required_columns={results.get('missing_required_columns')}"
            f"; pk_any_nulls={results.get('pk_any_nulls')}"
            f"; pk_unique={results.get('pk_unique')}"
            f"; wm_yr_wk_nulls={results.get('wm_yr_wk_nulls')}"
            f"; sell_price_nulls={results.get('sell_price_nulls')}"
            f"; sell_price_non_numeric={results.get('sell_price_non_numeric')}"
            f"; sell_price_non_positive={results.get('sell_price_non_positive')}"
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
