"""
training.evaluate

Evaluation utilities for forecasting models.

Purpose
-------
- Keep model evaluation logic separate from training code
- Provide consistent metrics across notebooks and production scripts
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
    denominator = np.sum(y_true)

    if denominator == 0:
        raise ValueError("WMAPE is undefined because the sum of actual values is zero.")

    return float(np.sum(np.abs(y_true - y_pred)) / denominator)