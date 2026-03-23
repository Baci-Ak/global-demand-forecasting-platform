"""
training.validation.rolling_windows

Rolling window split utilities for time-series model validation.

Purpose
-------
- generate leakage-safe rolling train/test splits
- keep temporal validation logic reusable across models
- provide one clear split generator for production forecasting workflows
"""

from __future__ import annotations

import pandas as pd

from training.validation.config import RollingBacktestConfig


def generate_rolling_splits(
    df: pd.DataFrame,
    config: RollingBacktestConfig,
):
    """
    Generate rolling backtest windows for time-series evaluation.

    Parameters
    ----------
    df : pd.DataFrame
        Modeling dataframe containing a date column.
    config : RollingBacktestConfig
        Shared rolling-validation configuration.

    Yields
    ------
    tuple[pd.DataFrame, pd.DataFrame]
        Train and test dataframes for each rolling split.
    """
    working_df = df.sort_values(config.date_column).copy()

    max_date = working_df[config.date_column].max()

    for window in range(config.n_windows):
        test_end = max_date - pd.Timedelta(days=window * config.horizon_days)
        test_start = test_end - pd.Timedelta(days=config.horizon_days - 1)

        train_df = working_df[working_df[config.date_column] < test_start]
        test_df = working_df[
            (working_df[config.date_column] >= test_start)
            & (working_df[config.date_column] <= test_end)
        ]

        yield train_df, test_df