"""
forecast_app.app

Streamlit entrypoint for the Layer 2 forecast interface.

Purpose
-------
- provide the first public-facing UI on top of production forecast snapshots
- read the latest successful snapshot from S3
- fall back to local cached snapshots if S3 is unavailable

Design principles
-----------------
- keep the entrypoint thin
- keep data access separate from presentation
- never require live warehouse connectivity for user-facing reads
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from forecast_app.data_access.snapshot_reader import (
    read_forecast_rows,
    read_forecast_run_monitoring,
    read_latest_forecast_freshness,
    read_snapshot_metadata,
)
from forecast_app.ui.pages import (
    render_app_shell_styles,
    render_forecast_run_monitoring,
    render_latest_forecast_freshness,
    render_recent_forecast_rows,
    render_snapshot_metadata,
    render_snapshot_status,
)


st.set_page_config(
    page_title="GDF Forecast App",
    layout="wide",
)
render_app_shell_styles()

st.title("Global Demand Forecasting")
st.caption("Layer 2 forecast application reading from production snapshot outputs")

metadata, metadata_source = read_snapshot_metadata()
freshness_df, freshness_source = read_latest_forecast_freshness()
monitoring_df, monitoring_source = read_forecast_run_monitoring()
forecast_rows_df, forecast_rows_source = read_forecast_rows()

render_snapshot_status(
    metadata_source=metadata_source,
    freshness_source=freshness_source,
    monitoring_source=monitoring_source,
    forecast_rows_source=forecast_rows_source,
)
render_snapshot_metadata(metadata)
render_latest_forecast_freshness(freshness_df)
render_forecast_run_monitoring(monitoring_df)
render_recent_forecast_rows(forecast_rows_df)