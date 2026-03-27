"""
forecast_app.ui.pages.trends

Trends page for the public forecast application.

Purpose
-------
- provide a clean view of demand movement across the forecast window
- help users see how forecast demand changes over time
- surface simple trend summaries without technical noise

Design principles
-----------------
- trend-first storytelling
- simple interaction
- chart-led presentation
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

def _build_daily_trend_table(filtered_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a daily aggregated forecast trend table.
    """
    if filtered_df.empty:
        return pd.DataFrame()

    if "forecast_date" not in filtered_df.columns or "prediction" not in filtered_df.columns:
        return pd.DataFrame()

    trend_df = filtered_df.copy()
    trend_df["forecast_date"] = pd.to_datetime(
        trend_df["forecast_date"],
        errors="coerce",
    )

    summary_df = (
        trend_df.groupby("forecast_date", as_index=False)["prediction"]
        .sum()
        .sort_values("forecast_date")
        .rename(columns={"forecast_date": "Forecast date", "prediction": "Forecast demand"})
    )

    summary_df["Forecast date"] = pd.to_datetime(summary_df["Forecast date"]).dt.date
    summary_df["Forecast demand"] = pd.to_numeric(
        summary_df["Forecast demand"],
        errors="coerce",
    ).round(2)

    summary_df["Day-over-day change"] = summary_df["Forecast demand"].diff().round(2)

    return summary_df


# ============================================================
# Page renderer
# ============================================================

def render_trends_page(payload: dict) -> None:
    """
    Render the Trends page.
    """
    forecast_rows_df = payload.get("forecast_rows_df", pd.DataFrame())

    render_app_header(
        title="Trends",
        subtitle=(
            "Track how forecast demand moves across the published window and "
            "review the daily outlook in a simple trend view."
        ),
    )

    filters = render_main_filters(forecast_rows_df)
    filtered_df = apply_main_filters(forecast_rows_df, filters)
    forecast_window_label = build_forecast_window_label(filtered_df)
    st.caption(forecast_window_label)
    

    render_forecast_trend_chart(filtered_df)

    trend_table_df = _build_daily_trend_table(filtered_df)

    render_clean_table(
        trend_table_df,
        title="Daily trend details",
        subtitle="Daily aggregated forecast demand across the selected filter scope.",
        height=460,
    )