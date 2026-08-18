from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, StandardScaler

from app.schemas import TransformOperation
from app.utils import json_safe


def apply_transformations(
    df: pd.DataFrame,
    operations: list[TransformOperation],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    transformed = df.copy()
    applied = []
    for operation in operations:
        if operation.type in {"normalize", "scale_minmax"}:
            transformed, detail = _scale(transformed, operation.columns, MinMaxScaler(), "normalize")
        elif operation.type == "standardize":
            transformed, detail = _scale(transformed, operation.columns, StandardScaler(), "standardize")
        elif operation.type == "encode":
            transformed, detail = _encode(transformed, operation.columns)
        elif operation.type == "merge_columns":
            transformed, detail = _merge_columns(transformed, operation)
        elif operation.type == "split_column":
            transformed, detail = _split_column(transformed, operation)
        elif operation.type == "date_parts":
            transformed, detail = _date_parts(transformed, operation.columns)
        elif operation.type == "calculated_column":
            transformed, detail = _calculated_column(transformed, operation)
        else:
            detail = {"type": operation.type, "status": "skipped"}
        applied.append(detail)
    report = {
        "operations": applied,
        "rows": int(len(transformed)),
        "columns": int(transformed.shape[1]),
        "new_columns": [str(col) for col in transformed.columns if col not in df.columns],
    }
    return transformed, json_safe(report)


def _scale(df: pd.DataFrame, columns: list[str], scaler: Any, prefix: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    cols = [col for col in columns if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    if not cols:
        return df, {"type": prefix, "status": "skipped", "reason": "No numeric columns selected."}
    result = df.copy()
    scaled = scaler.fit_transform(result[cols].replace([np.inf, -np.inf], np.nan).fillna(0))
    for index, column in enumerate(cols):
        result[f"{column}_{prefix}"] = scaled[:, index]
    return result, {"type": prefix, "columns": cols, "created": [f"{col}_{prefix}" for col in cols]}


def _encode(df: pd.DataFrame, columns: list[str]) -> tuple[pd.DataFrame, dict[str, Any]]:
    result = df.copy()
    created = []
    mappings = {}
    for column in columns:
        if column not in result.columns:
            continue
        encoder = LabelEncoder()
        values = result[column].astype(str).fillna("Unknown")
        encoded = encoder.fit_transform(values)
        target = f"{column}_encoded"
        result[target] = encoded
        created.append(target)
        mappings[column] = {label: int(code) for code, label in enumerate(encoder.classes_)}
    return result, {"type": "encode", "columns": columns, "created": created, "mappings": mappings}


def _merge_columns(df: pd.DataFrame, operation: TransformOperation) -> tuple[pd.DataFrame, dict[str, Any]]:
    cols = [col for col in operation.columns if col in df.columns]
    if len(cols) < 2:
        return df, {"type": "merge_columns", "status": "skipped", "reason": "Select at least two columns."}
    result = df.copy()
    target = operation.target_column or "_".join(cols)[:80]
    result[target] = result[cols].astype(str).agg(operation.separator.join, axis=1)
    return result, {"type": "merge_columns", "columns": cols, "created": target}


def _split_column(df: pd.DataFrame, operation: TransformOperation) -> tuple[pd.DataFrame, dict[str, Any]]:
    if not operation.columns or operation.columns[0] not in df.columns:
        return df, {"type": "split_column", "status": "skipped", "reason": "Column not found."}
    result = df.copy()
    column = operation.columns[0]
    parts = result[column].astype(str).str.split(operation.separator, expand=True, n=4)
    created = []
    for index in range(parts.shape[1]):
        target = f"{column}_part_{index + 1}"
        result[target] = parts[index]
        created.append(target)
    return result, {"type": "split_column", "column": column, "created": created}


def _date_parts(df: pd.DataFrame, columns: list[str]) -> tuple[pd.DataFrame, dict[str, Any]]:
    result = df.copy()
    created = []
    for column in columns:
        if column not in result.columns:
            continue
        dates = pd.to_datetime(result[column], errors="coerce")
        if dates.notna().mean() < 0.5:
            continue
        for part, values in {
            "year": dates.dt.year,
            "month": dates.dt.month,
            "day": dates.dt.day,
            "weekday": dates.dt.dayofweek,
        }.items():
            target = f"{column}_{part}"
            result[target] = values
            created.append(target)
    return result, {"type": "date_parts", "columns": columns, "created": created}


def _calculated_column(df: pd.DataFrame, operation: TransformOperation) -> tuple[pd.DataFrame, dict[str, Any]]:
    if not operation.formula or not operation.target_column:
        return df, {"type": "calculated_column", "status": "skipped", "reason": "Formula and target column are required."}
    result = df.copy()
    safe_locals = {col: result[col] for col in result.columns if pd.api.types.is_numeric_dtype(result[col])}
    try:
        result[operation.target_column] = pd.eval(operation.formula, local_dict=safe_locals, engine="python")
    except Exception as exc:  # noqa: BLE001
        return df, {"type": "calculated_column", "status": "failed", "error": str(exc)}
    return result, {"type": "calculated_column", "created": operation.target_column, "formula": operation.formula}

