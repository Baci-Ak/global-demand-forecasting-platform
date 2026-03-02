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
2) Downloads Kaggle ZIP to Bronze (S3) and extracts/upload CSVs from the ZIP
3) Uploads CSV artifacts to Bronze (MinIO locally / S3 in AWS) using partitioned keys:
      source=<source_name>/ingest_date=<YYYY-MM-DD>/<filename>
4) Updates audit.ingestion_runs to SUCCEEDED/FAILED with row_count/file_count and s3_path

Inputs (from config.config.settings / .env)
-------------------------------------------
- M5_SOURCE_NAME: logical source identifier (default: "m5_sales")
- M5_COMPETITION: Kaggle competition slug (default: "m5-forecasting-accuracy")
- M5_DESTINATION: local staging dir (default: "local_data/m5") for download only to local staging area
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
import io
import zipfile

from datetime import date
from pathlib import Path

from app_config.config import settings
from database.database import AuditSessionLocal
from audit_log.ingestion_audit_logger import fail_run, start_run, succeed_run
from ingestion.kaggle_client import download_competition_zip_to_bronze
from ingestion.s3_client import get_s3_client


# def count_csv_rows(csv_path: Path) -> int:
#     """
#     Count CSV data rows (excluding header) without loading the file into memory.
#     """
#     with csv_path.open("r", encoding="utf-8", errors="ignore") as f:
#         return max(sum(1 for _ in f) - 1, 0)


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

    # staging_dir = Path(settings.M5_DESTINATION or "local_data/m5")
    # staging_dir.mkdir(parents=True, exist_ok=True)

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

        
        # Download Kaggle ZIP to Bronze (ephemeral /tmp only) then extract CSVs in-memory
        total_rows = 0
        file_count = 0
        total_bytes = 0
        prefix = f"source={source_name}/ingest_date={today.isoformat()}/"

        # Store the raw zip as an artifact in Bronze (handy for replay/debug)
        zip_key = f"{prefix}{source_name}.zip"
        zip_s3_url = download_competition_zip_to_bronze(s3_key=zip_key)
        print(f"Uploaded Kaggle zip → {zip_s3_url}")

        # Now read the zip back from Bronze and stream each CSV member into Bronze
        s3 = get_s3_client()

        buf = io.BytesIO()
        s3.download_fileobj(bronze_bucket, zip_key, buf)
        buf.seek(0)

        with zipfile.ZipFile(buf) as z:
            for member in z.infolist():
                # Only process CSVs at the root of the zip
                if member.is_dir() or not member.filename.lower().endswith(".csv"):
                    continue

                filename = Path(member.filename).name
                s3_key = f"{prefix}{filename}"

                with z.open(member) as f:
                    # Upload CSV bytes directly to Bronze
                    s3.upload_fileobj(f, bronze_bucket, s3_key)
                    head = s3.head_object(Bucket=bronze_bucket, Key=s3_key)
                    bytes_size = int(head["ContentLength"])
                    total_bytes += bytes_size
                    print(f"Uploaded {filename} ({bytes_size} bytes) → s3://{bronze_bucket}/{s3_key}")

                file_count += 1
                #print(f"Uploaded {filename} → s3://{bronze_bucket}/{s3_key}")


        # Audit SUCCEEDED
        succeed_run(
            db=db,
            run_id=run_id,
            s3_path=f"s3://{bronze_bucket}/{prefix}",
            row_count=None,
            file_count=file_count,
            total_bytes=total_bytes,
        )
        db.commit()
        print(
            f"Ingestion run {run_id} SUCCEEDED (file_count={file_count}, total_bytes={total_bytes})"
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
