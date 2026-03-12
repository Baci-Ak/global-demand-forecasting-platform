"""
External Drivers page.

Purpose
-------
Shows how weather, macro signals, and search trends move alongside sales.

This page will later contain driver-family sections, comparative overlays,
correlation views, and combined driver analysis.
"""

from __future__ import annotations

import streamlit as st


def render(filter_state: dict) -> None:
    """
    Render the External Drivers page.
    """
    st.header("External Drivers")

    with st.expander("Current filter state", expanded=False):
        st.json(filter_state)

    st.info(
        "Weather, macro, and search-trend analysis will appear here once "
        "data queries and reusable visual components are connected."
    )