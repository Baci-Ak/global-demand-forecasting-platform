"""
forecast_app.ui.formatters

Formatting helpers for public-facing forecast presentation.

Purpose
-------
- convert internal values into clean user-facing text
- avoid leaking technical labels directly into the UI
- keep formatting logic reusable across pages
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


# ============================================================
# Number formatting
# ============================================================

def format_int(value: Any) -> str:
    """
    Format an integer-like value for display.
    """
    if value is None:
        return "—"

    try:
        return f"{int(value):,}"
    except Exception:
        return "—"


def format_float(value: Any, decimals: int = 1) -> str:
    """
    Format a float-like value for display.
    """
    if value is None:
        return "—"

    try:
        return f"{float(value):,.{decimals}f}"
    except Exception:
        return "—"


# ============================================================
# Date and time formatting
# ============================================================

def format_timestamp(value: Any) -> str:
    """
    Format timestamp-like values for display.
    """
    if value in (None, "", "NaT"):
        return "—"

    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return ts.strftime("%d %b %Y, %H:%M UTC")
    except Exception:
        return str(value)


# ============================================================
# User-facing labeling
# ============================================================

def format_model_label(value: Any) -> str:
    """
    Translate internal model names into public-friendly labels.
    """
    if not value:
        return "Demand forecasting model"

    value_str = str(value).strip()

    mapping = {
        "gdf_lightgbm_demand_forecasting": "Demand forecasting model",
        "gdf_random_forest_demand_forecasting": "Benchmark demand model",
    }

    return mapping.get(value_str, "Demand forecasting model")


def format_feature_set_label(value: Any) -> str:
    """
    Translate internal feature-set names into public-friendly labels.
    """
    if not value:
        return "Operational forecast feature set"

    value_str = str(value).strip()

    mapping = {
        "calendar_lag_rolling_baseline": "Operational demand feature set",
        "baseline_plus_price": "Demand + price feature set",
        "baseline_plus_weather": "Demand + weather feature set",
        "baseline_plus_macro": "Demand + macro feature set",
        "baseline_plus_trends": "Demand + trends feature set",
        "full_feature_set": "Extended demand feature set",
    }

    return mapping.get(value_str, "Operational forecast feature set")


def format_data_source_label(source: str) -> str:
    """
    Convert internal data-source labels into public-facing labels.
    """
    mapping = {
        "s3_latest": "Latest published snapshot",
        "local_cache": "Cached snapshot",
        "unavailable": "Currently unavailable",
    }
    return mapping.get(source, "Unknown")