"""
forecast_app.ui.components.tables

Reusable table helpers for the public forecast application.

Purpose
-------
- keep table rendering out of page files
- provide clean, consistent dataframe presentation
- support drill-down views without cluttering the main UI
"""

from __future__ import annotations

import pandas as pd
import streamlit as st


# ============================================================
# Public table renderer
# ============================================================

def render_clean_table(
    df: pd.DataFrame,
    *,
    title: str,
    subtitle: str | None = None,
    height: int = 420,
) -> None:
    """
    Render a clean public-facing table section.
    """
    st.subheader(title)

    if subtitle:
        st.caption(subtitle)

    if df.empty:
        st.info("No data is available for the selected filters.")
        return

    st.dataframe(
        df,
        use_container_width=True,
        height=height,
        hide_index=True,
    )