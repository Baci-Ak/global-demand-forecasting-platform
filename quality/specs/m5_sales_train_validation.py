"""
DQ specification for the M5 sales_train_validation dataset.

This is the core fact table (daily unit sales by item/store).
"""

from __future__ import annotations

DATASET_NAME = "m5_sales_train_validation"
SUITE_NAME = "sales_train_validation_basic_v1"

BRONZE_FILENAME = "sales_train_validation.csv"

# Minimum columns we require to treat the dataset as usable.
REQUIRED_COLUMNS = {"id", "item_id", "dept_id", "cat_id", "store_id", "state_id"}

# Primary key in the raw file is the row-level series id (e.g. FOODS_1_001_CA_1_validation)
PRIMARY_KEY_COLUMN = "id"
