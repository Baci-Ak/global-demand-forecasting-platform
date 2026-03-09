"""
Bronze key helpers for the Weather source.

Purpose
-------
Keep Weather-specific Bronze object naming isolated from extraction logic while
still following the shared lake partition convention used across the platform.
"""

from __future__ import annotations

from ingestion.bronze_io import build_bronze_key
from ingestion.weather.provider_contract import RAW_FILENAME, SOURCE_NAME


def build_weather_bronze_key(*, ingest_date: str, location_id: str) -> str:
    """
    Build the Bronze object key for one weather raw payload.

    Layout
    ------
    source=<source_name>/ingest_date=<YYYY-MM-DD>/<location_id>/<filename>

    Example
    -------
    source=weather_openmeteo/ingest_date=2026-03-06/CA/daily_weather.json
    """
    return build_bronze_key(
        source_name=SOURCE_NAME,
        ingest_date=ingest_date,
        filename=f"{location_id}/{RAW_FILENAME}",
    )