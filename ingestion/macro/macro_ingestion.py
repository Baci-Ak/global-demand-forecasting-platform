"""
Module: ingestion.macro.macro_ingestion

Purpose
-------
Ingest macroeconomic time series from FRED into the Bronze layer.

Pattern
-------
1) create audit.ingestion_runs row
2) extract raw payloads from provider
3) write raw artifacts to Bronze
4) mark audit row SUCCEEDED or FAILED
"""

from __future__ import annotations

import json
from datetime import date
from io import BytesIO

from sqlalchemy import text

from app_config.config import settings
from audit_log.ingestion_audit_logger import fail_run, start_run, succeed_run
from database.database import AuditSessionLocal, warehouse_engine
from ingestion.macro.bronze_keys import build_macro_bronze_key
from ingestion.macro.extract_fred import fetch_fred_series
from ingestion.macro.provider_contract import SCHEMA_VERSION, SOURCE_NAME
from ingestion.macro.series_registry import MACRO_SERIES
from ingestion.s3_client import upload_fileobj_to_bronze


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
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


# ------------------------------------------------------------------------------
# Public ingestion entrypoint
# ------------------------------------------------------------------------------
def ingest_macro_to_bronze() -> None:
    """
    Run one macro ingestion cycle and land raw JSON payloads in Bronze.
    """
    today = date.today()
    source_name = settings.MACRO_SOURCE_NAME or SOURCE_NAME
    bronze_bucket = settings.BRONZE_BUCKET or ""

    if not bronze_bucket:
        raise RuntimeError("BRONZE_BUCKET is not configured.")

    db = AuditSessionLocal()
    run_id = None

    try:
        observation_start, observation_end = _get_m5_sales_date_range()

        run_id = start_run(
            db=db,
            source_name=source_name,
            ingest_date=today,
            schema_version=SCHEMA_VERSION,
        )
        db.commit()

        file_count = 0
        total_bytes = 0

        for series in MACRO_SERIES:
            payload = fetch_fred_series(
                series_id=series["series_id"],
                observation_start=observation_start,
                observation_end=observation_end,
            )

            payload["series_metadata"] = {
                "series_id": series["series_id"],
                "feature_name": series["feature_name"],
                "label": series["label"],
                "frequency": series["frequency"],
                "units": series["units"],
            }

            payload["ingestion_metadata"] = {
                "source_name": source_name,
                "provider": settings.MACRO_PROVIDER or "fred",
                "schema_version": SCHEMA_VERSION,
                "ingest_date": today.isoformat(),
                "observation_start": observation_start.isoformat(),
                "observation_end": observation_end.isoformat(),
            }

            body = json.dumps(payload).encode("utf-8")

            s3_key = build_macro_bronze_key(
                ingest_date=today.isoformat(),
                series_id=series["series_id"],
            )

            upload_fileobj_to_bronze(BytesIO(body), s3_key)

            file_count += 1
            total_bytes += len(body)

            print(
                f"Uploaded macro series {series['series_id']} "
                f"covering {observation_start} -> {observation_end} "
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
            f"Macro ingestion run {run_id} SUCCEEDED "
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