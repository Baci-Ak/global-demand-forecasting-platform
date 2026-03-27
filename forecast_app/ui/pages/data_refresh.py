"""
forecast_app.ui.pages.data_refresh

Data and refresh page for the public forecast application.

Purpose
-------
- provide trust and freshness information for the published forecast
- keep technical status details out of the main business pages
- present refresh information in user-friendly language
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from forecast_app.ui.components.tables import render_clean_table
from forecast_app.ui.formatters import (
    format_data_source_label,
    format_feature_set_label,
    format_int,
    format_model_label,
    format_timestamp,
)
from forecast_app.ui.styles import render_app_header


def _build_refresh_summary(metadata: dict, payload: dict) -> pd.DataFrame:
    """
    Build a compact refresh summary table for display.
    """
    rows = [
        {
            "Metric": "Forecast model",
            "Value": format_model_label(metadata.get("model_name")),
        },
        {
            "Metric": "Feature set",
            "Value": format_feature_set_label(metadata.get("feature_set_name")),
        },
        {
            "Metric": "Model version",
            "Value": str(metadata.get("model_version") or "—"),
        },
        {
            "Metric": "Forecast rows",
            "Value": format_int(metadata.get("forecast_row_count")),
        },
        {
            "Metric": "Forecast series",
            "Value": format_int(metadata.get("forecast_series_count")),
        },
        {
            "Metric": "Forecast horizon",
            "Value": f"{format_int(metadata.get('forecast_horizon_days'))} days",
        },
        {
            "Metric": "Forecast generated",
            "Value": format_timestamp(metadata.get("source_generated_at")),
        },
        {
            "Metric": "App refreshed",
            "Value": format_timestamp(metadata.get("refreshed_at")),
        },
        {
            "Metric": "Metadata source",
            "Value": format_data_source_label(payload.get("metadata_source", "unavailable")),
        },
        {
            "Metric": "Forecast data source",
            "Value": format_data_source_label(payload.get("forecast_rows_source", "unavailable")),
        },
    ]

    return pd.DataFrame(rows)


def render_data_refresh_page(payload: dict) -> None:
    """
    Render the Data & Refresh page.
    """
    metadata = payload.get("metadata", {})
    freshness_df = payload.get("freshness_df", pd.DataFrame())
    monitoring_df = payload.get("monitoring_df", pd.DataFrame())

    render_app_header(
        title="Data & Refresh",
        subtitle=(
            "See when the published forecast was generated, how much data is included, "
            "and the latest refresh information behind the dashboard."
        ),
    )

    summary_df = _build_refresh_summary(metadata, payload)

    render_clean_table(
        summary_df,
        title="Forecast refresh summary",
        subtitle="Latest published forecast and application refresh details.",
        height=420,
    )

    render_clean_table(
        freshness_df,
        title="Latest forecast batch",
        subtitle="Latest forecast freshness record available in the published snapshot.",
        height=260,
    )

    render_clean_table(
        monitoring_df.head(25) if not monitoring_df.empty else monitoring_df,
        title="Recent forecast updates",
        subtitle="Recent forecast batch records included in the published snapshot.",
        height=420,
    )