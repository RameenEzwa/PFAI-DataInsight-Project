from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.utils import json_safe


NULL_TOKENS = {"", "nan", "none", "null", "nil", "na", "n/a", "missing", "-", "--"}


def analyze_quality(df: pd.DataFrame) -> dict[str, Any]:
    missing_by_column = df.isna().sum().sort_values(ascending=False)
    duplicate_rows = int(df.duplicated().sum())
    inconsistent_formats = _detect_inconsistent_formats(df)
    type_mismatches = _detect_type_mismatches(df)
    invalid_entries = _detect_invalid_entries(df)
    suggestions = build_cleaning_suggestions(
        df,
        duplicate_rows=duplicate_rows,
        inconsistent_formats=inconsistent_formats,
        type_mismatches=type_mismatches,
        invalid_entries=invalid_entries,
    )
    return json_safe(
        {
            "row_count": int(len(df)),
            "column_count": int(df.shape[1]),
            "missing_total": int(missing_by_column.sum()),
            "missing_by_column": missing_by_column[missing_by_column > 0].to_dict(),
            "duplicate_rows": duplicate_rows,
            "inconsistent_formats": inconsistent_formats,
            "type_mismatches": type_mismatches,
            "invalid_entries": invalid_entries,
            "suggestions": suggestions,
        }
    )


