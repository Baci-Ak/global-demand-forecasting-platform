"""
forecast_app.ui.pages.forecast_explorer

Forecast Explorer page for the public forecast application.

Purpose
-------
- provide the main interactive forecast exploration view
- let users filter the published forecast window
- combine trend charts with a clean detail table

Design principles
-----------------
- interactive but simple
- chart-first layout
- detail available without overwhelming the page
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from .forecast_window import build_forecast_window_label
from forecast_app.ui.components.charts import render_forecast_trend_chart
from forecast_app.ui.components.filters import (
    apply_main_filters,
    render_main_filters,
)
from forecast_app.ui.components.tables import render_clean_table
from forecast_app.ui.styles import render_app_header


# ============================================================
# Helpers
# ============================================================

def _build_forecast_detail_table(filtered_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a clean forecast detail table for display.
    """
    if filtered_df.empty:
        return pd.DataFrame()

    detail_df = filtered_df.copy()

    if "forecast_date" in detail_df.columns:
        detail_df["forecast_date"] = pd.to_datetime(
            detail_df["forecast_date"],
            errors="coerce",
        ).dt.date

    preferred_columns = [
        "forecast_date",
        "store_id",
        "item_id",
        "prediction",
    ]

    available_columns = [col for col in preferred_columns if col in detail_df.columns]
    detail_df = detail_df[available_columns].copy()

    if "prediction" in detail_df.columns:
        detail_df["prediction"] = pd.to_numeric(
            detail_df["prediction"],
            errors="coerce",
        ).round(2)

    rename_map = {
        "forecast_date": "Forecast date",
        "store_id": "Store",
        "item_id": "Product",
        "prediction": "Forecast demand",
    }

    return detail_df.rename(columns=rename_map)



# ============================================================
# Page renderer
# ============================================================

def render_forecast_explorer_page(payload: dict) -> None:
    """
    Render the Forecast Explorer page.
    """
    forecast_rows_df = payload.get("forecast_rows_df", pd.DataFrame())

    render_app_header(
        title="Forecast Explorer",
        subtitle=(
            "Explore forecast demand across the published horizon. "
            "Filter by date, store, and product to focus on the view that matters."
        ),
    )

    filters = render_main_filters(forecast_rows_df)
    filtered_df = apply_main_filters(forecast_rows_df, filters)
    forecast_window_label = build_forecast_window_label(filtered_df)
    st.caption(forecast_window_label)

    render_forecast_trend_chart(filtered_df)

    detail_table_df = _build_forecast_detail_table(filtered_df)

    render_clean_table(
        detail_table_df,
        title="Forecast details",
        subtitle="Filtered forecast rows for the selected date range, stores, and products.",
        height=460,
    )