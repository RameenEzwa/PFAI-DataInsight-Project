from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.config import get_settings
from app.utils import json_safe


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json", ".jsonl", ".db", ".sqlite", ".sql"}


class UnsupportedDatasetError(ValueError):
    pass


def validate_extension(path: Path) -> str:
    extension = path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise UnsupportedDatasetError(
            f"Unsupported file type '{extension}'. Upload CSV, XLSX, JSON, JSONL, SQLite DB, or SQL export files."
        )
    return extension


def read_dataset(path: str | Path, nrows: int | None = None) -> pd.DataFrame:
    path = Path(path)
    extension = validate_extension(path)
    if extension == ".csv":
        return pd.read_csv(path, nrows=nrows, low_memory=False)
    if extension in {".xlsx", ".xls"}:
        return pd.read_excel(path, nrows=nrows)
    if extension in {".json", ".jsonl"}:
        return _read_json(path, nrows)
    if extension in {".db", ".sqlite"}:
        return _read_sqlite_database(path, nrows)
    if extension == ".sql":
        return _read_sql_export(path, nrows)
    raise UnsupportedDatasetError(f"Unsupported file type '{extension}'.")


def read_sampled_dataset(path: str | Path) -> pd.DataFrame:
    settings = get_settings()
    return read_dataset(path, nrows=settings.analysis_sample_rows)


def read_dataset_window(path: str | Path, offset: int = 0, nrows: int = 100) -> pd.DataFrame:
    path = Path(path)
    extension = validate_extension(path)
    offset = max(int(offset), 0)
    nrows = max(int(nrows), 1)
    if extension == ".csv":
        skiprows = range(1, offset + 1) if offset else None
        return pd.read_csv(path, nrows=nrows, skiprows=skiprows, low_memory=False)
    df = read_dataset(path, nrows=offset + nrows)
    return df.iloc[offset : offset + nrows].copy()


def save_dataframe(df: pd.DataFrame, destination: str | Path) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    extension = destination.suffix.lower()
    if extension == ".parquet":
        df.to_parquet(destination, index=False)
    elif extension in {".xlsx", ".xls"}:
        df.to_excel(destination, index=False)
    elif extension in {".json", ".jsonl"}:
        df.to_json(destination, orient="records", lines=extension == ".jsonl")
    else:
        df.to_csv(destination, index=False)
    return destination


def get_dataset_profile(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    sample = read_sampled_dataset(path)
    row_count = estimate_row_count(path, sample)
    columns = build_column_profile(sample, row_count)
    duplicate_count = int(sample.duplicated().sum())
    missing_total = int(sample.isna().sum().sum())
    total_cells = max(int(row_count) * max(len(sample.columns), 1), 1)
    missing_pct = float(missing_total / max(sample.shape[0] * max(sample.shape[1], 1), 1))
    health_score = calculate_health_score(missing_pct, duplicate_count, sample.shape[0])
    return json_safe(
        {
            "row_count": int(row_count),
            "column_count": int(sample.shape[1]),
            "sampled_rows": int(sample.shape[0]),
            "estimated_total_cells": int(total_cells),
            "missing_cells_in_sample": missing_total,
            "duplicate_rows_in_sample": duplicate_count,
            "health_score": health_score,
            "columns": columns,
        }
    )


def estimate_row_count(path: str | Path, sample: pd.DataFrame | None = None) -> int:
    path = Path(path)
    extension = validate_extension(path)
    if extension == ".csv":
        count = 0
        for chunk in pd.read_csv(path, chunksize=250_000, usecols=[0]):
            count += len(chunk)
        return count
    if extension in {".db", ".sqlite"}:
        table = _first_sqlite_table(path)
        with sqlite3.connect(path) as conn:
            return int(conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])
    if sample is not None:
        full = read_dataset(path)
        return int(len(full))
    return int(len(read_dataset(path)))


def build_column_profile(df: pd.DataFrame, total_rows: int | None = None) -> list[dict[str, Any]]:
    total_rows = total_rows or len(df)
    profile = []
    for column in df.columns:
        series = df[column]
        missing = int(series.isna().sum())
        unique = int(series.nunique(dropna=True))
        detected_type = detect_semantic_type(series)
        examples = series.dropna().astype(str).head(5).tolist()
        item = {
            "name": str(column),
            "pandas_dtype": str(series.dtype),
            "detected_type": detected_type,
            "missing_count": missing,
            "missing_pct": float(missing / max(len(series), 1)),
            "unique_count": unique,
            "unique_pct": float(unique / max(len(series), 1)),
            "examples": examples,
        }
        if pd.api.types.is_numeric_dtype(series):
            item.update(
                {
                    "min": series.min(skipna=True),
                    "max": series.max(skipna=True),
                    "mean": series.mean(skipna=True),
                }
            )
        profile.append(item)
    return json_safe(profile)


def detect_semantic_type(series: pd.Series) -> str:
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    non_null = series.dropna()
    if non_null.empty:
        return "empty"
    sample = non_null.astype(str).head(1_000)
    parsed = pd.to_datetime(sample, errors="coerce", utc=False, format="mixed")
    if parsed.notna().mean() >= 0.85:
        return "datetime"
    if non_null.nunique(dropna=True) <= max(50, len(non_null) * 0.05):
        return "categorical"
    return "text"


def calculate_health_score(missing_pct: float, duplicate_count: int, sample_rows: int) -> int:
    duplicate_pct = duplicate_count / max(sample_rows, 1)
    penalty = missing_pct * 45 + duplicate_pct * 35
    score = 100 - min(75, penalty * 100)
    return int(max(20, round(score)))


def _read_json(path: Path, nrows: int | None) -> pd.DataFrame:
    try:
        if path.suffix.lower() == ".jsonl":
            df = pd.read_json(path, lines=True, nrows=nrows)
        else:
            df = pd.read_json(path)
    except ValueError:
        df = pd.read_json(path, lines=True, nrows=nrows)
    if isinstance(df, pd.Series):
        df = df.to_frame()
    if nrows is not None:
        df = df.head(nrows)
    return pd.json_normalize(df.to_dict(orient="records"))


def _first_sqlite_table(path: Path) -> str:
    with sqlite3.connect(path) as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name LIMIT 1"
        ).fetchone()
    if not row:
        raise UnsupportedDatasetError("SQLite file does not contain a readable table.")
    return str(row[0])


def _read_sqlite_database(path: Path, nrows: int | None) -> pd.DataFrame:
    table = _first_sqlite_table(path)
    limit = f" LIMIT {int(nrows)}" if nrows is not None else ""
    with sqlite3.connect(path) as conn:
        return pd.read_sql_query(f'SELECT * FROM "{table}"{limit}', conn)


def _read_sql_export(path: Path, nrows: int | None) -> pd.DataFrame:
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp:
        temp_db = Path(tmp.name)
    try:
        script = path.read_text(encoding="utf-8", errors="ignore")
        with sqlite3.connect(temp_db) as conn:
            conn.executescript(script)
            conn.commit()
        return _read_sqlite_database(temp_db, nrows)
    finally:
        temp_db.unlink(missing_ok=True)
