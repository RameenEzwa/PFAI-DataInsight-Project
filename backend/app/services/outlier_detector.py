from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from app.config import get_settings
from app.utils import json_safe


def numeric_columns(df: pd.DataFrame, columns: list[str] | None = None) -> list[str]:
    available = df.select_dtypes(include=[np.number]).columns.tolist()
    if not columns:
        return [str(col) for col in available]
    return [col for col in columns if col in available]


def detect_outliers(
    df: pd.DataFrame,
    method: str = "iqr",
    columns: list[str] | None = None,
    contamination: float = 0.03,
    z_threshold: float = 3.0,
) -> tuple[pd.Series, dict[str, Any]]:
    cols = numeric_columns(df, columns)
    if not cols:
        mask = pd.Series(False, index=df.index)
        return mask, {"method": method, "columns": [], "outlier_count": 0, "outlier_pct": 0, "per_column": []}

    if method == "zscore":
        mask, per_column = _zscore(df, cols, z_threshold)
    elif method == "isolation_forest":
        mask, per_column = _isolation_forest(df, cols, contamination)
    else:
        mask, per_column = _iqr(df, cols)

    settings = get_settings()
    indices = [int(i) for i in df.index[mask].tolist()[: settings.outlier_index_limit]]
    report = {
        "method": method,
        "columns": cols,
        "outlier_count": int(mask.sum()),
        "outlier_pct": float(mask.mean() if len(mask) else 0),
        "outlier_indices": indices,
        "index_limit": settings.outlier_index_limit,
        "per_column": per_column,
    }
    return mask, json_safe(report)


def apply_outlier_strategy(
    df: pd.DataFrame,
    mask: pd.Series,
    method: str,
    columns: list[str] | None,
    strategy: str = "retain",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    cols = numeric_columns(df, columns)
    if strategy == "remove":
        cleaned = df.loc[~mask].copy()
        return cleaned, {"strategy": "remove", "rows_removed": int(mask.sum())}
    if strategy == "cap":
        cleaned = df.copy()
        caps = {}
        for column in cols:
            q1 = cleaned[column].quantile(0.25)
            q3 = cleaned[column].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            cleaned[column] = cleaned[column].clip(lower=lower, upper=upper)
            caps[column] = {"lower": lower, "upper": upper}
        return cleaned, {"strategy": "cap", "columns": caps, "rows_changed": int(mask.sum())}
    return df.copy(), {"strategy": "retain", "rows_changed": 0}


def _iqr(df: pd.DataFrame, cols: list[str]) -> tuple[pd.Series, list[dict[str, Any]]]:
    mask = pd.Series(False, index=df.index)
    per_column = []
    for column in cols:
        series = df[column]
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        column_mask = (series < lower) | (series > upper)
        mask = mask | column_mask.fillna(False)
        per_column.append(
            {
                "column": column,
                "lower_bound": lower,
                "upper_bound": upper,
                "count": int(column_mask.sum()),
            }
        )
    return mask, per_column


def _zscore(df: pd.DataFrame, cols: list[str], threshold: float) -> tuple[pd.Series, list[dict[str, Any]]]:
    mask = pd.Series(False, index=df.index)
    per_column = []
    for column in cols:
        series = df[column]
        std = series.std(ddof=0)
        if not std or np.isnan(std):
            column_mask = pd.Series(False, index=df.index)
            max_abs_z = 0
        else:
            zscores = (series - series.mean()) / std
            column_mask = zscores.abs() > threshold
            max_abs_z = zscores.abs().max()
        mask = mask | column_mask.fillna(False)
        per_column.append({"column": column, "threshold": threshold, "count": int(column_mask.sum()), "max_abs_z": max_abs_z})
    return mask, per_column


def _isolation_forest(
    df: pd.DataFrame,
    cols: list[str],
    contamination: float,
) -> tuple[pd.Series, list[dict[str, Any]]]:
    features = df[cols].replace([np.inf, -np.inf], np.nan)
    features = features.fillna(features.median(numeric_only=True)).fillna(0)
    model = IsolationForest(contamination=contamination, random_state=42, n_estimators=80)
    labels = model.fit_predict(features)
    mask = pd.Series(labels == -1, index=df.index)
    return mask, [{"column": "multivariate", "count": int(mask.sum()), "contamination": contamination}]
