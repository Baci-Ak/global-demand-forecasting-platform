"""
Reusable empty-state component.

Purpose
-------
Provides a consistent message when a page, chart, or table has no data
for the current filter selection.
"""

from __future__ import annotations

import streamlit as st


def render_empty_state(
    title: str = "No data available",
    message: str = (
        "No records match the current filters. Adjust your selections and try again."
    ),
) -> None:
    """
    Render a standard empty-state message block.
    """
    st.warning(f"**{title}**\n\n{message}")