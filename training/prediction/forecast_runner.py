"""
training.forecast_runner

Recursive batch forecasting utilities for demand forecasting.

Purpose
-------
- prepare the latest available feature state per series
- generate multi-step forecasts recursively
- produce a warehouse-ready forecast output dataframe
"""

from __future__ import annotations

from datetime import timedelta

import pandas as pd

from training.features.features import build_features, get_feature_columns


# ============================================================
# Forecast horizon preparation
# ============================================================
# Purpose:
# - isolate the most recent history for each series
# - keep recursive forecasting logic reusable
# ============================================================


def get_latest_series_history(
    df: pd.DataFrame,
    history_days: int = 60,
) -> pd.DataFrame:
    """
    Keep only the most recent history window per series.

    Parameters
    ----------
    df : pd.DataFrame
        Raw historical dataframe.
    history_days : int, default=60
        Number of recent days to keep per series.

    Returns
    -------
    pd.DataFrame
        Recent history per (store_id, item_id).
    """
    working_df = df.copy()
    working_df["date"] = pd.to_datetime(working_df["date"])
    working_df = working_df.sort_values(["store_id", "item_id", "date"])

    return (
        working_df.groupby(["store_id", "item_id"], group_keys=False)
        .tail(history_days)
        .reset_index(drop=True)
    )


# ============================================================
# Recursive forecasting engine
# ============================================================
# Purpose:
# - generate forecasts one day at a time
# - feed prior predictions back as future lag inputs
# - keep the first production inference path simple and explicit
# ============================================================


def run_recursive_forecast(
    model,
    history_df: pd.DataFrame,
    forecast_horizon: int = 28,
    feature_set_name: str = "calendar_lag_rolling_baseline",
) -> pd.DataFrame:
    """
    Generate recursive forecasts for all series.

    Parameters
    ----------
    model :
        Trained forecasting model.
    history_df : pd.DataFrame
        Historical dataframe containing at least the raw fields needed by
        training.features.build_features.
    forecast_horizon : int, default=28
        Number of future days to forecast.
    feature_set_name : str, default="calendar_lag_rolling_baseline"
        Feature-set name used by the trained model.

    Returns
    -------
    pd.DataFrame
        Forecast dataframe with one row per (store_id, item_id, forecast_date).
    """
    feature_columns = get_feature_columns(feature_set_name)
    working_df = history_df.copy()
    working_df["date"] = pd.to_datetime(working_df["date"])
    working_df = working_df.sort_values(["store_id", "item_id", "date"]).reset_index(drop=True)

    forecast_rows: list[dict] = []

    for step in range(1, forecast_horizon + 1):
        latest_dates = (
            working_df.groupby(["store_id", "item_id"], as_index=False)["date"]
            .max()
            .rename(columns={"date": "latest_date"})
        )

        next_rows = latest_dates.copy()
        next_rows["date"] = next_rows["latest_date"] + timedelta(days=1)
        next_rows = next_rows.drop(columns=["latest_date"])

        metadata_cols = [
            "item_id",
            "dept_id",
            "cat_id",
            "store_id",
            "state_id",
            "wm_yr_wk",
            "sell_price",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max",
            "cpi_all_items",
            "unemployment_rate",
            "federal_funds_rate",
            "nonfarm_payrolls",
            "trends_walmart",
            "trends_grocery_store",
            "trends_discount_store",
            "trends_cleaning_supplies",
        ]

        latest_context = (
            working_df.sort_values(["store_id", "item_id", "date"])
            .groupby(["store_id", "item_id"], as_index=False)
            .tail(1)[metadata_cols]
            .reset_index(drop=True)
        )

        next_rows = next_rows.merge(
            latest_context,
            on=["store_id", "item_id"],
            how="left",
        )

        next_rows["sales"] = float("nan")
        next_rows["is_future"] = 1
        working_df["is_future"] = working_df.get("is_future", 0)

        candidate_df = pd.concat([working_df, next_rows], ignore_index=True)
        candidate_df = build_features(candidate_df)

        forecast_input_df = (
            candidate_df[candidate_df["is_future"] == 1]
            .sort_values(["store_id", "item_id", "date"])
            .groupby(["store_id", "item_id"], as_index=False)
            .tail(1)
            .reset_index(drop=True)
        )

        preds = model.predict(forecast_input_df[feature_columns])
        forecast_input_df["prediction"] = preds
        forecast_input_df["forecast_step"] = step

        forecast_rows.append(
            forecast_input_df[
                [
                    "store_id",
                    "item_id",
                    "date",
                    "forecast_step",
                    "prediction",
                ]
            ].rename(columns={"date": "forecast_date"})
        )

        next_rows = forecast_input_df.copy()
        next_rows["sales"] = next_rows["prediction"]
        next_rows = next_rows.drop(columns=["prediction", "forecast_step"])

        working_df = pd.concat([working_df, next_rows], ignore_index=True)
        working_df = working_df.sort_values(["store_id", "item_id", "date"]).reset_index(drop=True)

    forecast_df = pd.concat(forecast_rows, ignore_index=True)
    return forecast_df