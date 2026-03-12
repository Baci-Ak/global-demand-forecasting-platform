"""
Sales & Demand page.

Purpose
-------
Detailed sales behavior and core demand patterns.

This page will later contain sales KPIs, trend charts, distribution views,
and ranked demand breakdowns.
"""

from __future__ import annotations

import streamlit as st


def render(filter_state: dict) -> None:
    """
    Render the Sales & Demand page.
    """
    st.header("Sales & Demand")

    with st.expander("Current filter state", expanded=False):
        st.json(filter_state)

    st.info(
        "Sales KPIs, demand trends, and demand breakdown visuals will appear "
        "here once data queries and reusable chart components are connected."
    )