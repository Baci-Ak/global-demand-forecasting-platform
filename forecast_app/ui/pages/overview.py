"""
forecast_app.ui.pages.overview

Overview page for the public forecast application.

Purpose
-------
- provide the main landing page for the app
- surface the key demand outlook in a clean business-friendly format
- combine filters, KPIs, and charts into one decision-first view

Design principles
-----------------
- lead with clarity, not internal system labels
- show summary before detail
- prefer charts over raw tables
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from .forecast_window import build_forecast_window_label
from forecast_app.ui.components.cards import (
    render_overview_highlights,
    render_refresh_banner,
    render_summary_metrics,
)
from forecast_app.ui.components.charts import (
    render_forecast_trend_chart,
    render_top_products_chart,
    render_top_stores_chart,
)
from forecast_app.ui.components.filters import (
    apply_main_filters,
    render_main_filters,
)
from forecast_app.ui.styles import render_app_header


# ============================================================
# Helpers
# ============================================================

def _build_overview_highlights(filtered_df: pd.DataFrame) -> list[str]:
    """
    Build short insight chips for the overview page.
    """
    if filtered_df.empty:
        return ["No forecast data available for the selected filters"]

    highlights: list[str] = []

    if "forecast_date" in filtered_df.columns and "prediction" in filtered_df.columns:
        trend_df = (
            filtered_df.groupby("forecast_date", as_index=False)["prediction"]
            .sum()
            .sort_values("forecast_date")
        )

        if len(trend_df) >= 2:
            first_value = float(trend_df["prediction"].iloc[0])
            last_value = float(trend_df["prediction"].iloc[-1])

            if last_value > first_value:
                highlights.append("Demand outlook rises across the selected window")
            elif last_value < first_value:
                highlights.append("Demand outlook softens across the selected window")
            else:
                highlights.append("Demand outlook remains stable across the selected window")

    if "store_id" in filtered_df.columns:
        store_count = filtered_df["store_id"].nunique()
        highlights.append(f"{store_count:,} stores included")

    if "item_id" in filtered_df.columns:
        product_count = filtered_df["item_id"].nunique()
        highlights.append(f"{product_count:,} products included")

    return highlights[:4]


def _compute_summary_metrics(filtered_df: pd.DataFrame) -> dict:
    """
    Compute the primary KPI values for the overview page.
    """
    if filtered_df.empty:
        return {
            "total_forecast": 0,
            "average_daily_forecast": 0,
            "store_count": 0,
            "product_count": 0,
        }

    total_forecast = 0
    average_daily_forecast = 0
    store_count = 0
    product_count = 0

    if "prediction" in filtered_df.columns:
        total_forecast = float(filtered_df["prediction"].sum())

    if "forecast_date" in filtered_df.columns and "prediction" in filtered_df.columns:
        unique_days = filtered_df["forecast_date"].nunique()
        if unique_days and unique_days > 0:
            average_daily_forecast = float(filtered_df["prediction"].sum() / unique_days)

    if "store_id" in filtered_df.columns:
        store_count = int(filtered_df["store_id"].nunique())

    if "item_id" in filtered_df.columns:
        product_count = int(filtered_df["item_id"].nunique())

    return {
        "total_forecast": total_forecast,
        "average_daily_forecast": average_daily_forecast,
        "store_count": store_count,
        "product_count": product_count,
    }




# ============================================================
# Page renderer
# ============================================================

def render_overview_page(payload: dict) -> None:
    """
    Render the Overview page.
    """
    metadata = payload.get("metadata", {})
    forecast_rows_df = payload.get("forecast_rows_df", pd.DataFrame())

    render_app_header(
        title="Demand Forecast Overview",
        subtitle=(
            "Explore the latest published demand forecast window with summaries, "
            "trend views, and ranked demand drivers across the available forecast horizon."
        ),
    )

    filters = render_main_filters(forecast_rows_df)
    filtered_df = apply_main_filters(forecast_rows_df, filters)

    metrics = _compute_summary_metrics(filtered_df)
    highlights = _build_overview_highlights(filtered_df)
    forecast_window_label = build_forecast_window_label(filtered_df)
    st.caption(forecast_window_label)

    render_overview_highlights(highlights)

    render_summary_metrics(
        total_forecast=metrics["total_forecast"],
        average_daily_forecast=metrics["average_daily_forecast"],
        store_count=metrics["store_count"],
        product_count=metrics["product_count"],
    )

    render_refresh_banner(
        refreshed_at=metadata.get("refreshed_at"),
        source_generated_at=metadata.get("source_generated_at"),
    )

    st.markdown("")

    col1, col2 = st.columns([1.4, 1])

    with col1:
        render_forecast_trend_chart(filtered_df)

    with col2:
        render_top_stores_chart(filtered_df, top_n=10)

    st.markdown("")

    render_top_products_chart(filtered_df, top_n=15)