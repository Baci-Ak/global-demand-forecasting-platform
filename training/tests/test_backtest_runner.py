"""
training.test_backtest_runner

Quick validation script for the reusable backtest runner.

Purpose
-------
- sanity-check end-to-end rolling backtesting
- confirm the runner returns a structured result table
- validate integration before wiring it into training scripts
"""

from __future__ import annotations

import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from training.validation.rolling_backtest import run_backtest


def main() -> None:
    """
    Build a tiny synthetic modeling dataset and run rolling backtesting.
    """
    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=180, freq="D"),
            "feature_1": range(180),
            "feature_2": range(1000, 1180),
            "sales": range(180),
        }
    )

    results_df = run_backtest(
        modeling_df=df,
        feature_columns=["feature_1", "feature_2"],
        target_column="sales",
        date_column="date",
        model_factory=lambda: RandomForestRegressor(
            n_estimators=10,
            max_depth=3,
            random_state=42,
            n_jobs=-1,
        ),
        horizon=28,
        n_windows=3,
    )

    print(results_df)


if __name__ == "__main__":
    main()