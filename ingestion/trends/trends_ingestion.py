"""
Module: ingestion.trends.trends_ingestion

Purpose
-------
Ingest Google Trends interest-over-time data into the Bronze layer.

Pattern
-------
1) create audit.ingestion_runs row
2) extract raw payloads from provider
3) write raw artifacts to Bronze
4) mark audit row SUCCEEDED or FAILED
"""

from __future__ import annotations

from datetime import date
from io import BytesIO, StringIO

from sqlalchemy import text

from app_config.config import settings
from audit_log.ingestion_audit_logger import fail_run, start_run, succeed_run
from database.database import AuditSessionLocal, warehouse_engine
from ingestion.s3_client import upload_fileobj_to_bronze
from ingestion.trends.bronze_keys import build_trends_bronze_key
from ingestion.trends.extract_google_trends import fetch_interest_over_time
from ingestion.trends.keywords_registry import TRENDS_KEYWORDS
from ingestion.trends.provider_contract import SCHEMA_VERSION, SOURCE_NAME


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
def ingest_trends_to_bronze() -> None:
    """
    Run one Trends ingestion cycle and land raw CSV payloads in Bronze.
    """
    today = date.today()
    source_name = settings.TRENDS_SOURCE_NAME or SOURCE_NAME
    bronze_bucket = settings.BRONZE_BUCKET or ""

    if not bronze_bucket:
        raise RuntimeError("BRONZE_BUCKET is not configured.")

    db = AuditSessionLocal()
    run_id = None

    try:
        start_date, end_date = _get_m5_sales_date_range()

        run_id = start_run(
            db=db,
            source_name=source_name,
            ingest_date=today,
            schema_version=SCHEMA_VERSION,
        )
        db.commit()

        file_count = 0
        total_bytes = 0

        for entry in TRENDS_KEYWORDS:
            df = fetch_interest_over_time(
                keyword=entry["keyword"],
                start_date=start_date,
                end_date=end_date,
                geo=entry["geo"],
            )

            df["keyword"] = entry["keyword"]
            df["feature_name"] = entry["feature_name"]
            df["label"] = entry["label"]
            df["geo"] = entry["geo"]
            df["source_name"] = source_name
            df["provider"] = settings.TRENDS_PROVIDER or "google_trends"
            df["schema_version"] = SCHEMA_VERSION
            df["ingest_date"] = today.isoformat()

            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False)

            body = csv_buffer.getvalue().encode("utf-8")
            binary_buffer = BytesIO(body)

            s3_key = build_trends_bronze_key(
                ingest_date=today.isoformat(),
                keyword=entry["keyword"],
            )

            upload_fileobj_to_bronze(binary_buffer, s3_key)

            file_count += 1
            total_bytes += len(body)

            print(
                f"Uploaded Trends keyword {entry['keyword']} "
                f"covering {start_date} -> {end_date} "
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
            f"Trends ingestion run {run_id} SUCCEEDED "
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