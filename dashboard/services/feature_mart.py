"""
Feature mart service layer.

Purpose
-------
Provides reusable access patterns for the dashboard feature mart, including
global filter application logic shared across views.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from typing import Any

import pandas as pd

from dashboard.services.data_access import get_feature_mart_df


def load_feature_mart() -> pd.DataFrame:
    """
    Load the dashboard feature mart.
    """
    return get_feature_mart_df()


def _normalize_date_range(date_range_value: Any) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    """
    Normalize Streamlit date input output into pandas timestamps.
    """
    if not date_range_value:
        return None, None

    if isinstance(date_range_value, tuple | list) and len(date_range_value) == 2:
        start_date, end_date = date_range_value
        start_ts = pd.to_datetime(start_date) if start_date else None
        end_ts = pd.to_datetime(end_date) if end_date else None
        return start_ts, end_ts

    if isinstance(date_range_value, date):
        single_ts = pd.to_datetime(date_range_value)
        return single_ts, single_ts

    return None, None


def apply_global_filters(df: pd.DataFrame, filter_state: dict[str, Any]) -> pd.DataFrame:
    """
    Apply dashboard global filters to a feature mart dataframe.
    """
    filtered = df.copy()

    if filtered.empty:
        return filtered

    if "date" in filtered.columns:
        filtered["date"] = pd.to_datetime(filtered["date"])

        start_ts, end_ts = _normalize_date_range(filter_state.get("date_range"))
        if start_ts is not None:
            filtered = filtered.loc[filtered["date"] >= start_ts]
        if end_ts is not None:
            filtered = filtered.loc[filtered["date"] <= end_ts]

    discrete_filters: Iterable[str] = (
        "state_id",
        "store_id",
        "cat_id",
        "dept_id",
        "item_id",
        "wm_yr_wk",
    )

    for column in discrete_filters:
        selected_value = filter_state.get(column)
        if column in filtered.columns and selected_value not in (None, "All"):
            filtered = filtered.loc[filtered[column].astype(str) == str(selected_value)]

    return filtered