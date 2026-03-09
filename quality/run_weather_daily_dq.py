"""
Module: quality.run_weather_daily_dq

Purpose
-------
Run a lake-native Data Quality (DQ) gate for the Weather raw daily dataset and
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
from ingestion.weather.bronze_keys import build_weather_bronze_key
from ingestion.weather.locations import WEATHER_LOCATIONS
from quality.specs.weather_daily import (
    DATASET_NAME,
    REQUIRED_DAILY_KEYS,
    REQUIRED_INGESTION_METADATA_KEYS,
    REQUIRED_LOCATION_KEYS,
    REQUIRED_TOP_LEVEL_KEYS,
    SUITE_NAME,
)


def run_weather_daily_checks(json_path: Path) -> dict[str, Any]:
    with json_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    missing_top_level_keys = sorted(list(REQUIRED_TOP_LEVEL_KEYS - set(payload.keys())))

    daily = payload.get("daily", {})
    location = payload.get("location", {})
    ingestion_metadata = payload.get("ingestion_metadata", {})

    missing_daily_keys = (
        sorted(list(REQUIRED_DAILY_KEYS - set(daily.keys())))
        if isinstance(daily, dict)
        else sorted(list(REQUIRED_DAILY_KEYS))
    )
    missing_location_keys = (
        sorted(list(REQUIRED_LOCATION_KEYS - set(location.keys())))
        if isinstance(location, dict)
        else sorted(list(REQUIRED_LOCATION_KEYS))
    )
    missing_ingestion_metadata_keys = (
        sorted(list(REQUIRED_INGESTION_METADATA_KEYS - set(ingestion_metadata.keys())))
        if isinstance(ingestion_metadata, dict)
        else sorted(list(REQUIRED_INGESTION_METADATA_KEYS))
    )

    time_values = daily.get("time", []) if isinstance(daily, dict) else []
    tmax_values = daily.get("temperature_2m_max", []) if isinstance(daily, dict) else []
    tmin_values = daily.get("temperature_2m_min", []) if isinstance(daily, dict) else []
    precip_values = daily.get("precipitation_sum", []) if isinstance(daily, dict) else []
    wind_values = daily.get("wind_speed_10m_max", []) if isinstance(daily, dict) else []

    series_lengths = {
        "time": len(time_values) if isinstance(time_values, list) else None,
        "temperature_2m_max": len(tmax_values) if isinstance(tmax_values, list) else None,
        "temperature_2m_min": len(tmin_values) if isinstance(tmin_values, list) else None,
        "precipitation_sum": len(precip_values) if isinstance(precip_values, list) else None,
        "wind_speed_10m_max": len(wind_values) if isinstance(wind_values, list) else None,
    }

    expected_length = series_lengths["time"]
    aligned_series_lengths = (
        expected_length is not None
        and all(v == expected_length for v in series_lengths.values())
    )

    precipitation_negative_count = (
        sum(1 for v in precip_values if v is not None and v < 0)
        if isinstance(precip_values, list)
        else None
    )
    wind_negative_count = (
        sum(1 for v in wind_values if v is not None and v < 0)
        if isinstance(wind_values, list)
        else None
    )

    checks: dict[str, Any] = {
        "file": str(json_path),
        "required_top_level_keys": sorted(list(REQUIRED_TOP_LEVEL_KEYS)),
        "missing_top_level_keys": missing_top_level_keys,
        "missing_daily_keys": missing_daily_keys,
        "missing_location_keys": missing_location_keys,
        "missing_ingestion_metadata_keys": missing_ingestion_metadata_keys,
        "series_lengths": series_lengths,
        "aligned_series_lengths": aligned_series_lengths,
        "precipitation_negative_count": precipitation_negative_count,
        "wind_negative_count": wind_negative_count,
    }

    passed = True

    if missing_top_level_keys:
        passed = False
    if missing_daily_keys:
        passed = False
    if missing_location_keys:
        passed = False
    if missing_ingestion_metadata_keys:
        passed = False
    if aligned_series_lengths is not True:
        passed = False
    if expected_length is None or expected_length == 0:
        passed = False
    if precipitation_negative_count is None or precipitation_negative_count != 0:
        passed = False
    if wind_negative_count is None or wind_negative_count != 0:
        passed = False

    checks["passed"] = bool(passed)
    return checks


def main() -> None:
    dataset_name = DATASET_NAME
    suite_name = SUITE_NAME

    source_name = settings.WEATHER_SOURCE_NAME or "weather_openmeteo"
    bronze_bucket = get_bronze_bucket()

    db = AuditSessionLocal()
    dq_run_id = None
    temp_paths: list[Path] = []

    try:
        dq_run_id = start_run(db, dataset_name=dataset_name, suite_name=suite_name)
        db.commit()

        latest_ingest_date = get_latest_successful_ingest_date(db, source_name=source_name)

        location_results: list[dict[str, Any]] = []

        for location in WEATHER_LOCATIONS:
            bronze_key = build_weather_bronze_key(
                ingest_date=latest_ingest_date.isoformat(),
                location_id=location["location_id"],
            )

            json_path = download_bronze_object_to_tempfile(bucket=bronze_bucket, key=bronze_key)
            temp_paths.append(json_path)

            result = run_weather_daily_checks(json_path)
            result["location_id"] = location["location_id"]
            result["state_id"] = location["state_id"]
            location_results.append(result)

        passed = all(result["passed"] for result in location_results)

        details = {
            "source_name": source_name,
            "ingest_date": latest_ingest_date.isoformat(),
            "locations_checked": len(location_results),
            "results": location_results,
            "passed": passed,
        }
        details_json = json.dumps(details, default=str)

        if passed:
            pass_run(db, dq_run_id=dq_run_id, details_json=details_json)
            db.commit()
            print("DQ PASSED:", details)
            return

        failure_summary = (
            "Weather daily checks failed"
            f"; failing_locations={[r['location_id'] for r in location_results if not r['passed']]}"
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