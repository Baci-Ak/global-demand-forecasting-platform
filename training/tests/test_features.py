"""
training.test_features

Quick validation script for feature engineering utilities.

Purpose
-------
- sanity-check configurable feature-set behavior
- confirm price handling works as expected
- validate feature preparation before training integration
"""

from __future__ import annotations

import pandas as pd

from training.features.features import (
    build_features,
    get_feature_columns,
    prepare_modeling_dataset,
)


def main() -> None:
    """
    Build a tiny synthetic dataset and validate feature engineering behavior.
    """
    df = pd.DataFrame(
        {
            "store_id": ["CA_1"] * 40,
            "item_id": ["ITEM_1"] * 40,
            "date": pd.date_range("2024-01-01", periods=40, freq="D"),
            "sales": range(40),
            "sell_price": [None, None, 2.5, 2.5, None] * 8,
            "temperature_2m_max": [20.0] * 40,
            "temperature_2m_min": [10.0] * 40,
            "precipitation_sum": [0.0] * 40,
            "wind_speed_10m_max": [5.0] * 40,
            "cpi_all_items": [300.0] * 40,
            "unemployment_rate": [4.0] * 40,
            "federal_funds_rate": [5.0] * 40,
            "nonfarm_payrolls": [150000.0] * 40,
            "trends_walmart": [50] * 40,
            "trends_grocery_store": [40] * 40,
            "trends_discount_store": [30] * 40,
            "trends_cleaning_supplies": [20] * 40,
        }
    )

    feature_df = build_features(df)

    print("Feature dataframe columns:")
    print(feature_df.columns.tolist())
    print()

    print("Price feature preview:")
    print(
        feature_df[
            [
                "date",
                "sell_price",
                "sell_price_missing_flag",
                "sell_price_filled",
            ]
        ].head(10)
    )
    print()

    baseline_modeling_df = prepare_modeling_dataset(
        feature_df,
        feature_set_name="calendar_lag_rolling_baseline",
    )
    price_modeling_df = prepare_modeling_dataset(
        feature_df,
        feature_set_name="baseline_plus_price",
    )

    print("Baseline feature columns:")
    print(get_feature_columns("calendar_lag_rolling_baseline"))
    print()

    print("Price feature columns:")
    print(get_feature_columns("baseline_plus_price"))
    print()

    print("Baseline modeling shape:", baseline_modeling_df.shape)
    print("Price modeling shape:", price_modeling_df.shape)


if __name__ == "__main__":
    main()