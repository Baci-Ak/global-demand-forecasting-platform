"""
Ingestion contract for the Trends source.

Purpose
-------
Define the stable source-level contract for search-intent data ingestion.

Notes
-----
- Keep provider-specific extraction logic out of this file.
- Keep secrets/config in app_config.config, not here.
"""

from __future__ import annotations


SOURCE_NAME = "trends_google"
SCHEMA_VERSION = "v1"
RAW_FILENAME = "trends_interest_over_time.csv"