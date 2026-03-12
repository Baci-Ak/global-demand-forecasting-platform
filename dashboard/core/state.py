"""
Dashboard state management.

Purpose
-------
Centralizes how global filter state is stored and accessed across views.
Uses Streamlit session_state so all views share the same filter values.
"""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from dashboard.core.config import CONFIG
from dashboard.core.constants import (
    DEFAULT_TOP_N,
    GLOBAL_FILTER_FIELDS,
    GRANULARITY_OPTIONS,
    METRIC_OPTIONS,
)


def initialize_state() -> None:
    """
    Ensure all global filter keys exist in session_state.
    """
    today = date.today()
    default_start = today - timedelta(days=CONFIG.default_date_window_days)

    defaults = {
        "date_range": (default_start, today),
        "state_id": "All",
        "store_id": "All",
        "cat_id": "All",
        "dept_id": "All",
        "item_id": "All",
        "wm_yr_wk": "All",
        "top_n": DEFAULT_TOP_N,
        "metric": METRIC_OPTIONS[0],
        "granularity": GRANULARITY_OPTIONS[0],
    }

    for field in GLOBAL_FILTER_FIELDS:
        if field not in st.session_state:
            st.session_state[field] = defaults[field]


def get_filter_state() -> dict:
    """
    Return current global filter values.
    """
    return {field: st.session_state.get(field) for field in GLOBAL_FILTER_FIELDS}


def set_filter_value(key: str, value) -> None:
    """
    Update a specific filter value.
    """
    if key in GLOBAL_FILTER_FIELDS:
        st.session_state[key] = value


def reset_filters() -> None:
    """
    Reset all global filters back to their default values.
    """
    for key in GLOBAL_FILTER_FIELDS:
        st.session_state.pop(key, None)

    initialize_state()