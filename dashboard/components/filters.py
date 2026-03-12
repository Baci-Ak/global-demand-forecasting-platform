"""
Global dashboard filters component.

Purpose
-------
Renders the shared top control zone used across dashboard pages.

This version uses data-driven slicer options from the feature mart.
"""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from dashboard.core.config import CONFIG
from dashboard.core.constants import DEFAULT_TOP_N, GRANULARITY_OPTIONS, METRIC_OPTIONS
from dashboard.core.state import get_filter_state, set_filter_value
from dashboard.services.filter_options import get_filter_options


def _safe_index(options: list[str], current_value: str) -> int:
    """Return a safe selectbox index."""
    if current_value in options:
        return options.index(current_value)
    return 0


def render_filters() -> dict:
    """
    Render the shared global filter bar and return current filter state.
    """
    st.subheader("Filters")

    today = date.today()
    default_start = today - timedelta(days=CONFIG.default_date_window_days)

    if st.session_state.get("date_range") is None:
        st.session_state["date_range"] = (default_start, today)
    if st.session_state.get("state_id") is None:
        st.session_state["state_id"] = "All"
    if st.session_state.get("store_id") is None:
        st.session_state["store_id"] = "All"
    if st.session_state.get("cat_id") is None:
        st.session_state["cat_id"] = "All"
    if st.session_state.get("dept_id") is None:
        st.session_state["dept_id"] = "All"
    if st.session_state.get("item_id") is None:
        st.session_state["item_id"] = "All"
    if st.session_state.get("wm_yr_wk") is None:
        st.session_state["wm_yr_wk"] = "All"
    if st.session_state.get("top_n") is None:
        st.session_state["top_n"] = DEFAULT_TOP_N
    if st.session_state.get("metric") is None:
        st.session_state["metric"] = METRIC_OPTIONS[0]
    if st.session_state.get("granularity") is None:
        st.session_state["granularity"] = GRANULARITY_OPTIONS[0]

    filter_options = get_filter_options()

    state_options = filter_options["state_id"]
    store_options = filter_options["store_id"]
    cat_options = filter_options["cat_id"]
    dept_options = filter_options["dept_id"]
    item_options = filter_options["item_id"]
    week_options = filter_options["wm_yr_wk"]

    row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(4)
    row2_col1, row2_col2, row2_col3, row2_col4 = st.columns(4)

    with row1_col1:
        date_range = st.date_input(
            "Date Range",
            value=st.session_state["date_range"],
        )
        set_filter_value("date_range", date_range)

    with row1_col2:
        state_id = st.selectbox(
            "State",
            options=state_options,
            index=_safe_index(state_options, st.session_state["state_id"]),
        )
        set_filter_value("state_id", state_id)

    with row1_col3:
        store_id = st.selectbox(
            "Store",
            options=store_options,
            index=_safe_index(store_options, st.session_state["store_id"]),
        )
        set_filter_value("store_id", store_id)

    with row1_col4:
        cat_id = st.selectbox(
            "Category",
            options=cat_options,
            index=_safe_index(cat_options, st.session_state["cat_id"]),
        )
        set_filter_value("cat_id", cat_id)

    with row2_col1:
        dept_id = st.selectbox(
            "Department",
            options=dept_options,
            index=_safe_index(dept_options, st.session_state["dept_id"]),
        )
        set_filter_value("dept_id", dept_id)

    with row2_col2:
        item_id = st.selectbox(
            "Item",
            options=item_options,
            index=_safe_index(item_options, st.session_state["item_id"]),
        )
        set_filter_value("item_id", item_id)

    with row2_col3:
        wm_yr_wk = st.selectbox(
            "Week",
            options=week_options,
            index=_safe_index(week_options, st.session_state["wm_yr_wk"]),
        )
        set_filter_value("wm_yr_wk", wm_yr_wk)

    with row2_col4:
        top_n_options = [5, 10, 20, 50]
        top_n = st.selectbox(
            "Top N",
            options=top_n_options,
            index=top_n_options.index(st.session_state["top_n"]),
        )
        set_filter_value("top_n", top_n)

    row3_col1, row3_col2 = st.columns(2)

    with row3_col1:
        metric = st.selectbox(
            "Metric",
            options=METRIC_OPTIONS,
            index=METRIC_OPTIONS.index(st.session_state["metric"]),
        )
        set_filter_value("metric", metric)

    with row3_col2:
        granularity = st.selectbox(
            "Granularity",
            options=GRANULARITY_OPTIONS,
            index=GRANULARITY_OPTIONS.index(st.session_state["granularity"]),
        )
        set_filter_value("granularity", granularity)

    return get_filter_state()