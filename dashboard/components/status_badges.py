"""
Reusable status badge helpers.

Purpose
-------
Provides a consistent way to display simple dashboard status labels such as:
- Ready
- Partial Coverage
- Data Issue
"""

from __future__ import annotations

import streamlit as st


def render_status_badge(label: str) -> None:
    """
    Render a simple status badge-like label.
    """
    normalized = label.strip().lower()

    if normalized == "ready":
        st.success(label)
    elif normalized == "partial coverage":
        st.warning(label)
    elif normalized == "data issue":
        st.error(label)
    else:
        st.info(label)