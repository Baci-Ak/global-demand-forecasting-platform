"""
Bronze key helpers for the Macro source.

Purpose
-------
Keep Macro-specific Bronze object naming isolated from extraction logic while
still following the shared lake partition convention used across the platform.
"""

from __future__ import annotations

from ingestion.bronze_io import build_bronze_key
from ingestion.macro.provider_contract import RAW_FILENAME, SOURCE_NAME


def build_macro_bronze_key(*, ingest_date: str, series_id: str) -> str:
    """
    Build the Bronze object key for one macro series raw payload.

    Layout
    ------
    source=<source_name>/ingest_date=<YYYY-MM-DD>/<series_id>/<filename>

    Example
    -------
    source=macro_fred/ingest_date=2026-03-07/CPIAUCSL/macro_series.json
    """
    return build_bronze_key(
        source_name=SOURCE_NAME,
        ingest_date=ingest_date,
        filename=f"{series_id}/{RAW_FILENAME}",
    )