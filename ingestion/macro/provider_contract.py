"""
Ingestion contract for the Macro source.

Purpose
-------
Define the stable source-level contract for macroeconomic data ingestion.

"""

from __future__ import annotations


SOURCE_NAME = "macro_fred"
SCHEMA_VERSION = "v1"
RAW_FILENAME = "macro_series.json"