from __future__ import annotations

from typing import Any

import pandas as pd

from app.services.visualization_service import create_chart, create_default_visualizations


class VisualizationBuilder:
    """Encapsulates chart generation for a dataframe."""

    def __init__(self, dataframe: pd.DataFrame) -> None:
        self._df = dataframe.copy()

    def default_charts(self) -> list[dict[str, Any]]:
        return create_default_visualizations(self._df)

    def chart(
        self,
        chart_type: str,
        x: str | None = None,
        y: str | None = None,
        color: str | None = None,
        columns: list[str] | None = None,
        title: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return create_chart(
            self._df,
            chart_type=chart_type,
            x=x,
            y=y,
            color=color,
            columns=columns,
            title=title,
            filters=filters,
        )

    def dataframe(self) -> pd.DataFrame:
        return self._df.copy()

