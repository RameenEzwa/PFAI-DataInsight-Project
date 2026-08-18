from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.utils import json_safe


def generate_eda(df: pd.DataFrame) -> dict[str, Any]:
    numeric = df.select_dtypes(include=[np.number])
    categorical = df.select_dtypes(include=["object", "category", "string", "bool"])
    overview = {
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "numeric_columns": int(numeric.shape[1]),
        "categorical_columns": int(categorical.shape[1]),
        "missing_values": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "memory_usage_mb": float(df.memory_usage(deep=True).sum() / 1_048_576),
    }
    return json_safe(
        {
            "overview": overview,
            "statistical_summary": _statistical_summary(numeric),
            "column_statistics": _column_statistics(df),
            "correlation_matrix": _correlation_matrix(numeric),
            "strong_correlations": _strong_correlations(numeric),
            "feature_distributions": _feature_distributions(numeric),
            "category_frequencies": _category_frequencies(categorical),
        }
    )


def _statistical_summary(numeric: pd.DataFrame) -> dict[str, Any]:
    if numeric.empty:
        return {}
    summary = numeric.describe().T
    summary["variance"] = numeric.var(numeric_only=True)
    summary["skewness"] = numeric.skew(numeric_only=True)
    summary["kurtosis"] = numeric.kurtosis(numeric_only=True)
    return summary.round(4).to_dict(orient="index")


def _column_statistics(df: pd.DataFrame) -> list[dict[str, Any]]:
    stats = []
    for column in df.columns:
        series = df[column]
        mode = series.mode(dropna=True)
        item = {
            "column": str(column),
            "dtype": str(series.dtype),
            "missing": int(series.isna().sum()),
            "missing_pct": float(series.isna().mean()),
            "unique": int(series.nunique(dropna=True)),
            "mode": mode.iloc[0] if not mode.empty else None,
        }
        if pd.api.types.is_numeric_dtype(series):
            item.update(
                {
                    "mean": series.mean(skipna=True),
                    "median": series.median(skipna=True),
                    "variance": series.var(skipna=True),
                    "standard_deviation": series.std(skipna=True),
                    "min": series.min(skipna=True),
                    "max": series.max(skipna=True),
                    "skewness": series.skew(skipna=True),
                    "kurtosis": series.kurtosis(skipna=True),
                }
            )
        stats.append(item)
    return stats


def _correlation_matrix(numeric: pd.DataFrame) -> dict[str, Any]:
    if numeric.shape[1] < 2:
        return {"columns": [], "values": []}
    corr = numeric.corr(numeric_only=True).round(4)
    return {"columns": [str(col) for col in corr.columns], "values": corr.values.tolist()}


def _strong_correlations(numeric: pd.DataFrame, threshold: float = 0.55) -> list[dict[str, Any]]:
    if numeric.shape[1] < 2:
        return []
    corr = numeric.corr(numeric_only=True)
    results = []
    for i, col_a in enumerate(corr.columns):
        for col_b in corr.columns[i + 1 :]:
            value = corr.loc[col_a, col_b]
            if pd.notna(value) and abs(value) >= threshold:
                results.append({"feature_a": str(col_a), "feature_b": str(col_b), "correlation": float(value)})
    return sorted(results, key=lambda item: abs(item["correlation"]), reverse=True)


def _feature_distributions(numeric: pd.DataFrame) -> list[dict[str, Any]]:
    distributions = []
    for column in numeric.columns[:30]:
        series = numeric[column].dropna()
        if series.empty:
            continue
        counts, bins = np.histogram(series, bins=min(20, max(5, int(np.sqrt(len(series))))))
        distributions.append(
            {
                "column": str(column),
                "bins": bins.tolist(),
                "counts": counts.tolist(),
                "skewness": series.skew(),
                "kurtosis": series.kurtosis(),
            }
        )
    return distributions


def _category_frequencies(categorical: pd.DataFrame) -> list[dict[str, Any]]:
    frequencies = []
    for column in categorical.columns[:40]:
        counts = categorical[column].astype(str).value_counts(dropna=False).head(15)
        frequencies.append(
            {
                "column": str(column),
                "values": [{"label": str(index), "count": int(value)} for index, value in counts.items()],
            }
        )
    return frequencies

