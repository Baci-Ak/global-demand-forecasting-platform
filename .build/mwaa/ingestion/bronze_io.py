"""
Module: ingestion.bronze_io

Purpose
-------
Shared helpers for reading objects from the Bronze layer (S3/MinIO).

Why this exists
---------------
Multiple parts of the platform need to read from Bronze:
- Data Quality (DQ) gates
- Warehouse loaders (Bronze -> staging tables)
- Feature engineering jobs (later)

To avoid duplicated code and inconsistent behavior, we centralize:
- building the Bronze object key pattern
- downloading Bronze objects to a local temporary file for processing

Design notes
------------
- Bronze is treated as the system-of-record for raw data (lake-native).
- We download to a temp file because many libraries (pandas, pyarrow, etc.)
  work cleanly with file paths, and this pattern translates well to AWS.

Configuration
-------------
Reads from config.config.settings:
- BRONZE_BUCKET
- MLFLOW_S3_ENDPOINT_URL / AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_REGION
- source naming is supplied by the caller (e.g., "m5_sales")

Key conventions
---------------
We follow a consistent Bronze partition layout:

  source=<source_name>/ingest_date=<YYYY-MM-DD>/<filename>

Example:
  source=m5_sales/ingest_date=2026-01-18/calendar.csv
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from app_config.config import settings
from ingestion.s3_client import get_s3_client


def build_bronze_key(*, source_name: str, ingest_date: str, filename: str) -> str:
    """
    Build a Bronze object key using our lake partition convention.

    Args:
        source_name: logical ingestion source name (e.g., "m5_sales")
        ingest_date: YYYY-MM-DD (string for portability)
        filename: leaf filename (e.g., "calendar.csv")

    Returns:
        Bronze key string.
    """
    return f"source={source_name}/ingest_date={ingest_date}/{filename}"


def download_bronze_object_to_tempfile(*, bucket: str, key: str) -> Path:
    """
    Download s3://bucket/key to a local temporary file and return the local path.

    Notes:
    - Caller is responsible for deleting the temp file (best-effort cleanup).
    """
    s3 = get_s3_client()

    suffix = Path(key).suffix or ".bin"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp_path = Path(tmp.name)
    tmp.close()

    s3.download_file(bucket, key, str(tmp_path))
    return tmp_path


def get_bronze_bucket() -> str:
    """
    Convenience accessor for Bronze bucket name.

    Returns:
        Bronze bucket name from settings.

    Raises:
        RuntimeError if not configured.
    """
    bucket = settings.BRONZE_BUCKET
    if not bucket:
        raise RuntimeError("BRONZE_BUCKET is not set in .env")
    return bucket
