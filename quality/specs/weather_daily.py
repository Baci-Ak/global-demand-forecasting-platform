"""
DQ specification for the Weather daily raw dataset.

This module holds dataset metadata and expectations that may evolve over time.
"""

from __future__ import annotations

DATASET_NAME = "weather_daily"
SUITE_NAME = "weather_daily_basic_v1"

BRONZE_FILENAME = "daily_weather.json"

REQUIRED_TOP_LEVEL_KEYS = {
    "latitude",
    "longitude",
    "timezone",
    "daily",
    "location",
    "ingestion_metadata",
}

REQUIRED_DAILY_KEYS = {
    "time",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "wind_speed_10m_max",
}

REQUIRED_LOCATION_KEYS = {
    "location_id",
    "state_id",
    "label",
    "latitude",
    "longitude",
    "timezone",
}

REQUIRED_INGESTION_METADATA_KEYS = {
    "source_name",
    "provider",
    "schema_version",
    "ingest_date",
}