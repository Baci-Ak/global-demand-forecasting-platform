"""
S3 key helpers for Trends Bronze artifacts.

Purpose
-------
Centralize how raw Trends payloads are written into the Bronze layer so the
path layout stays consistent with the rest of the platform.

Pattern
-------
s3://<bronze-bucket>/
    source=trends_google/
        ingest_date=YYYY-MM-DD/
            keyword=<keyword>/
                trends_interest_over_time.csv
"""

from __future__ import annotations

from ingestion.trends.provider_contract import RAW_FILENAME, SOURCE_NAME


def build_trends_bronze_key(*, ingest_date: str, keyword: str) -> str:
    """
    Build the S3 key for a Trends raw artifact.

    Parameters
    ----------
    ingest_date:
        ISO date (YYYY-MM-DD) representing the ingestion partition.

    keyword:
        Keyword used for the Trends query.

    Returns
    -------
    S3 key string.
    """
    return (
        f"source={SOURCE_NAME}/"
        f"ingest_date={ingest_date}/"
        f"keyword={keyword}/"
        f"{RAW_FILENAME}"
    )