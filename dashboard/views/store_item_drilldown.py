"""
Store / Item Drilldown page.

Purpose
-------
Deep operational analysis for a selected store and item combination.

This page will later contain item-store KPIs, daily trends, pricing view,
external driver mini-panels, and a detailed record table.
"""

from __future__ import annotations

import streamlit as st


def render(filter_state: dict) -> None:
    """
    Render the Store / Item Drilldown page.
    """
    st.header("Store / Item Drilldown")

    with st.expander("Current filter state", expanded=False):
        st.json(filter_state)

    st.info(
        "Store-item level KPIs, trends, and detailed records will appear "
        "here once data queries and reusable components are connected."
    )