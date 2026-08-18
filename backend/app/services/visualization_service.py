from __future__ import annotations

import base64
from io import BytesIO
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
import plotly.express as px
import seaborn as sns

from app.config import get_settings
from app.utils import json_safe

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


PLOT_TEMPLATE = "plotly_white"


def create_chart(
    df: pd.DataFrame,
    chart_type: str,
    x: str | None = None,
    y: str | None = None,
    color: str | None = None,
    columns: list[str] | None = None,
    title: str | None = None,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = _apply_filters(df, filters or {})
    data = _sample_for_visualization(data)
    numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = data.select_dtypes(include=["object", "category", "string", "bool"]).columns.tolist()
    x = x if x in data.columns else None
    y = y if y in data.columns else None
    color = color if color in data.columns else None

    if chart_type == "bar":
        x = x or (categorical_cols[0] if categorical_cols else data.columns[0])
        if y and y in numeric_cols:
            grouped = data.groupby(x, dropna=False)[y].mean().reset_index().head(30)
            fig = px.bar(grouped, x=x, y=y, title=title or f"Average {y} by {x}", template=PLOT_TEMPLATE)
        else:
            counts = data[x].astype(str).value_counts().head(30).reset_index()
            counts.columns = [x, "count"]
            fig = px.bar(counts, x=x, y="count", title=title or f"{x} frequency", template=PLOT_TEMPLATE)
    elif chart_type == "line":
        x = x or data.columns[0]
        y = y or (numeric_cols[0] if numeric_cols else data.columns[-1])
        fig = px.line(data.sort_values(by=x).head(5_000), x=x, y=y, color=color, title=title or f"{y} over {x}", template=PLOT_TEMPLATE)
    elif chart_type in {"pie"}:
        x = x or (categorical_cols[0] if categorical_cols else data.columns[0])
        counts = data[x].astype(str).value_counts().head(12).reset_index()
        counts.columns = [x, "count"]
        fig = px.pie(counts, names=x, values="count", title=title or f"{x} share", template=PLOT_TEMPLATE, hole=0.35)
    elif chart_type == "scatter":
        x = x or (numeric_cols[0] if numeric_cols else data.columns[0])
        y = y or (numeric_cols[1] if len(numeric_cols) > 1 else x)
        fig = px.scatter(data, x=x, y=y, color=color, title=title or f"{x} vs {y}", template=PLOT_TEMPLATE)
    elif chart_type == "box":
        y = y or (numeric_cols[0] if numeric_cols else data.columns[0])
        fig = px.box(data, x=x, y=y, color=color, points="outliers", title=title or f"{y} distribution", template=PLOT_TEMPLATE)
    elif chart_type == "heatmap" or chart_type == "correlation":
        selected = columns or numeric_cols[:12]
        corr = data[selected].corr(numeric_only=True)
        fig = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r", aspect="auto", title=title or "Correlation heatmap", template=PLOT_TEMPLATE)
    elif chart_type == "time_series":
        x = x or _first_datetime_candidate(data)
        y = y or (numeric_cols[0] if numeric_cols else None)
        if x:
            data = data.copy()
            data[x] = pd.to_datetime(data[x], errors="coerce", format="mixed")
            fig = px.line(data.dropna(subset=[x]).sort_values(x).head(5_000), x=x, y=y, color=color, title=title or f"{y or 'Value'} over time", template=PLOT_TEMPLATE)
        else:
            fig = px.line(data.head(5_000), y=y or numeric_cols[:3], title=title or "Time-series chart", template=PLOT_TEMPLATE)
    elif chart_type == "pair":
        return {"type": "image", "format": "png", "image_base64": create_pair_plot_image(data, columns)}
    else:
        x = x or (numeric_cols[0] if numeric_cols else data.columns[0])
        fig = px.histogram(data, x=x, color=color, nbins=35, marginal="box", title=title or f"{x} distribution", template=PLOT_TEMPLATE)

    fig.update_layout(
        margin=dict(l=32, r=20, t=52, b=36),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend_title_text="",
    )
    return {"type": "plotly", "figure": json_safe(fig.to_plotly_json())}


def create_default_visualizations(df: pd.DataFrame) -> list[dict[str, Any]]:
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category", "string", "bool"]).columns.tolist()
    charts = []
    if numeric_cols:
        charts.append(create_chart(df, "histogram", x=numeric_cols[0], title=f"{numeric_cols[0]} distribution"))
        charts.append(create_chart(df, "box", y=numeric_cols[0], x=categorical_cols[0] if categorical_cols else None))
    if categorical_cols:
        charts.append(create_chart(df, "bar", x=categorical_cols[0], title=f"{categorical_cols[0]} frequency"))
        charts.append(create_chart(df, "pie", x=categorical_cols[0], title=f"{categorical_cols[0]} share"))
    if len(numeric_cols) >= 2:
        charts.append(create_chart(df, "scatter", x=numeric_cols[0], y=numeric_cols[1]))
        charts.append(create_chart(df, "correlation", columns=numeric_cols[:10]))
    return charts


def create_pair_plot_image(df: pd.DataFrame, columns: list[str] | None = None) -> str:
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    selected = [col for col in (columns or numeric_cols[:5]) if col in numeric_cols][:5]
    if len(selected) < 2:
        selected = numeric_cols[: min(5, len(numeric_cols))]
    if len(selected) < 2:
        return ""
    sample = df[selected].dropna().sample(min(len(df[selected].dropna()), 1_000), random_state=42)
    grid = sns.pairplot(sample, diag_kind="hist", corner=True)
    buffer = BytesIO()
    grid.fig.savefig(buffer, format="png", dpi=140, bbox_inches="tight")
    plt.close(grid.fig)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _sample_for_visualization(df: pd.DataFrame) -> pd.DataFrame:
    settings = get_settings()
    if len(df) <= settings.visualization_sample_rows:
        return df
    return df.sample(settings.visualization_sample_rows, random_state=42)


def _apply_filters(df: pd.DataFrame, filters: dict[str, Any]) -> pd.DataFrame:
    data = df
    for column, value in filters.items():
        if column not in data.columns or value in (None, "", []):
            continue
        if isinstance(value, list):
            data = data[data[column].isin(value)]
        elif isinstance(value, dict):
            if "min" in value:
                data = data[data[column] >= value["min"]]
            if "max" in value:
                data = data[data[column] <= value["max"]]
        else:
            data = data[data[column].astype(str) == str(value)]
    return data


def _first_datetime_candidate(df: pd.DataFrame) -> str | None:
    for column in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[column]):
            return str(column)
        if df[column].dtype == "object":
            parsed = pd.to_datetime(df[column].dropna().astype(str).head(1_000), errors="coerce", format="mixed")
            if parsed.notna().mean() > 0.8:
                return str(column)
    return None
