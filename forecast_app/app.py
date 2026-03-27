"""
forecast_app.app

Public Streamlit entrypoint for the forecast application.

Purpose
-------
- provide the main public-facing app shell
- load snapshot-backed forecast data
- route users between product-style pages
- keep the entrypoint thin and easy to maintain

Design principles
-----------------
- snapshot-first reads only
- business-friendly navigation
- modular page rendering
- future-ready structure for deployment beyond Streamlit
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
from forecast_app.ui.navigation import render_sidebar_navigation
from forecast_app.ui.pages.about import render_about_page
from forecast_app.ui.pages.data_refresh import render_data_refresh_page
from forecast_app.ui.pages.forecast_explorer import render_forecast_explorer_page
from forecast_app.ui.pages.overview import render_overview_page
from forecast_app.ui.pages.product_performance import render_product_performance_page
from forecast_app.ui.pages.store_performance import render_store_performance_page
from forecast_app.ui.pages.trends import render_trends_page
from forecast_app.ui.styles import apply_global_styles


# ============================================================
# Page configuration
# ============================================================

st.set_page_config(
    page_title="Global Demand Forecasting",
    page_icon="📈",
    layout="wide",
)

apply_global_styles()


# ============================================================
# Snapshot data loading
# ============================================================

@st.cache_data(show_spinner=False)
def load_snapshot_payload() -> dict:
    """
    Load all snapshot-backed datasets required by the public app.

    Returns
    -------
    dict
        Dictionary containing metadata, source labels, and dataframes.
    """
    metadata, metadata_source = read_snapshot_metadata()
    freshness_df, freshness_source = read_latest_forecast_freshness()
    monitoring_df, monitoring_source = read_forecast_run_monitoring()
    forecast_rows_df, forecast_rows_source = read_forecast_rows()

    return {
        "metadata": metadata,
        "metadata_source": metadata_source,
        "freshness_df": freshness_df,
        "freshness_source": freshness_source,
        "monitoring_df": monitoring_df,
        "monitoring_source": monitoring_source,
        "forecast_rows_df": forecast_rows_df,
        "forecast_rows_source": forecast_rows_source,
    }


payload = load_snapshot_payload()


# ============================================================
# Sidebar navigation
# ============================================================

selected_page = render_sidebar_navigation()


# ============================================================
# Page routing
# ============================================================

if selected_page == "Overview":
    render_overview_page(payload)

elif selected_page == "Forecast Explorer":
    render_forecast_explorer_page(payload)

elif selected_page == "Store Performance":
    render_store_performance_page(payload)

elif selected_page == "Product Performance":
    render_product_performance_page(payload)

elif selected_page == "Trends":
    render_trends_page(payload)

elif selected_page == "Data & Refresh":
    render_data_refresh_page(payload)

elif selected_page == "About":
    render_about_page(payload)

else:
    st.error("The selected page could not be loaded.")