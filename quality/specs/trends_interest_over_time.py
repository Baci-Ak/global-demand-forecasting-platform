"""
DQ specification for the Trends interest-over-time raw dataset.

Purpose
-------
Hold dataset metadata and minimum structural expectations for raw search-intent
time series ingested from Google Trends.
"""

from __future__ import annotations


DATASET_NAME = "trends_interest_over_time"
SUITE_NAME = "trends_interest_over_time_basic_v1"

BRONZE_FILENAME = "trends_interest_over_time.csv"

REQUIRED_COLUMNS = {
    "date",
    "keyword",
    "feature_name",
    "label",
    "geo",
    "source_name",
    "provider",
    "schema_version",
    "ingest_date",
}