"""
forecast_app.app

Streamlit entrypoint for the Layer 2 forecast interface.

Purpose
-------
- provide the first public-facing UI on top of warehouse-served forecasts
- load Layer 2 datasets through the data-access layer
- render the UI through dedicated page helpers

Design principles
-----------------
- keep the entrypoint thin
- keep data access separate from presentation
- make the app easy to evolve into a fuller multi-page product later
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from forecast_app.data_access.warehouse_queries import (
    fetch_forecast_rows,
    fetch_forecast_run_monitoring,
    fetch_latest_forecast_freshness,
)
from forecast_app.ui.pages import (
    render_forecast_run_monitoring,
    render_latest_forecast_freshness,
    render_recent_forecast_rows,
)


st.set_page_config(
    page_title="GDF Forecast App",
    layout="wide",
)

st.title("Global Demand Forecasting")
st.caption("Layer 2 forecast application reading from production warehouse outputs")

freshness_df = fetch_latest_forecast_freshness()
monitoring_df = fetch_forecast_run_monitoring(limit=50)
forecast_rows_df = fetch_forecast_rows(limit=500)

render_latest_forecast_freshness(freshness_df)
render_forecast_run_monitoring(monitoring_df)
render_recent_forecast_rows(forecast_rows_df)