"""
forecast_app.ui.pages.product_performance

Product Performance page for the public forecast application.

Purpose
-------
- provide a product-level view of forecast demand
- help users identify highest-demand products quickly
- support product ranking and drill-down in one page

Design principles
-----------------
- product-first summary
- chart-led comparison
- clean supporting table
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from .forecast_window import build_forecast_window_label
from forecast_app.ui.components.charts import render_top_products_chart
from forecast_app.ui.components.filters import (
    apply_main_filters,
    render_main_filters,
)
from forecast_app.ui.components.tables import render_clean_table
from forecast_app.ui.styles import render_app_header


# ============================================================
# Helpers
# ============================================================

def _build_product_summary(filtered_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a product-level forecast summary dataframe.
    """
    if filtered_df.empty:
        return pd.DataFrame()

    if "item_id" not in filtered_df.columns or "prediction" not in filtered_df.columns:
        return pd.DataFrame()

    summary_df = (
        filtered_df.groupby("item_id", as_index=False)["prediction"]
        .sum()
        .sort_values("prediction", ascending=False)
        .rename(columns={"item_id": "Product", "prediction": "Forecast demand"})
    )

    summary_df["Forecast demand"] = pd.to_numeric(
        summary_df["Forecast demand"],
        errors="coerce",
    ).round(2)

    return summary_df


# ============================================================
# Page renderer
# ============================================================

def render_product_performance_page(payload: dict) -> None:
    """
    Render the Product Performance page.
    """
    forecast_rows_df = payload.get("forecast_rows_df", pd.DataFrame())

    render_app_header(
        title="Product Performance",
        subtitle=(
            "Explore expected demand by product and identify which products "
            "carry the highest forecast volume across the selected horizon."
        ),
    )

    filters = render_main_filters(forecast_rows_df)
    filtered_df = apply_main_filters(forecast_rows_df, filters)

    forecast_window_label = build_forecast_window_label(filtered_df)
    st.caption(forecast_window_label)

    render_top_products_chart(filtered_df, top_n=20)

    product_summary_df = _build_product_summary(filtered_df)

    render_clean_table(
        product_summary_df,
        title="Product forecast details",
        subtitle="Ranked forecast totals by product for the selected filter scope.",
        height=460,
    )