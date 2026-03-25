"""
forecast_app.data_access.snapshot_reader

Snapshot reader utilities for the Layer 2 forecast application.

Purpose
-------
- read app-serving snapshot datasets from S3
- fall back to local cached snapshots if S3 is unavailable
- keep the public app resilient during upstream outages

Design principles
-----------------
- prefer latest successful S3 snapshot
- keep local cache as last-known-good fallback
- never make the UI depend on live warehouse connectivity
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import boto3
import pandas as pd

from forecast_app.snapshot_export.config import settings



def _empty_snapshot_metadata() -> dict:
    """
    Return a safe fallback metadata payload when no snapshot is available.
    """
    return {
        "snapshot_run_id": None,
        "refreshed_at": None,
        "source_generated_at": None,
        "model_name": None,
        "model_version": None,
        "feature_set_name": None,
        "forecast_row_count": 0,
        "forecast_series_count": 0,
        "forecast_horizon_days": 0,
        "monitoring_row_count": 0,
    }


def get_s3_client():
    """
    Return an S3 client for snapshot reads.
    """
    return boto3.client("s3")


def _read_parquet_from_s3(key: str) -> pd.DataFrame:
    """
    Read one parquet snapshot file from S3.
    """
    s3 = get_s3_client()
    obj = s3.get_object(
        Bucket=settings.LAYER2_SNAPSHOT_BUCKET,
        Key=key,
    )
    buffer = io.BytesIO(obj["Body"].read())
    return pd.read_parquet(buffer)


def _read_json_from_s3(key: str) -> dict:
    """
    Read one JSON snapshot metadata file from S3.
    """
    s3 = get_s3_client()
    obj = s3.get_object(
        Bucket=settings.LAYER2_SNAPSHOT_BUCKET,
        Key=key,
    )
    return json.loads(obj["Body"].read().decode("utf-8"))


def _read_local_parquet(filename: str) -> pd.DataFrame:
    """
    Read one cached parquet snapshot file from local disk.
    """
    path = Path(settings.LOCAL_SNAPSHOT_CACHE_DIR) / filename
    return pd.read_parquet(path)


def _read_local_json(filename: str) -> dict:
    """
    Read one cached JSON metadata file from local disk.
    """
    path = Path(settings.LOCAL_SNAPSHOT_CACHE_DIR) / filename
    return json.loads(path.read_text())


def read_latest_forecast_freshness() -> tuple[pd.DataFrame, str]:
    """
    Read latest forecast freshness, preferring S3 then local cache.

    Returns
    -------
    tuple[pd.DataFrame, str]
        DataFrame and source label.
    """
    s3_key = f"{settings.LAYER2_SNAPSHOT_PREFIX}/latest/latest_forecast_freshness.parquet"

    try:
        return _read_parquet_from_s3(s3_key), "s3_latest"
    except Exception:
        try:
            return _read_local_parquet("latest_forecast_freshness.parquet"), "local_cache"
        except Exception:
            return pd.DataFrame(), "unavailable"


def read_forecast_run_monitoring() -> tuple[pd.DataFrame, str]:
    """
    Read forecast run monitoring, preferring S3 then local cache.

    Returns
    -------
    tuple[pd.DataFrame, str]
        DataFrame and source label.
    """
    s3_key = f"{settings.LAYER2_SNAPSHOT_PREFIX}/latest/forecast_run_monitoring.parquet"

    try:
        return _read_parquet_from_s3(s3_key), "s3_latest"
    except Exception:
        try:
            return _read_local_parquet("forecast_run_monitoring.parquet"), "local_cache"
        except Exception:
            return pd.DataFrame(), "unavailable"


def read_forecast_rows() -> tuple[pd.DataFrame, str]:
    """
    Read forecast rows, preferring S3 then local cache.

    Returns
    -------
    tuple[pd.DataFrame, str]
        DataFrame and source label.
    """
    s3_key = f"{settings.LAYER2_SNAPSHOT_PREFIX}/latest/forecast_rows.parquet"

    try:
        return _read_parquet_from_s3(s3_key), "s3_latest"
    except Exception:
        try:
            return _read_local_parquet("forecast_rows.parquet"), "local_cache"
        except Exception:
            return pd.DataFrame(), "unavailable"


def read_snapshot_metadata() -> tuple[dict, str]:
    """
    Read snapshot metadata, preferring S3 then local cache.

    Returns
    -------
    tuple[dict, str]
        Metadata dict and source label.
    """
    s3_key = f"{settings.LAYER2_SNAPSHOT_PREFIX}/latest/snapshot_metadata.json"

    try:
        return _read_json_from_s3(s3_key), "s3_latest"
    except Exception:
        try:
            return _read_local_json("snapshot_metadata.json"), "local_cache"
        except Exception:
            return _empty_snapshot_metadata(), "unavailable"