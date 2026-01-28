"""
S3/MinIO client helpers.

Purpose
-------
Provide a thin wrapper around boto3 for interacting with the project's S3-compatible
object storage (MinIO locally, AWS S3 in deployed environments).

Configuration
-------------
All configuration is sourced from `config.config.settings` to keep environment
handling consistent across the project:
- MLFLOW_S3_ENDPOINT_URL (MinIO endpoint URL locally)
- AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY
- AWS_REGION
- BRONZE_BUCKET
"""

from __future__ import annotations

from pathlib import Path

import boto3
from botocore.config import Config

from config.config import settings


def _require_s3_settings() -> None:
    """
    Validate required S3 settings are present.
    """
    # if not settings.MLFLOW_S3_ENDPOINT_URL:
    #     raise RuntimeError(
    #         "Missing MLFLOW_S3_ENDPOINT_URL. Set it to your MinIO/S3 endpoint URL."
    #     )

    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        raise RuntimeError(
            "Missing AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY for S3/MinIO access."
        )

    if not settings.BRONZE_BUCKET:
        raise RuntimeError("Missing BRONZE_BUCKET.")


def get_s3_client():
    """
    Create and return a boto3 S3 client configured for the current environment.
    """
    _require_s3_settings()
    endpoint_url = settings.MLFLOW_S3_ENDPOINT_URL or None

    return boto3.client(
        "s3",
        #endpoint_url=settings.MLFLOW_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
        endpoint_url=endpoint_url,
        config=Config(signature_version="s3v4"),
    )


def upload_file_to_bronze(local_path: Path, s3_key: str) -> str:
    """
    Upload a local file to the Bronze bucket under the provided object key.

    Parameters
    ----------
    local_path:
        Path to a local file on disk.
    s3_key:
        Object key inside the bronze bucket (e.g., "m5/raw/calendar.csv").

    Returns
    -------
    str
        An S3 URI of the uploaded object (e.g., "s3://bucket/key").
    """
    _require_s3_settings()

    local_path = Path(local_path)
    if not local_path.exists():
        raise FileNotFoundError(str(local_path))

    s3 = get_s3_client()
    s3.upload_file(str(local_path), settings.BRONZE_BUCKET, s3_key)

    return f"s3://{settings.BRONZE_BUCKET}/{s3_key}"




def upload_fileobj_to_bronze(fileobj, s3_key: str) -> str:
    """
    Upload a file-like object (stream) to the Bronze bucket under the provided object key.

    This is production-friendly for large payloads where writing to local disk is undesirable.

    Parameters
    ----------
    fileobj:
        A file-like object opened in binary mode.
    s3_key:
        Object key inside the bronze bucket.

    Returns
    -------
    str
        An S3 URI of the uploaded object (e.g., "s3://bucket/key").
    """
    _require_s3_settings()

    s3 = get_s3_client()
    s3.upload_fileobj(fileobj, settings.BRONZE_BUCKET, s3_key)

    return f"s3://{settings.BRONZE_BUCKET}/{s3_key}"

