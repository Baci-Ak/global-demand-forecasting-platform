"""
forecast_app.ui.components.filters

Reusable filter controls for the public forecast application.

Purpose
-------
- keep interactive controls out of page files
- provide consistent filtering across pages
- support date, store, and product exploration

Design principles
-----------------
- simple public-facing controls
- safe defaults
- reusable output contract
"""

from __future__ import annotations

import pandas as pd
import streamlit as st


# ============================================================
# Helpers
# ============================================================

def _safe_sorted_values(series: pd.Series) -> list[str]:
    """
    Return sorted non-null string values from a series.
    """
    if series is None or series.empty:
        return []

    values = (
        series.dropna()
        .astype(str)
        .sort_values()
        .unique()
        .tolist()
    )
    return values


# ============================================================
# Main filter bar
# ============================================================

def render_main_filters(forecast_rows_df: pd.DataFrame) -> dict:
    """
    Render the main public filter controls.

    Parameters
    ----------
    forecast_rows_df : pd.DataFrame
        Forecast rows dataframe from the snapshot payload.

    Returns
    -------
    dict
        Selected filter values.
    """
    working_df = forecast_rows_df.copy()

    if "forecast_date" in working_df.columns:
        working_df["forecast_date"] = pd.to_datetime(
            working_df["forecast_date"],
            errors="coerce",
        )

    available_stores = _safe_sorted_values(working_df.get("store_id", pd.Series(dtype=object)))
    available_products = _safe_sorted_values(working_df.get("item_id", pd.Series(dtype=object)))

    min_date = None
    max_date = None

    if "forecast_date" in working_df.columns and not working_df["forecast_date"].dropna().empty:
        min_date = working_df["forecast_date"].min().date()
        max_date = working_df["forecast_date"].max().date()

    col1, col2, col3 = st.columns([1.2, 1, 1])

    with col1:
        if min_date and max_date:
            selected_date_range = st.date_input(
                "Forecast window",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )
        else:
            st.date_input(
                "Forecast window",
                disabled=True,
                value=(),
            )
            selected_date_range = ()

    with col2:
        selected_stores = st.multiselect(
            "Store",
            options=available_stores,
            placeholder="All stores",
        )

    with col3:
        selected_products = st.multiselect(
            "Product",
            options=available_products,
            placeholder="All products",
        )

    return {
        "date_range": selected_date_range,
        "stores": selected_stores,
        "products": selected_products,
    }


# ============================================================
# Dataframe filtering
# ============================================================

def apply_main_filters(forecast_rows_df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """
    Apply the selected filter values to the forecast rows dataframe.
    """
    df = forecast_rows_df.copy()

    if df.empty:
        return df

    if "forecast_date" in df.columns:
        df["forecast_date"] = pd.to_datetime(df["forecast_date"], errors="coerce")

    selected_date_range = filters.get("date_range")
    selected_stores = filters.get("stores", [])
    selected_products = filters.get("products", [])

    if (
        isinstance(selected_date_range, tuple)
        and len(selected_date_range) == 2
        and "forecast_date" in df.columns
    ):
        start_date, end_date = selected_date_range
        df = df[
            (df["forecast_date"].dt.date >= start_date)
            & (df["forecast_date"].dt.date <= end_date)
        ]

    if selected_stores and "store_id" in df.columns:
        df = df[df["store_id"].astype(str).isin(selected_stores)]

    if selected_products and "item_id" in df.columns:
        df = df[df["item_id"].astype(str).isin(selected_products)]

    return df