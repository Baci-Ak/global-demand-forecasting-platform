"""
training.evaluate

Evaluation utilities for forecasting models.

Purpose
-------
- Keep model evaluation logic separate from training code
- Provide consistent metrics across notebooks and production scripts
- Support both simple benchmark metrics and M5-style competition evaluation
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def wmape(y_true: pd.Series, y_pred: pd.Series) -> float:
    """
    Compute Weighted Mean Absolute Percentage Error (WMAPE).

    Parameters
    ----------
    y_true : pd.Series
        Actual target values.
    y_pred : pd.Series
        Predicted target values.

    Returns
    -------
    float
        WMAPE value.
    """
    y_true_np = np.asarray(y_true, dtype=float)
    y_pred_np = np.asarray(y_pred, dtype=float)

    denominator = np.sum(y_true_np)

    if denominator == 0:
        raise ValueError("WMAPE is undefined because the sum of actual values is zero.")

    return float(np.sum(np.abs(y_true_np - y_pred_np)) / denominator)


def mae(y_true: pd.Series, y_pred: pd.Series) -> float:
    """
    Compute Mean Absolute Error (MAE).

    Parameters
    ----------
    y_true : pd.Series
        Actual target values.
    y_pred : pd.Series
        Predicted target values.

    Returns
    -------
    float
        MAE value.
    """
    y_true_np = np.asarray(y_true, dtype=float)
    y_pred_np = np.asarray(y_pred, dtype=float)

    return float(np.mean(np.abs(y_true_np - y_pred_np)))


def rmse(y_true: pd.Series, y_pred: pd.Series) -> float:
    """
    Compute Root Mean Squared Error (RMSE).

    Parameters
    ----------
    y_true : pd.Series
        Actual target values.
    y_pred : pd.Series
        Predicted target values.

    Returns
    -------
    float
        RMSE value.
    """
    y_true_np = np.asarray(y_true, dtype=float)
    y_pred_np = np.asarray(y_pred, dtype=float)

    return float(np.sqrt(np.mean((y_true_np - y_pred_np) ** 2)))


def rmsse(
    y_true: pd.Series,
    y_pred: pd.Series,
    y_train: pd.Series,
) -> float:
    """
    Compute Root Mean Squared Scaled Error (RMSSE) for a single series.

    This is the per-series scaled error used inside WRMSSE-style evaluation.

    Parameters
    ----------
    y_true : pd.Series
        Actual target values for the forecast horizon.
    y_pred : pd.Series
        Predicted target values for the forecast horizon.
    y_train : pd.Series
        Historical training target values for the same series, used to
        compute the scaling denominator.

    Returns
    -------
    float
        RMSSE value for the series.

    Raises
    ------
    ValueError
        If the training history is too short or the scale denominator is zero.
    """
    y_true_np = np.asarray(y_true, dtype=float)
    y_pred_np = np.asarray(y_pred, dtype=float)
    y_train_np = np.asarray(y_train, dtype=float)

    if len(y_train_np) < 2:
        raise ValueError("RMSSE requires at least two training observations.")

    scale = np.mean(np.diff(y_train_np) ** 2)

    if scale == 0:
        raise ValueError(
            "RMSSE is undefined because the training series has zero scale."
        )

    mse = np.mean((y_true_np - y_pred_np) ** 2)
    return float(np.sqrt(mse / scale))


def wrmsse(
    rmsse_values: pd.Series | np.ndarray,
    weights: pd.Series | np.ndarray,
) -> float:
    """
    Compute Weighted Root Mean Squared Scaled Error (WRMSSE) from
    precomputed per-series RMSSE values and their corresponding weights.

    This function is intentionally lightweight and reusable:
    - upstream code is responsible for producing aligned per-series RMSSE values
    - upstream code is responsible for producing aligned evaluation weights

    Parameters
    ----------
    rmsse_values : pd.Series | np.ndarray
        RMSSE values for the evaluated series.
    weights : pd.Series | np.ndarray
        Non-negative weights aligned to `rmsse_values`.

    Returns
    -------
    float
        WRMSSE value.

    Raises
    ------
    ValueError
        If inputs are empty, misaligned, or the weight sum is zero.
    """
    rmsse_np = np.asarray(rmsse_values, dtype=float)
    weights_np = np.asarray(weights, dtype=float)

    if rmsse_np.shape[0] != weights_np.shape[0]:
        raise ValueError("WRMSSE inputs must have the same length.")

    if rmsse_np.shape[0] == 0:
        raise ValueError("WRMSSE inputs must not be empty.")

    weight_sum = np.sum(weights_np)

    if weight_sum == 0:
        raise ValueError("WRMSSE is undefined because the weight sum is zero.")

    return float(np.sum(rmsse_np * weights_np) / weight_sum)