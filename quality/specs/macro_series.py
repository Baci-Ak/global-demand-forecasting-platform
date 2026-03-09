"""
DQ specification for the Macro raw series dataset.

Purpose
-------
Hold dataset metadata and minimum structural expectations for raw macroeconomic
series ingested from FRED.
"""

from __future__ import annotations


DATASET_NAME = "macro_series"
SUITE_NAME = "macro_series_basic_v1"

BRONZE_FILENAME = "macro_series.json"

REQUIRED_TOP_LEVEL_KEYS = {
    "observations",
    "series_metadata",
    "ingestion_metadata",
}

REQUIRED_SERIES_METADATA_KEYS = {
    "series_id",
    "feature_name",
    "label",
    "frequency",
    "units",
}

REQUIRED_INGESTION_METADATA_KEYS = {
    "source_name",
    "provider",
    "schema_version",
    "ingest_date",
}

REQUIRED_OBSERVATION_KEYS = {
    "date",
    "value",
}