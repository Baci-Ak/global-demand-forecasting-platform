"""
Executive Overview page.

Purpose
-------
High-level leadership view answering:
"What is happening with demand right now?"
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.components.empty_state import render_empty_state
from dashboard.components.kpi_strip import render_kpi_strip
from dashboard.services.feature_mart import apply_global_filters, load_feature_mart


def _safe_numeric_sum(df: pd.DataFrame, column: str) -> float:
    """Return a safe numeric sum for a column."""
    if column not in df.columns:
        return 0.0
    return float(pd.to_numeric(df[column], errors="coerce").fillna(0).sum())


def _safe_numeric_mean(df: pd.DataFrame, column: str) -> float:
    """Return a safe numeric mean for a column."""
    if column not in df.columns:
        return 0.0
    series = pd.to_numeric(df[column], errors="coerce").dropna()
    if series.empty:
        return 0.0
    return float(series.mean())


def _safe_nunique(df: pd.DataFrame, column: str) -> int:
    """Return a safe distinct count for a column."""
    if column not in df.columns:
        return 0
    return int(df[column].nunique())


def render(filter_state: dict) -> None:
    """
    Render the Executive Overview page.
    """
    st.header("Executive Overview")

    df = load_feature_mart()
    filtered_df = apply_global_filters(df, filter_state)

    if filtered_df.empty:
        render_empty_state(
            title="No executive data available",
            message="No records match the current filters for the Executive Overview page.",
        )
        return

    kpis = [
        {
            "label": "Total Sales",
            "value": f"{_safe_numeric_sum(filtered_df, 'sales'):,.0f}",
            "delta": None,
        },
        {
            "label": "Avg Daily Sales",
            "value": f"{_safe_numeric_mean(filtered_df, 'sales'):,.2f}",
            "delta": None,
        },
        {
            "label": "Distinct Items",
            "value": f"{_safe_nunique(filtered_df, 'item_id'):,}",
            "delta": None,
        },
        {
            "label": "Distinct Stores",
            "value": f"{_safe_nunique(filtered_df, 'store_id'):,}",
            "delta": None,
        },
        {
            "label": "Avg Sell Price",
            "value": f"{_safe_numeric_mean(filtered_df, 'sell_price'):,.2f}",
            "delta": None,
        },
    ]

    render_kpi_strip(kpis)

    with st.expander("Filtered dataset preview", expanded=False):
        st.dataframe(filtered_df.head(50), use_container_width=True)