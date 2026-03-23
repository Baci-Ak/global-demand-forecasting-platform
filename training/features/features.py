"""
training.features

Feature engineering utilities for forecasting model training.

Purpose
-------
- Convert raw modeling data into a training-ready feature set
- Keep feature logic reusable across notebooks, scripts, and future pipelines
- Ensure lag and rolling features are created in a leakage-safe way
- Support configurable feature-set experiments for model comparison
"""

from __future__ import annotations

import pandas as pd


# ============================================================
# Core grouping and feature-set definitions
# ============================================================
# Purpose:
# - centralize reusable grouping columns
# - define the approved feature-set experiment families
# - keep training scripts free from hardcoded feature lists
# ============================================================

GROUP_COLS = ["store_id", "item_id"]

CALENDAR_FEATURE_COLUMNS = [
    "day_of_week",
    "day_of_month",
    "week_of_year",
    "month",
]

LAG_ROLLING_FEATURE_COLUMNS = [
    "lag_1",
    "lag_7",
    "lag_28",
    "rolling_mean_7",
    "rolling_mean_28",
]

PRICE_FEATURE_COLUMNS = [
    "sell_price_filled",
    "sell_price_missing_flag",
]

WEATHER_FEATURE_COLUMNS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "wind_speed_10m_max",
]

MACRO_FEATURE_COLUMNS = [
    "cpi_all_items",
    "unemployment_rate",
    "federal_funds_rate",
    "nonfarm_payrolls",
]

TRENDS_FEATURE_COLUMNS = [
    "trends_walmart",
    "trends_grocery_store",
    "trends_discount_store",
    "trends_cleaning_supplies",
]

FEATURE_SET_REGISTRY: dict[str, list[str]] = {
    "calendar_lag_rolling_baseline": (
        CALENDAR_FEATURE_COLUMNS
        + LAG_ROLLING_FEATURE_COLUMNS
    ),
    "baseline_plus_price": (
        CALENDAR_FEATURE_COLUMNS
        + LAG_ROLLING_FEATURE_COLUMNS
        + PRICE_FEATURE_COLUMNS
    ),
    "baseline_plus_weather": (
        CALENDAR_FEATURE_COLUMNS
        + LAG_ROLLING_FEATURE_COLUMNS
        + WEATHER_FEATURE_COLUMNS
    ),
    "baseline_plus_macro": (
        CALENDAR_FEATURE_COLUMNS
        + LAG_ROLLING_FEATURE_COLUMNS
        + MACRO_FEATURE_COLUMNS
    ),
    "baseline_plus_trends": (
        CALENDAR_FEATURE_COLUMNS
        + LAG_ROLLING_FEATURE_COLUMNS
        + TRENDS_FEATURE_COLUMNS
    ),
    "full_feature_set": (
        CALENDAR_FEATURE_COLUMNS
        + LAG_ROLLING_FEATURE_COLUMNS
        + PRICE_FEATURE_COLUMNS
        + WEATHER_FEATURE_COLUMNS
        + MACRO_FEATURE_COLUMNS
        + TRENDS_FEATURE_COLUMNS
    ),
}

DEFAULT_FEATURE_SET_NAME = "calendar_lag_rolling_baseline"
FEATURE_COLUMNS = FEATURE_SET_REGISTRY[DEFAULT_FEATURE_SET_NAME]


