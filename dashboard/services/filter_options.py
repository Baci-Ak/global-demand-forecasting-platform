"""
Filter option service.

Purpose
-------
Builds reusable filter option lists from the dashboard feature mart so
UI controls stay data-driven and never hardcoded.

This module is resilient to missing datasets during early dashboard setup.
"""

from __future__ import annotations

import pandas as pd

from dashboard.services.data_access import get_feature_mart_df


def _sorted_options(df: pd.DataFrame, column: str) -> list[str]:
    """
    Return sorted distinct non-null values for a column, prefixed with 'All'.
    """
    if column not in df.columns:
        return ["All"]

    values = (
        df[column]
        .dropna()
        .astype(str)
        .sort_values()
        .unique()
        .tolist()
    )
    return ["All", *values]


def get_filter_options() -> dict[str, list[str]]:
    """
    Build all global filter option lists from the feature mart.
    Falls back to 'All' options if data is not yet available.
    """
    try:
        df = get_feature_mart_df()
    except FileNotFoundError:
        return {
            "state_id": ["All"],
            "store_id": ["All"],
            "cat_id": ["All"],
            "dept_id": ["All"],
            "item_id": ["All"],
            "wm_yr_wk": ["All"],
        }

    return {
        "state_id": _sorted_options(df, "state_id"),
        "store_id": _sorted_options(df, "store_id"),
        "cat_id": _sorted_options(df, "cat_id"),
        "dept_id": _sorted_options(df, "dept_id"),
        "item_id": _sorted_options(df, "item_id"),
        "wm_yr_wk": _sorted_options(df, "wm_yr_wk"),
    }