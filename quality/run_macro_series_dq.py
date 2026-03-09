"""
Module: quality.run_macro_series_dq

Purpose
-------
Run a lake-native Data Quality (DQ) gate for the Macro raw series dataset and
persist an auditable record of the outcome in Postgres.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app_config.config import settings
from audit_log.dq_audit_logger import fail_run, pass_run, start_run
from database.database import AuditSessionLocal
from ingestion.bronze_io import download_bronze_object_to_tempfile, get_bronze_bucket
from ingestion.ingestion_queries import get_latest_successful_ingest_date
from ingestion.macro.bronze_keys import build_macro_bronze_key
from ingestion.macro.series_registry import MACRO_SERIES
from quality.specs.macro_series import (
    DATASET_NAME,
    REQUIRED_INGESTION_METADATA_KEYS,
    REQUIRED_OBSERVATION_KEYS,
    REQUIRED_SERIES_METADATA_KEYS,
    REQUIRED_TOP_LEVEL_KEYS,
    SUITE_NAME,
)


def run_macro_series_checks(json_path: Path) -> dict[str, Any]:
    """
    Run structural checks for one raw macro series payload.
    """
    with json_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    missing_top_level_keys = sorted(list(REQUIRED_TOP_LEVEL_KEYS - set(payload.keys())))

    series_metadata = payload.get("series_metadata", {})
    ingestion_metadata = payload.get("ingestion_metadata", {})
    observations = payload.get("observations", [])

    missing_series_metadata_keys = (
        sorted(list(REQUIRED_SERIES_METADATA_KEYS - set(series_metadata.keys())))
        if isinstance(series_metadata, dict)
        else sorted(list(REQUIRED_SERIES_METADATA_KEYS))
    )
    missing_ingestion_metadata_keys = (
        sorted(list(REQUIRED_INGESTION_METADATA_KEYS - set(ingestion_metadata.keys())))
        if isinstance(ingestion_metadata, dict)
        else sorted(list(REQUIRED_INGESTION_METADATA_KEYS))
    )

    observation_count = len(observations) if isinstance(observations, list) else None

    missing_observation_keys_count = None
    empty_date_count = None
    empty_value_count = None

    if isinstance(observations, list):
        missing_observation_keys_count = 0
        empty_date_count = 0
        empty_value_count = 0

        for obs in observations:
            if not isinstance(obs, dict):
                missing_observation_keys_count += len(REQUIRED_OBSERVATION_KEYS)
                continue

            missing_keys = REQUIRED_OBSERVATION_KEYS - set(obs.keys())
            missing_observation_keys_count += len(missing_keys)

            if not obs.get("date"):
                empty_date_count += 1

            if obs.get("value") in (None, ""):
                empty_value_count += 1

    checks: dict[str, Any] = {
        "file": str(json_path),
        "missing_top_level_keys": missing_top_level_keys,
        "missing_series_metadata_keys": missing_series_metadata_keys,
        "missing_ingestion_metadata_keys": missing_ingestion_metadata_keys,
        "observation_count": observation_count,
        "missing_observation_keys_count": missing_observation_keys_count,
        "empty_date_count": empty_date_count,
        "empty_value_count": empty_value_count,
    }

    passed = True

    if missing_top_level_keys:
        passed = False
    if missing_series_metadata_keys:
        passed = False
    if missing_ingestion_metadata_keys:
        passed = False
    if observation_count is None or observation_count == 0:
        passed = False
    if missing_observation_keys_count is None or missing_observation_keys_count != 0:
        passed = False
    if empty_date_count is None or empty_date_count != 0:
        passed = False
    if empty_value_count is None or empty_value_count != 0:
        passed = False

    checks["passed"] = bool(passed)
    return checks


def main() -> None:
    """
    Run DQ across all ingested macro series for the latest successful ingest date.
    """
    dataset_name = DATASET_NAME
    suite_name = SUITE_NAME

    source_name = settings.MACRO_SOURCE_NAME or "macro_fred"
    bronze_bucket = get_bronze_bucket()

    db = AuditSessionLocal()
    dq_run_id = None
    temp_paths: list[Path] = []

    try:
        dq_run_id = start_run(db, dataset_name=dataset_name, suite_name=suite_name)
        db.commit()

        latest_ingest_date = get_latest_successful_ingest_date(db, source_name=source_name)

        series_results: list[dict[str, Any]] = []

        for series in MACRO_SERIES:
            bronze_key = build_macro_bronze_key(
                ingest_date=latest_ingest_date.isoformat(),
                series_id=series["series_id"],
            )

            json_path = download_bronze_object_to_tempfile(
                bucket=bronze_bucket,
                key=bronze_key,
            )
            temp_paths.append(json_path)

            result = run_macro_series_checks(json_path)
            result["series_id"] = series["series_id"]
            result["feature_name"] = series["feature_name"]
            series_results.append(result)

        passed = all(result["passed"] for result in series_results)

        details = {
            "source_name": source_name,
            "ingest_date": latest_ingest_date.isoformat(),
            "series_checked": len(series_results),
            "results": series_results,
            "passed": passed,
        }
        details_json = json.dumps(details, default=str)

        if passed:
            pass_run(db, dq_run_id=dq_run_id, details_json=details_json)
            db.commit()
            print("DQ PASSED:", details)
            return

        failure_summary = (
            "Macro series checks failed"
            f"; failing_series={[r['series_id'] for r in series_results if not r['passed']]}"
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