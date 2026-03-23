"""
training.test_backtest

Quick validation script for the rolling backtest utility.

Purpose
-------
- sanity-check rolling split generation
- confirm split boundaries before model integration
- keep the backtest utility easy to debug in isolation
"""

from __future__ import annotations

import pandas as pd

from training.validation.rolling_windows import generate_rolling_splits


def main() -> None:
    """
    Build a tiny synthetic dataset and print rolling split summaries.
    """
    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=120, freq="D"),
            "sales": range(120),
        }
    )

    for i, (train_df, test_df) in enumerate(
        generate_rolling_splits(df=df, date_column="date", horizon=28, n_windows=3),
        start=1,
    ):
        print(f"Window {i}")
        print(
            f"  Train: {train_df['date'].min().date()} -> {train_df['date'].max().date()} "
            f"({len(train_df)} rows)"
        )
        print(
            f"  Test:  {test_df['date'].min().date()} -> {test_df['date'].max().date()} "
            f"({len(test_df)} rows)"
        )
        print()


if __name__ == "__main__":
    main()