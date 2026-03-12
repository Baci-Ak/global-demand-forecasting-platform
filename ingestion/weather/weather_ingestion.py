"""
Module: ingestion.weather.weather_ingestion

Purpose
-------
Ingest raw Weather payloads into the Bronze layer and record an operational
audit trail in Postgres.

This follows the same production pattern used by M5:
1) create audit.ingestion_runs row
2) extract raw payloads from the upstream provider
3) write raw artifacts to Bronze under partitioned keys
4) mark audit row SUCCEEDED or FAILED
"""

from __future__ import annotations

import json
from datetime import date

from app_config.config import settings
from audit_log.ingestion_audit_logger import fail_run, start_run, succeed_run
from database.database import AuditSessionLocal, warehouse_engine
from ingestion.s3_client import upload_fileobj_to_bronze
from ingestion.weather.bronze_keys import build_weather_bronze_key
from ingestion.weather.extract_openmeteo import fetch_daily_weather
from ingestion.weather.locations import WEATHER_LOCATIONS
from ingestion.weather.provider_contract import SCHEMA_VERSION, SOURCE_NAME
from sqlalchemy import text


def _get_m5_sales_date_range() -> tuple[date, date]:
    """
    Read the M5 sales date range from staged M5 data, not Silver.

    Why:
    - External-source Bronze ingestion must be bootstrap-safe.
    - Silver may not exist yet on a clean rebuild.
    - M5 staging is guaranteed to exist before external ingestion runs.
    """
    sql = text(
        """
        select
            min(cast(c.date as date)) as min_date,
            max(cast(c.date as date)) as max_date
        from staging.m5_sales_train_validation_long_raw s
        join staging.m5_calendar_raw c
          on s.d = c.d
        """
    )

    with warehouse_engine.begin() as conn:
        row = conn.execute(sql).mappings().one()

    min_date = row["min_date"]
    max_date = row["max_date"]

    if min_date is None or max_date is None:
        raise RuntimeError(
            "Could not determine M5 sales date range from staging M5 tables."
        )

    return min_date, max_date


def ingest_weather_to_bronze() -> None:
    """
    Run one Weather ingestion cycle and land raw JSON payloads in Bronze.
    """
    today = date.today()
    source_name = settings.WEATHER_SOURCE_NAME or SOURCE_NAME
    bronze_bucket = settings.BRONZE_BUCKET or ""
    if not bronze_bucket:
        raise RuntimeError("BRONZE_BUCKET is not set.")

    db = AuditSessionLocal()
    run_id = None

    try:
        weather_start_date, weather_end_date = _get_m5_sales_date_range()

        run_id = start_run(
            db=db,
            source_name=source_name,
            ingest_date=today,
            schema_version=SCHEMA_VERSION,
        )
        db.commit()

        file_count = 0
        total_bytes = 0

        for location in WEATHER_LOCATIONS:
            payload = fetch_daily_weather(
                latitude=location["latitude"],
                longitude=location["longitude"],
                timezone=location["timezone"],
                start_date=weather_start_date,
                end_date=weather_end_date,
            )

            payload["location"] = {
                "location_id": location["location_id"],
                "state_id": location["state_id"],
                "label": location["label"],
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "timezone": location["timezone"],
            }

            payload["ingestion_metadata"] = {
                "source_name": source_name,
                "provider": settings.WEATHER_PROVIDER or "openmeteo",
                "schema_version": SCHEMA_VERSION,
                "ingest_date": today.isoformat(),
                "weather_start_date": weather_start_date.isoformat(),
                "weather_end_date": weather_end_date.isoformat(),
            }

            body = json.dumps(payload).encode("utf-8")
            s3_key = build_weather_bronze_key(
                ingest_date=today.isoformat(),
                location_id=location["location_id"],
            )

            from io import BytesIO

            upload_fileobj_to_bronze(BytesIO(body), s3_key)

            file_count += 1
            total_bytes += len(body)

            print(
                f"Uploaded weather payload for {location['location_id']} "
                f"covering {weather_start_date} -> {weather_end_date} "
                f"to s3://{bronze_bucket}/{s3_key}"
            )

        succeed_run(
            db=db,
            run_id=run_id,
            s3_path=f"s3://{bronze_bucket}/source={source_name}/ingest_date={today.isoformat()}/",
            row_count=None,
            file_count=file_count,
            total_bytes=total_bytes,
        )
        db.commit()

        print(
            f"Weather ingestion run {run_id} SUCCEEDED "
            f"(file_count={file_count}, total_bytes={total_bytes})"
        )

    except Exception as e:
        db.rollback()
        if run_id is not None:
            try:
                fail_run(db=db, run_id=run_id, error_message=str(e))
                db.commit()
            except Exception:
                db.rollback()
        raise

    finally:
        db.close()