from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class CleaningRequest(BaseModel):
    mode: Literal["auto", "manual"] = "auto"
    actions: dict[str, Any] = Field(default_factory=dict)
    persist: bool = True


class OutlierRequest(BaseModel):
    method: Literal["iqr", "zscore"] = "iqr"
    columns: list[str] | None = None
    strategy: Literal["retain", "remove", "cap"] = "retain"
    contamination: float = Field(default=0.03, ge=0.001, le=0.5)
    z_threshold: float = Field(default=3.0, ge=1.0, le=10.0)
    persist: bool = False


class ChartRequest(BaseModel):
    chart_type: Literal[
        "bar",
        "line",
        "pie",
        "scatter",
        "histogram",
        "box",
        "heatmap",
        "correlation",
        "pair",
        "time_series",
    ] = "histogram"
    x: str | None = None
    y: str | None = None
    color: str | None = None
    columns: list[str] | None = None
    title: str | None = None
    filters: dict[str, Any] = Field(default_factory=dict)


class TransformOperation(BaseModel):
    type: Literal[
        "normalize",
        "standardize",
        "encode",
        "scale_minmax",
        "merge_columns",
        "split_column",
        "date_parts",
        "calculated_column",
    ]
    columns: list[str] = Field(default_factory=list)
    target_column: str | None = None
    separator: str = " "
    formula: str | None = None


class TransformRequest(BaseModel):
    operations: list[TransformOperation]
    persist: bool = True
