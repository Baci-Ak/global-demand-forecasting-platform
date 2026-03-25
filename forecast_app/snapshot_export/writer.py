"""
forecast_app.snapshot_export.writer

Snapshot writer utilities for Layer 2 export.

Purpose
-------
- write app-serving snapshot datasets to local cache
- upload the same snapshot datasets to S3
- keep file-writing logic separate from warehouse query logic

Design principles
-----------------
- write versioned snapshot outputs first
- keep local cache and S3 publishing reusable
- use parquet for compact, app-friendly snapshot files
"""

from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from pathlib import Path

import boto3
import pandas as pd

from forecast_app.snapshot_export.config import settings


# ============================================================
# Path helpers
# ============================================================


def build_snapshot_run_id() -> str:
    """
    Build a UTC timestamp-based snapshot run identifier.
    """
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_history_prefix(run_id: str) -> str:
    """
    Build the versioned history prefix for one snapshot export run.
    """
    return f"{settings.LAYER2_SNAPSHOT_PREFIX}/history/{run_id}"


def build_latest_prefix() -> str:
    """
    Build the latest snapshot prefix.
    """
    return f"{settings.LAYER2_SNAPSHOT_PREFIX}/latest"


# ============================================================
# Local cache writers
# ============================================================


def ensure_local_cache_dir() -> Path:
    """
    Ensure the local snapshot cache directory exists.
    """
    cache_dir = Path(settings.LOCAL_SNAPSHOT_CACHE_DIR)
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def write_local_parquet(df: pd.DataFrame, filename: str) -> Path:
    """
    Write one dataframe to the local cache as parquet.
    """
    cache_dir = ensure_local_cache_dir()
    output_path = cache_dir / filename
    df.to_parquet(output_path, index=False)
    return output_path


def write_local_metadata(metadata: dict) -> Path:
    """
    Write snapshot metadata to the local cache as JSON.
    """
    cache_dir = ensure_local_cache_dir()
    output_path = cache_dir / "snapshot_metadata.json"
    output_path.write_text(json.dumps(metadata, indent=2, default=str))
    return output_path


# ============================================================
# S3 writers
# ============================================================


def get_s3_client():
    """
    Return an S3 client for snapshot publishing.
    """
    return boto3.client("s3")


def upload_dataframe_parquet_to_s3(
    df: pd.DataFrame,
    *,
    bucket: str,
    key: str,
) -> None:
    """
    Upload one dataframe to S3 as parquet.
    """
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False)
    buffer.seek(0)

    s3 = get_s3_client()
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=buffer.getvalue(),
    )


def upload_metadata_json_to_s3(
    metadata: dict,
    *,
    bucket: str,
    key: str,
) -> None:
    """
    Upload snapshot metadata to S3 as JSON.
    """
    s3 = get_s3_client()
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(metadata, indent=2, default=str).encode("utf-8"),
        ContentType="application/json",
    )