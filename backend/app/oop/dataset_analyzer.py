from __future__ import annotations

from typing import Any

import pandas as pd

from app.services.ai_insights import generate_insights
from app.services.data_cleaner import analyze_quality
from app.services.statistics_engine import generate_eda
from app.utils import dataframe_preview, json_safe


class DatasetAnalyzer:
    """Encapsulates dataset summary, preview, EDA, and insight workflows."""

    def __init__(self, dataframe: pd.DataFrame, dataset_name: str = "dataset") -> None:
        self._df = dataframe.copy()
        self._dataset_name = dataset_name

    def preview(self, rows: int = 100, offset: int = 0, total_rows: int | None = None) -> dict[str, Any]:
        return dataframe_preview(self._df, rows=rows, offset=offset, total_rows=total_rows)

    def quality_report(self, total_row_count: int | None = None) -> dict[str, Any]:
        quality = analyze_quality(self._df)
        quality["sampled_rows"] = quality["row_count"]
        if total_row_count is not None:
            quality["row_count"] = int(total_row_count)
        return json_safe(quality)

    def eda_report(self) -> dict[str, Any]:
        return generate_eda(self._df)

    def insights(self) -> dict[str, Any]:
        return generate_insights(self._df, dataset_name=self._dataset_name)

    def dataframe(self) -> pd.DataFrame:
        return self._df.copy()

