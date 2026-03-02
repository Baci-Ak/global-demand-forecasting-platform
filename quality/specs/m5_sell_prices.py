"""
DQ specification for the M5 sell_prices dataset.

Holds dataset metadata and expectations that may evolve over time.
"""

from __future__ import annotations

DATASET_NAME = "m5_sell_prices"
SUITE_NAME = "sell_prices_basic_v1"

BRONZE_FILENAME = "sell_prices.csv"

REQUIRED_COLUMNS = {"store_id", "item_id", "wm_yr_wk", "sell_price"}

# M5 doesn't provide a single natural PK column; the grain is (store_id, item_id, wm_yr_wk)
PRIMARY_KEY_COLUMNS = ("store_id", "item_id", "wm_yr_wk")
