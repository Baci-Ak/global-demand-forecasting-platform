"""
DQ specification for the M5 calendar dataset.

This module holds dataset metadata and expectations that may evolve over time.

"""

from __future__ import annotations

DATASET_NAME = "m5_calendar"
SUITE_NAME = "calendar_basic_v1"

BRONZE_FILENAME = "calendar.csv"

REQUIRED_COLUMNS = {"d", "date", "wm_yr_wk", "weekday"}
PRIMARY_KEY_COLUMN = "d"
DATE_COLUMN = "date"
