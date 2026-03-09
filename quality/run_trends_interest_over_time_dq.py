"""
Module: quality.run_trends_interest_over_time_dq

Purpose
-------
Run a lake-native Data Quality (DQ) gate for the Trends raw interest-over-time
dataset and persist an auditable record of the outcome in Postgres.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from app_config.config import settings
from audit_log.dq_audit_logger import fail_run, pass_run, start_run
from database.database import AuditSessionLocal
from ingestion.bronze_io import download_bronze_object_to_tempfile, get_bronze_bucket
from ingestion.ingestion_queries import get_latest_successful_ingest_date
from ingestion.trends.bronze_keys import build_trends_bronze_key
from ingestion.trends.keywords_registry import TRENDS_KEYWORDS
from quality.specs.trends_interest_over_time import (
    DATASET_NAME,
    REQUIRED_COLUMNS,
    SUITE_NAME,
)


def run_trends_interest_over_time_checks(csv_path: Path) -> dict[str, Any]:
    """
    Run structural checks for one raw Trends CSV payload.
    """
    df = pd.read_csv(csv_path)

    missing_required_columns = sorted(list(REQUIRED_COLUMNS - set(df.columns)))

    row_count = int(df.shape[0])
    date_nulls = int(df["date"].isna().sum()) if "date" in df.columns else None

    interest_column_name = None
    interest_nulls = None
    interest_negative_count = None

    candidate_interest_columns = [
        c for c in df.columns
        if c not in REQUIRED_COLUMNS and c.lower() != "ispartial"
    ]

    if len(candidate_interest_columns) == 1:
        interest_column_name = candidate_interest_columns[0]
        interest_series = pd.to_numeric(df[interest_column_name], errors="coerce")
        interest_nulls = int(interest_series.isna().sum())
        interest_negative_count = int((interest_series < 0).sum())

    keyword_nulls = int(df["keyword"].isna().sum()) if "keyword" in df.columns else None
    feature_name_nulls = int(df["feature_name"].isna().sum()) if "feature_name" in df.columns else None

    checks: dict[str, Any] = {
        "file": str(csv_path),
        "rows": row_count,
        "missing_required_columns": missing_required_columns,
        "date_nulls": date_nulls,
        "keyword_nulls": keyword_nulls,
        "feature_name_nulls": feature_name_nulls,
        "interest_column_name": interest_column_name,
        "interest_nulls": interest_nulls,
        "interest_negative_count": interest_negative_count,
    }

    passed = True

    if missing_required_columns:
        passed = False
    if row_count == 0:
        passed = False
    if date_nulls is None or date_nulls != 0:
        passed = False
    if keyword_nulls is None or keyword_nulls != 0:
        passed = False
    if feature_name_nulls is None or feature_name_nulls != 0:
        passed = False
    if interest_column_name is None:
        passed = False
    if interest_nulls is None or interest_nulls != 0:
        passed = False
    if interest_negative_count is None or interest_negative_count != 0:
        passed = False

    checks["passed"] = bool(passed)
    return checks


def main() -> None:
    """
    Run DQ across all ingested Trends keyword payloads for the latest successful
    ingest date.
    """
    dataset_name = DATASET_NAME
    suite_name = SUITE_NAME

    source_name = settings.TRENDS_SOURCE_NAME or "trends_google"
    bronze_bucket = get_bronze_bucket()

    db = AuditSessionLocal()
    dq_run_id = None
    temp_paths: list[Path] = []

    try:
        dq_run_id = start_run(db, dataset_name=dataset_name, suite_name=suite_name)
        db.commit()

        latest_ingest_date = get_latest_successful_ingest_date(db, source_name=source_name)

        keyword_results: list[dict[str, Any]] = []

        for entry in TRENDS_KEYWORDS:
            bronze_key = build_trends_bronze_key(
                ingest_date=latest_ingest_date.isoformat(),
                keyword=entry["keyword"],
            )

            csv_path = download_bronze_object_to_tempfile(
                bucket=bronze_bucket,
                key=bronze_key,
            )
            temp_paths.append(csv_path)

            result = run_trends_interest_over_time_checks(csv_path)
            result["keyword"] = entry["keyword"]
            result["feature_name"] = entry["feature_name"]
            keyword_results.append(result)

        passed = all(result["passed"] for result in keyword_results)

        details = {
            "source_name": source_name,
            "ingest_date": latest_ingest_date.isoformat(),
            "keywords_checked": len(keyword_results),
            "results": keyword_results,
            "passed": passed,
        }
        details_json = json.dumps(details, default=str)

        if passed:
            pass_run(db, dq_run_id=dq_run_id, details_json=details_json)
            db.commit()
            print("DQ PASSED:", details)
            return

        failure_summary = (
            "Trends interest-over-time checks failed"
            f"; failing_keywords={[r['keyword'] for r in keyword_results if not r['passed']]}"
        )

        fail_run(
            db,
            dq_run_id=dq_run_id,
            error_message=failure_summary,
            details_json=details_json,
        )
        db.commit()
        raise SystemExit(f"DQ FAILED: {details}")

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

        for temp_path in temp_paths:
            try:
                temp_path.unlink(missing_ok=True)
            except Exception:
                pass


if __name__ == "__main__":
    main()