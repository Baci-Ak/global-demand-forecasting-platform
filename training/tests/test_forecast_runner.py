"""
training.test_forecast_runner

Quick validation script for the recursive forecasting engine.

Purpose
-------
- sanity-check multi-step recursive forecasting
- confirm forecast output shape and columns
- validate forecast runner behavior before MLflow model integration
"""

from __future__ import annotations

import pandas as pd
from lightgbm import LGBMRegressor

from training.features.features import (
    build_features,
    get_feature_columns,
    prepare_modeling_dataset,
)
from training.prediction.forecast_runner import (
    get_latest_series_history,
    run_recursive_forecast,
)


def main() -> None:
    """
    Build a tiny synthetic dataset, fit a small model, and run forecasts.
    """
    rows = []
    for store_id in ["CA_1", "TX_1"]:
        for item_id in ["ITEM_1", "ITEM_2"]:
            for i, date in enumerate(pd.date_range("2024-01-01", periods=90, freq="D")):
                rows.append(
                    {
                        "id": f"{store_id}_{item_id}_{date.date()}",
                        "item_id": item_id,
                        "dept_id": "FOODS_1",
                        "cat_id": "FOODS",
                        "store_id": store_id,
                        "state_id": store_id.split("_")[0],
                        "d": f"d_{i+1}",
                        "date": date,
                        "wm_yr_wk": 11101 + (i // 7),
                        "sales": float((i % 7) + 10),
                        "sell_price": 2.5,
                        "temperature_2m_max": 25.0,
                        "temperature_2m_min": 15.0,
                        "precipitation_sum": 0.0,
                        "wind_speed_10m_max": 5.0,
                        "cpi_all_items": 300.0,
                        "unemployment_rate": 4.0,
                        "federal_funds_rate": 5.0,
                        "nonfarm_payrolls": 150000.0,
                        "trends_walmart": 50,
                        "trends_grocery_store": 40,
                        "trends_discount_store": 30,
                        "trends_cleaning_supplies": 20,
                    }
                )

    df = pd.DataFrame(rows)

    feature_df = build_features(df)
    modeling_df = prepare_modeling_dataset(
        feature_df,
        feature_set_name="calendar_lag_rolling_baseline",
    )
    feature_columns = get_feature_columns("calendar_lag_rolling_baseline")

    model = LGBMRegressor(
        objective="regression",
        num_leaves=16,
        learning_rate=0.05,
        n_estimators=50,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )
    model.fit(modeling_df[feature_columns], modeling_df["sales"])

    history_df = get_latest_series_history(df, history_days=60)

    forecast_df = run_recursive_forecast(
        model=model,
        history_df=history_df,
        forecast_horizon=7,
        feature_set_name="calendar_lag_rolling_baseline",
    )

    print("Forecast output shape:", forecast_df.shape)
    print()
    print(forecast_df.head(20))


if __name__ == "__main__":
    main()