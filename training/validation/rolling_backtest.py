"""
training.validation.rolling_backtest

Reusable rolling backtest runner for forecasting models.

Purpose
-------
- run a model across multiple rolling time windows
- compute consistent validation metrics per window
- return a structured result table for model comparison
"""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd

from training.evaluation.evaluate import mae, rmse, wmape
from training.validation.config import RollingBacktestConfig
from training.validation.rolling_windows import generate_rolling_splits


def run_rolling_backtest(
    modeling_df: pd.DataFrame,
    feature_columns: list[str],
    model_factory: Callable[[], object],
    config: RollingBacktestConfig,
) -> pd.DataFrame:
    """
    Run rolling backtesting for a model factory on a prepared modeling dataset.

    Parameters
    ----------
    modeling_df : pd.DataFrame
        Training-ready dataframe with engineered features already present.
    feature_columns : list[str]
        Feature columns used for model fitting and prediction.
    model_factory : Callable[[], object]
        Callable that returns a fresh model instance for each window.
    config : RollingBacktestConfig
        Shared rolling-validation configuration.

    Returns
    -------
    pd.DataFrame
        One row per backtest window with evaluation metrics and row counts.
    """
    results: list[dict] = []

    for window_idx, (train_df, test_df) in enumerate(
        generate_rolling_splits(
            df=modeling_df,
            config=config,
        ),
        start=1,
    ):
        if train_df.empty:
            raise ValueError(
                f"Backtest window {window_idx} has an empty training set. "
                "Increase the available history or reduce the number of windows."
            )

        if test_df.empty:
            raise ValueError(
                f"Backtest window {window_idx} has an empty test set. "
                "Check the horizon, date coverage, and number of windows."
            )

        X_train = train_df[feature_columns]
        y_train = train_df[config.target_column]

        X_test = test_df[feature_columns]
        y_test = test_df[config.target_column]

        model = model_factory()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        results.append(
            {
                "window": window_idx,
                "train_start_date": train_df[config.date_column].min(),
                "train_end_date": train_df[config.date_column].max(),
                "test_start_date": test_df[config.date_column].min(),
                "test_end_date": test_df[config.date_column].max(),
                "train_rows": len(train_df),
                "test_rows": len(test_df),
                "wmape": wmape(y_test, y_pred),
                "mae": mae(y_test, y_pred),
                "rmse": rmse(y_test, y_pred),
            }
        )

    return pd.DataFrame(results)