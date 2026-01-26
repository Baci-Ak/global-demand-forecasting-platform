"""
Module: ingestion.m5_ingestion

Purpose
-------
Ingest the M5 competition dataset into the project lake (Bronze layer) and record
an operational audit trail in Postgres.

Why this exists
---------------
In production data platforms, ingestion must be:
- repeatable (same steps every run)
- traceable (audited: what ran, when, outcome)
- partitioned (data organized by source/date for downstream processing)

What this module does (high-level)
----------------------------------
1) Creates an audit.ingestion_runs row (status=STARTED) in Postgres
2) Downloads the Kaggle competition bundle into a local staging directory
3) Uploads CSV artifacts to Bronze (MinIO locally / S3 in AWS) using partitioned keys:
      source=<source_name>/ingest_date=<YYYY-MM-DD>/<filename>
4) Updates audit.ingestion_runs to SUCCEEDED/FAILED with row_count/file_count and s3_path

Inputs (from config.config.settings / .env)
-------------------------------------------
- M5_SOURCE_NAME: logical source identifier (default: "m5_sales")
- M5_COMPETITION: Kaggle competition slug (default: "m5-forecasting-accuracy")
- M5_DESTINATION: local staging dir (default: "local_data/m5")
- BRONZE_BUCKET: Bronze bucket name
- POSTGRES_DSN / AUDIT_SCHEMA: for audit logging (via SQLAlchemy)

Outputs
-------
- Objects written to Bronze bucket (partitioned path)
- One audit row written/updated in audit.ingestion_runs

Ownership / future evolution
----------------------------
- This module is intentionally orchestration-only.
- Transformations (Silver/Gold) belong in warehouse/ (dbt) not here.
- Scheduling will later be done by Airflow; this function becomes a task callable.
"""


from __future__ import annotations

from datetime import date
from pathlib import Path

from config.config import settings
from database.database import AuditSessionLocal
from audit_log.ingestion_audit_logger import fail_run, start_run, succeed_run
from ingestion.kaggle_client import download_dataset
from ingestion.s3_client import upload_file_to_bronze


def count_csv_rows(csv_path: Path) -> int:
    """
    Count CSV data rows (excluding header) without loading the file into memory.
    """
    with csv_path.open("r", encoding="utf-8", errors="ignore") as f:
        return max(sum(1 for _ in f) - 1, 0)


def ingest_m5_to_bronze() -> None:
    """
    Run one ingestion cycle:
      1) create audit row (STARTED)
      2) download Kaggle competition files locally
      3) upload CSVs to Bronze under partitioned keys
      4) mark audit row SUCCEEDED or FAILED
    """
    today = date.today()

    source_name = settings.M5_SOURCE_NAME or "m5_sales"
    bronze_bucket = settings.BRONZE_BUCKET or ""
    if not bronze_bucket:
        raise RuntimeError("BRONZE_BUCKET is not set.")

    staging_dir = Path(settings.M5_DESTINATION or "local_data/m5")
    staging_dir.mkdir(parents=True, exist_ok=True)

    db = AuditSessionLocal()
    run_id = None

    try:
        # 1) Audit STARTED
        run_id = start_run(
            db=db,
            source_name=source_name,
            ingest_date=today,
            schema_version="v1",
        )
        db.commit()

        # Download into local staging folder
        local_path = Path(download_dataset())

        # Upload each CSV and accumulate row counts + file count
        total_rows = 0
        file_count = 0
        prefix = f"source={source_name}/ingest_date={today.isoformat()}/"

        for file_path in local_path.glob("*.csv"):
            rows = count_csv_rows(file_path)
            total_rows += rows

            s3_key = f"{prefix}{file_path.name}"
            s3_url = upload_file_to_bronze(file_path, s3_key)

            file_count += 1
            print(f"Uploaded {file_path.name} ({rows} rows) → {s3_url}")

        # Audit SUCCEEDED
        succeed_run(
            db=db,
            run_id=run_id,
            s3_path=f"s3://{bronze_bucket}/{prefix}",
            row_count=total_rows,
            file_count=file_count,
        )
        db.commit()
        print(
            f"Ingestion run {run_id} SUCCEEDED (total_rows={total_rows}, file_count={file_count})"
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
