"""
Reusable table component helpers.

Purpose
-------
Provides a consistent way to render tabular outputs across dashboard pages.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st


def render_table(df: pd.DataFrame, *, use_container_width: bool = True) -> None:
    """
    Render a dataframe in a consistent dashboard style.
    """
    if df.empty:
        st.info("No rows to display.")
        return

    st.dataframe(df, use_container_width=use_container_width)