def build_cleaning_suggestions(
    df: pd.DataFrame,
    duplicate_rows: int | None = None,
    inconsistent_formats: list[dict[str, Any]] | None = None,
    type_mismatches: list[dict[str, Any]] | None = None,
    invalid_entries: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    duplicate_rows = int(df.duplicated().sum()) if duplicate_rows is None else duplicate_rows
    inconsistent_formats = inconsistent_formats or _detect_inconsistent_formats(df)
    type_mismatches = type_mismatches or _detect_type_mismatches(df)
    invalid_entries = invalid_entries or _detect_invalid_entries(df)
    suggestions = []
    missing_columns = df.columns[df.isna().any()].tolist()
    for column in missing_columns:
        series = df[column]
        method = "median" if pd.api.types.is_numeric_dtype(series) else "mode"
        suggestions.append(
            {
                "id": f"missing-{column}",
                "severity": "high" if series.isna().mean() > 0.1 else "medium",
                "column": str(column),
                "issue": "missing_values",
                "recommendation": f"Fill missing values in {column} with {method}.",
                "action": {"handle_missing": {"columns": [str(column)], "strategy": method}},
            }
        )
    if duplicate_rows:
        suggestions.append(
            {
                "id": "duplicate-rows",
                "severity": "medium",
                "issue": "duplicate_records",
                "recommendation": f"Remove {duplicate_rows} duplicate rows.",
                "action": {"drop_duplicates": True},
            }
        )
    for item in invalid_entries:
        if item["issue"] == "blank_or_null_tokens":
            suggestions.append(
                {
                    "id": f"null-token-{item['column']}",
                    "severity": "medium",
                    "column": item["column"],
                    "issue": "null_like_tokens",
                    "recommendation": f"Convert null-like tokens in {item['column']} to missing values, then fill or remove them.",
                    "action": {"standardize_nulls": True},
                }
            )
    for item in inconsistent_formats:
        suggestions.append(
            {
                "id": f"format-{item['column']}",
                "severity": "medium",
                "column": item["column"],
                "issue": "inconsistent_formats",
                "recommendation": f"Trim whitespace and normalize casing in {item['column']}.",
                "action": {"trim_strings": True, "normalize_categories": [item["column"]]},
            }
        )
    for item in type_mismatches:
        suggestions.append(
            {
                "id": f"type-{item['column']}",
                "severity": "medium",
                "column": item["column"],
                "issue": "data_type_mismatch",
                "recommendation": f"Convert {item['column']} to {item['suggested_type']}.",
                "action": {"convert_types": {item["column"]: item["suggested_type"]}},
            }
        )
    return suggestions


def clean_dataset(df: pd.DataFrame, mode: str = "auto", actions: dict[str, Any] | None = None) -> tuple[pd.DataFrame, dict[str, Any]]:
    actions = actions or {}
    before = analyze_quality(df)
    cleaned = df.copy()
    changes: list[dict[str, Any]] = []

    if mode == "auto":
        actions = {
            "standardize_nulls": True,
            "trim_strings": True,
            "drop_duplicates": True,
            "handle_missing": {"strategy": "smart"},
            "convert_types": "infer",
        } | actions

    if actions.get("standardize_nulls"):
        cleaned, null_changes = _standardize_null_tokens(cleaned)
        changes.extend(null_changes)

    if actions.get("trim_strings"):
        object_cols = cleaned.select_dtypes(include=["object", "string"]).columns
        for column in object_cols:
            cleaned[column] = cleaned[column].apply(lambda v: v.strip() if isinstance(v, str) else v)
        changes.append({"type": "trim_strings", "columns": [str(c) for c in object_cols]})

    normalize_columns = actions.get("normalize_categories", [])
    for column in normalize_columns:
        if column in cleaned.columns:
            cleaned[column] = cleaned[column].apply(_normalize_label)
    if normalize_columns:
        changes.append({"type": "normalize_categories", "columns": normalize_columns})

    if actions.get("drop_duplicates"):
        before_count = len(cleaned)
        cleaned = cleaned.drop_duplicates()
        changes.append({"type": "drop_duplicates", "rows_removed": int(before_count - len(cleaned))})

    missing_action = actions.get("handle_missing")
    if missing_action:
        cleaned, missing_changes = _handle_missing(cleaned, missing_action)
        changes.extend(missing_changes)

    convert_action = actions.get("convert_types")
    if convert_action:
        cleaned, convert_changes = _convert_types(cleaned, convert_action)
        changes.extend(convert_changes)

    after = analyze_quality(cleaned)
    report = {
        "before": before,
        "after": after,
        "changes": changes,
        "row_delta": int(after["row_count"] - before["row_count"]),
        "missing_delta": int(after["missing_total"] - before["missing_total"]),
        "duplicate_delta": int(after["duplicate_rows"] - before["duplicate_rows"]),
    }
    return cleaned, json_safe(report)


def _handle_missing(df: pd.DataFrame, action: dict[str, Any] | str) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    cleaned = df.copy()
    changes = []
    if isinstance(action, str):
        action = {"strategy": action}
    strategy = action.get("strategy", "smart")
    columns = action.get("columns") or cleaned.columns.tolist()
    fill_value = action.get("value")
    for column in columns:
        if column not in cleaned.columns or not cleaned[column].isna().any():
            continue
        series = cleaned[column]
        column_strategy = strategy
        if strategy == "smart":
            column_strategy = "median" if pd.api.types.is_numeric_dtype(series) else "mode"
        missing_before = int(series.isna().sum())
        if column_strategy == "drop_rows":
            cleaned = cleaned[cleaned[column].notna()]
        elif column_strategy == "mean" and pd.api.types.is_numeric_dtype(series):
            cleaned[column] = series.fillna(series.mean())
        elif column_strategy == "median" and pd.api.types.is_numeric_dtype(series):
            cleaned[column] = series.fillna(series.median())
        elif column_strategy in {"mean", "median"}:
            column_strategy = "mode"
            mode = series.mode(dropna=True)
            fill = mode.iloc[0] if not mode.empty else "Unknown"
            cleaned[column] = series.fillna(fill)
        elif column_strategy in {"mode", "smart"}:
            mode = series.mode(dropna=True)
            fill = mode.iloc[0] if not mode.empty else "Unknown"
            cleaned[column] = series.fillna(fill)
        elif column_strategy == "zero":
            cleaned[column] = series.fillna(0)
        elif column_strategy == "constant":
            cleaned[column] = series.fillna("" if fill_value is None else fill_value)
        changes.append(
            {
                "type": "handle_missing",
                "column": str(column),
                "strategy": column_strategy,
                "values_changed": missing_before,
            }
        )
    return cleaned, changes


def _standardize_null_tokens(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    cleaned = df.copy()
    changes = []
    for column in cleaned.select_dtypes(include=["object", "string"]).columns:
        series = cleaned[column]
        mask = series.map(lambda value: isinstance(value, str) and value.strip().lower() in NULL_TOKENS)
        count = int(mask.sum())
        if count:
            cleaned.loc[mask, column] = np.nan
            changes.append({"type": "standardize_nulls", "column": str(column), "values_changed": count})
    return cleaned, changes


def _convert_types(df: pd.DataFrame, action: dict[str, str] | str) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    cleaned = df.copy()
    changes = []
    if action == "infer":
        conversions = {item["column"]: item["suggested_type"] for item in _detect_type_mismatches(cleaned)}
    else:
        conversions = action
    for column, target_type in conversions.items():
        if column not in cleaned.columns:
            continue
        original_dtype = str(cleaned[column].dtype)
        try:
            if target_type == "numeric":
                cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
            elif target_type == "datetime":
                cleaned[column] = pd.to_datetime(cleaned[column], errors="coerce")
            elif target_type == "category":
                cleaned[column] = cleaned[column].astype("category")
            elif target_type == "string":
                cleaned[column] = cleaned[column].astype("string")
            else:
                continue
            changes.append(
                {
                    "type": "convert_type",
                    "column": str(column),
                    "from": original_dtype,
                    "to": str(cleaned[column].dtype),
                }
            )
        except (TypeError, ValueError):
            continue
    return cleaned, changes


def _detect_inconsistent_formats(df: pd.DataFrame) -> list[dict[str, Any]]:
    issues = []
    for column in df.select_dtypes(include=["object", "string"]).columns:
        series = df[column].dropna().astype(str)
        if series.empty:
            continue
        stripped = series.str.strip()
        whitespace_count = int((series != stripped).sum())
        lowered_unique = stripped.str.lower().nunique()
        original_unique = stripped.nunique()
        if whitespace_count or lowered_unique < original_unique:
            issues.append(
                {
                    "column": str(column),
                    "whitespace_count": whitespace_count,
                    "case_variant_count": int(original_unique - lowered_unique),
                }
            )
    return issues


def _detect_type_mismatches(df: pd.DataFrame) -> list[dict[str, Any]]:
    issues = []
    for column in df.select_dtypes(include=["object", "string"]).columns:
        series = df[column].dropna().astype(str)
        if len(series) < 10:
            continue
        numeric_parse = pd.to_numeric(series, errors="coerce").notna().mean()
        date_parse = pd.to_datetime(series.head(5_000), errors="coerce", format="mixed").notna().mean()
        if numeric_parse >= 0.9:
            issues.append({"column": str(column), "suggested_type": "numeric", "parse_success": float(numeric_parse)})
        elif date_parse >= 0.85:
            issues.append({"column": str(column), "suggested_type": "datetime", "parse_success": float(date_parse)})
    return issues


def _detect_invalid_entries(df: pd.DataFrame) -> list[dict[str, Any]]:
    issues = []
    for column in df.columns:
        series = df[column]
        if pd.api.types.is_numeric_dtype(series):
            infinite = int(np.isinf(series.to_numpy(dtype=float, copy=False)).sum())
            if infinite:
                issues.append({"column": str(column), "issue": "infinite_values", "count": infinite})
        if series.dtype == "object":
            blank = int(series.astype(str).str.strip().isin(["", "nan", "None", "NULL", "null"]).sum())
            if blank:
                issues.append({"column": str(column), "issue": "blank_or_null_tokens", "count": blank})
    return issues


def _normalize_label(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    return " ".join(value.strip().split()).title()