# ============================================================
# Feature engineering
# ============================================================
# Purpose:
# - create reusable time-series features
# - keep feature generation leakage-safe
# - preserve a clean separation between raw data loading and modeling
# ============================================================

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create calendar, lag, rolling mean, and prepared external features
    for forecasting.

    Parameters
    ----------
    df : pd.DataFrame
        Raw modeling dataframe loaded from the Gold feature mart.

    Returns
    -------
    pd.DataFrame
        Dataframe with engineered features added.
    """
    feature_df = df.copy()

    # ------------------------------------------------------------
    # Ensure correct types and ordering
    # ------------------------------------------------------------
    feature_df["date"] = pd.to_datetime(feature_df["date"])
    feature_df = feature_df.sort_values(GROUP_COLS + ["date"]).reset_index(drop=True)

    # ------------------------------------------------------------
    # Normalize numeric external columns
    # ------------------------------------------------------------
    raw_numeric_columns = [
        "sell_price",
        *WEATHER_FEATURE_COLUMNS,
        *MACRO_FEATURE_COLUMNS,
        *TRENDS_FEATURE_COLUMNS,
    ]

    for col in raw_numeric_columns:
        if col in feature_df.columns:
            feature_df[col] = pd.to_numeric(feature_df[col], errors="coerce")

    # ------------------------------------------------------------
    # Price features
    # ------------------------------------------------------------
    # Keep both:
    # 1) a missingness indicator
    # 2) a filled numeric value for model consumption
    feature_df["sell_price_missing_flag"] = feature_df["sell_price"].isna().astype(int)

    feature_df["sell_price_filled"] = (
        feature_df.groupby(GROUP_COLS)["sell_price"]
        .transform(lambda s: s.ffill().bfill())
    )

    # Fallback in case an entire series has no price values at all
    feature_df["sell_price_filled"] = feature_df["sell_price_filled"].fillna(0.0)

    # ------------------------------------------------------------
    # Calendar features
    # ------------------------------------------------------------
    feature_df["day_of_week"] = feature_df["date"].dt.dayofweek
    feature_df["day_of_month"] = feature_df["date"].dt.day
    feature_df["week_of_year"] = feature_df["date"].dt.isocalendar().week.astype(int)
    feature_df["month"] = feature_df["date"].dt.month

    # ------------------------------------------------------------
    # Lag features
    # ------------------------------------------------------------
    feature_df["lag_1"] = feature_df.groupby(GROUP_COLS)["sales"].shift(1)
    feature_df["lag_7"] = feature_df.groupby(GROUP_COLS)["sales"].shift(7)
    feature_df["lag_28"] = feature_df.groupby(GROUP_COLS)["sales"].shift(28)

    # ------------------------------------------------------------
    # Rolling mean features
    # ------------------------------------------------------------
    # shift(1) ensures the current day's sales are excluded
    feature_df["rolling_mean_7"] = (
        feature_df.groupby(GROUP_COLS)["sales"].shift(1).rolling(7).mean()
    )

    feature_df["rolling_mean_28"] = (
        feature_df.groupby(GROUP_COLS)["sales"].shift(1).rolling(28).mean()
    )

    return feature_df


# ============================================================
# Feature-set selection helpers
# ============================================================
# Purpose:
# - provide one approved interface for selecting experiment feature sets
# - prevent feature drift across notebooks and training scripts
# ============================================================

def get_feature_columns(feature_set_name: str = DEFAULT_FEATURE_SET_NAME) -> list[str]:
    """
    Return the feature columns for a named experiment feature set.

    Parameters
    ----------
    feature_set_name : str, default="calendar_lag_rolling_baseline"
        Name of the approved feature-set experiment.

    Returns
    -------
    list[str]
        Feature columns for the selected feature set.

    Raises
    ------
    ValueError
        If the feature-set name is not registered.
    """
    if feature_set_name not in FEATURE_SET_REGISTRY:
        valid_names = ", ".join(FEATURE_SET_REGISTRY.keys())
        raise ValueError(
            f"Unknown feature set '{feature_set_name}'. Valid options: {valid_names}."
        )

    return FEATURE_SET_REGISTRY[feature_set_name]


# ============================================================
# Modeling dataset preparation
# ============================================================
# Purpose:
# - keep only rows with a complete usable feature set
# - allow different experiment families to reuse the same logic
# ============================================================

def prepare_modeling_dataset(
    df: pd.DataFrame,
    feature_set_name: str = DEFAULT_FEATURE_SET_NAME,
) -> pd.DataFrame:
    """
    Keep only rows with a complete engineered feature set.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe after feature engineering.
    feature_set_name : str, default="calendar_lag_rolling_baseline"
        Name of the feature set that will be used for modeling.

    Returns
    -------
    pd.DataFrame
        Training-ready dataframe with missing feature rows removed.
    """
    feature_columns = get_feature_columns(feature_set_name=feature_set_name)
    modeling_df = df.dropna(subset=feature_columns).copy()
    return modeling_df