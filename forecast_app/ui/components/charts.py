"""
forecast_app.ui.components.charts

Reusable chart helpers for the public forecast application.

Purpose
-------
- keep chart-building logic out of page files
- provide clean, business-friendly visuals
- support consistent chart rendering across the app
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st


# ============================================================
# Time-series chart
# ============================================================

def render_forecast_trend_chart(filtered_df: pd.DataFrame) -> None:
    """
    Render the forecast trend over time for the selected filter scope.
    """
    st.subheader("Forecast trend")

    if filtered_df.empty:
        st.info("No forecast data is available for the selected filters.")
        return

    if "forecast_date" not in filtered_df.columns or "prediction" not in filtered_df.columns:
        st.info("Forecast trend data is not available in the current snapshot.")
        return

    working_df = filtered_df.copy()
    working_df["forecast_date"] = pd.to_datetime(
        working_df["forecast_date"],
        errors="coerce",
    )

    chart_df = (
        working_df.groupby("forecast_date", as_index=False)["prediction"]
        .sum()
        .sort_values("forecast_date")
        .rename(columns={"prediction": "Forecast demand"})
    )

    chart = (
        alt.Chart(chart_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("forecast_date:T", title="Forecast date"),
            y=alt.Y("Forecast demand:Q", title="Forecast demand"),
            tooltip=[
                alt.Tooltip("forecast_date:T", title="Date"),
                alt.Tooltip("Forecast demand:Q", title="Forecast demand", format=",.0f"),
            ],
        )
        .properties(height=360)
    )

    st.altair_chart(chart, use_container_width=True)


# ============================================================
# Ranking chart helpers
# ============================================================

def _render_ranked_bar_chart(
    chart_df: pd.DataFrame,
    *,
    category_col: str,
    value_col: str,
    title_if_empty: str,
) -> None:
    """
    Render a ranked bar chart with value labels above each bar.
    """
    if chart_df.empty:
        st.info(title_if_empty)
        return

    base = alt.Chart(chart_df).encode(
        x=alt.X(
            f"{category_col}:N",
            sort="-y",
            title="",
            axis=alt.Axis(labelAngle=-30, labelLimit=180),
        ),
        y=alt.Y(
            f"{value_col}:Q",
            title="Forecast demand",
        ),
        tooltip=[
            alt.Tooltip(f"{category_col}:N", title=category_col),
            alt.Tooltip(f"{value_col}:Q", title="Forecast demand", format=",.0f"),
        ],
    )

    bars = base.mark_bar()

    labels = base.mark_text(
        dy=-8,
        fontSize=12,
        fontWeight="bold",
    ).encode(
        text=alt.Text(f"{value_col}:Q", format=",.0f"),
    )

    chart = (bars + labels).properties(height=380)

    st.altair_chart(chart, use_container_width=True)


# ============================================================
# Ranking charts
# ============================================================

def render_top_stores_chart(filtered_df: pd.DataFrame, top_n: int = 10) -> None:
    """
    Render a ranked bar chart of top stores by forecast demand.
    """
    st.subheader("Top stores")

    if filtered_df.empty or "store_id" not in filtered_df.columns or "prediction" not in filtered_df.columns:
        st.info("Store-level forecast data is not available for the selected filters.")
        return

    chart_df = (
        filtered_df.groupby("store_id", as_index=False)["prediction"]
        .sum()
        .sort_values("prediction", ascending=False)
        .head(top_n)
        .rename(columns={"store_id": "Store", "prediction": "Forecast demand"})
    )

    _render_ranked_bar_chart(
        chart_df,
        category_col="Store",
        value_col="Forecast demand",
        title_if_empty="Store-level forecast data is not available for the selected filters.",
    )


def render_top_products_chart(filtered_df: pd.DataFrame, top_n: int = 10) -> None:
    """
    Render a ranked bar chart of top products by forecast demand.
    """
    st.subheader("Top products")

    if filtered_df.empty or "item_id" not in filtered_df.columns or "prediction" not in filtered_df.columns:
        st.info("Product-level forecast data is not available for the selected filters.")
        return

    chart_df = (
        filtered_df.groupby("item_id", as_index=False)["prediction"]
        .sum()
        .sort_values("prediction", ascending=False)
        .head(top_n)
        .rename(columns={"item_id": "Product", "prediction": "Forecast demand"})
    )

    _render_ranked_bar_chart(
        chart_df,
        category_col="Product",
        value_col="Forecast demand",
        title_if_empty="Product-level forecast data is not available for the selected filters.",
    )