from __future__ import annotations

import json
import math
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np
import pandas as pd


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def safe_filename(filename: str) -> str:
    stem = Path(filename).stem or "dataset"
    suffix = Path(filename).suffix.lower()
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", stem).strip("-")[:80] or "dataset"
    return f"{cleaned}-{uuid4().hex[:10]}{suffix}"


def dataframe_preview(df: pd.DataFrame, rows: int = 100, offset: int = 0, total_rows: int | None = None) -> dict[str, Any]:
    preview = df.head(rows).copy()
    total = int(total_rows if total_rows is not None else len(df))
    return {
        "columns": [str(col) for col in preview.columns],
        "rows": json_safe(preview.replace({np.nan: None}).to_dict(orient="records")),
        "total_preview_rows": min(rows, len(df)),
        "offset": int(offset),
        "limit": int(rows),
        "total_rows": total,
        "has_previous": int(offset) > 0,
        "has_next": int(offset) + len(preview) < total,
    }


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return json_safe(value.tolist())
    if isinstance(value, (pd.Index, pd.Series)):
        return json_safe(value.tolist())
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if isinstance(value, pd.Timedelta):
        return str(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        number = float(value)
        return None if not math.isfinite(number) else number
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, float):
        return None if not math.isfinite(value) else value
    if not isinstance(value, (list, dict, tuple, set)):
        try:
            if pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass
    return value


def dumps_json(value: Any) -> str:
    return json.dumps(json_safe(value), ensure_ascii=True)


def loads_json(value: str | None, default: Any = None) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default
