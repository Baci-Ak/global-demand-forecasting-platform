"""
Forecast Readiness page.

Purpose
-------
Shows whether the curated dataset is fit for forecasting use.

This page will later contain coverage KPIs, missingness analysis,
series counts, completeness checks, and readiness status cards.
"""

from __future__ import annotations

import streamlit as st


def render(filter_state: dict) -> None:
    """
    Render the Forecast Readiness page.
    """
    st.header("Forecast Readiness")

    with st.expander("Current filter state", expanded=False):
        st.json(filter_state)

    st.info(
        "Forecast readiness KPIs, feature coverage checks, and completeness "
        "views will appear here once data queries and reusable components "
        "are connected."
    )