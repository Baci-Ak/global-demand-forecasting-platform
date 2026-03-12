"""
Dashboard-wide constants.

Purpose
-------
Central place for non-secret application constants so page modules,
services, and shared UI components do not hardcode repeated values.
"""

from __future__ import annotations

APP_NAME = "Global Demand Forecasting Dashboard"
APP_ICON = "📈"

# ------------------------------------------------------------------------------
# Warehouse tables
# ------------------------------------------------------------------------------

GOLD_SCHEMA = "gold"
GOLD_FEATURE_MART = "gold_m5_daily_feature_mart"
GOLD_FEATURE_MART_FQN = f"{GOLD_SCHEMA}.{GOLD_FEATURE_MART}"

# ------------------------------------------------------------------------------
# Dashboard serving datasets
# ------------------------------------------------------------------------------

FILTER_OPTIONS_DATASET = "dashboard_filter_options"
EXEC_DAILY_DATASET = "dashboard_exec_daily"
STORE_ITEM_DAILY_DATASET = "dashboard_store_item_daily"
PIPELINE_HEALTH_DATASET = "dashboard_pipeline_health"

# ------------------------------------------------------------------------------
# App layout
# ------------------------------------------------------------------------------

DEFAULT_PAGE_TITLE = "Forecasting Intelligence"
DEFAULT_LAYOUT = "wide"

# ------------------------------------------------------------------------------
# Defaults
# ------------------------------------------------------------------------------

DEFAULT_TOP_N = 10
DEFAULT_DATE_WINDOW_DAYS = 90
DEFAULT_CACHE_TTL_SECONDS = 300

# ------------------------------------------------------------------------------
# Metric selectors
# ------------------------------------------------------------------------------

METRIC_OPTIONS = (
    "Sales",
    "Sell Price",
    "Avg Daily Sales",
    "Sales Growth %",
)

GRANULARITY_OPTIONS = (
    "Daily",
    "Weekly",
    "Monthly",
)

COMPARE_PERIOD_OPTIONS = (
    "Previous Week",
    "Previous Month",
    "Previous Same Period",
)

# ------------------------------------------------------------------------------
# External driver groups
# ------------------------------------------------------------------------------

DRIVER_FAMILY_OPTIONS = (
    "Weather",
    "Macro",
    "Search Trends",
    "Combined",
)

# ------------------------------------------------------------------------------
# Navigation pages
# ------------------------------------------------------------------------------

NAV_PAGES = (
    "Executive Overview",
    "Sales & Demand",
    "Pricing & Commercial",
    "External Drivers",
    "Store / Item Drilldown",
    "Forecast Readiness",
    "Data Quality & Freshness",
)

# ------------------------------------------------------------------------------
# Global filters used across dashboard
# ------------------------------------------------------------------------------

GLOBAL_FILTER_FIELDS = (
    "date_range",
    "state_id",
    "store_id",
    "cat_id",
    "dept_id",
    "item_id",
    "wm_yr_wk",
    "top_n",
    "metric",
    "granularity",
)

# ------------------------------------------------------------------------------
# Drilldown page required selectors
# ------------------------------------------------------------------------------

DRILLDOWN_REQUIRED_FILTER_FIELDS = (
    "store_id",
    "item_id",
    "date_range",
)

# ------------------------------------------------------------------------------
# Forecast readiness statuses
# ------------------------------------------------------------------------------

READINESS_STATUS = (
    "Ready",
    "Partial Coverage",
    "Data Issue",
)

# ------------------------------------------------------------------------------
# Supported backend types
# ------------------------------------------------------------------------------

SUPPORTED_DATA_BACKENDS = (
    "warehouse",
    "extract",
)