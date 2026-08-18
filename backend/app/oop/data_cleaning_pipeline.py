from __future__ import annotations

from typing import Any

import pandas as pd

from app.services.data_cleaner import clean_dataset


class DataCleaningPipeline:
    """Encapsulates cleaning state and exposes cleaning methods."""

    def __init__(self, dataframe: pd.DataFrame) -> None:
        self._df = dataframe.copy()
        self._last_report: dict[str, Any] | None = None

    def clean(self, mode: str = "auto", actions: dict[str, Any] | None = None) -> tuple[pd.DataFrame, dict[str, Any]]:
        cleaned_df, report = clean_dataset(self._df, mode=mode, actions=actions)
        self._df = cleaned_df
        self._last_report = report
        return self.dataframe(), report

    def dataframe(self) -> pd.DataFrame:
        return self._df.copy()

    def last_report(self) -> dict[str, Any] | None:
        return self._last_report

