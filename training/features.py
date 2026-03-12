"""
training.features

Feature engineering utilities for forecasting model training.

Purpose
-------
- Convert raw modeling data into a training-ready feature set
- Keep feature logic reusable across notebooks, scripts, and future pipelines
- Ensure lag and rolling features are created in a leakage-safe way
"""

from __future__ import annotations

import pandas as pd


GROUP_COLS = ["store_id", "item_id"]

FEATURE_COLUMNS = [
    "day_of_week",
    "day_of_month",
    "week_of_year",
    "month",
    "lag_1",
    "lag_7",
    "lag_28",
    "rolling_mean_7",
    "rolling_mean_28",
]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create calendar, lag, and rolling mean features for forecasting.

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


def prepare_modeling_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only rows with a complete engineered feature set.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe after feature engineering.

    Returns
    -------
    pd.DataFrame
        Training-ready dataframe with missing feature rows removed.
    """
    modeling_df = df.dropna(subset=FEATURE_COLUMNS).copy()
    return modeling_df