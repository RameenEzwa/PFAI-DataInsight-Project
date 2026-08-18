from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.services.outlier_detector import detect_outliers
from app.services.statistics_engine import generate_eda
from app.utils import json_safe


def generate_insights(df: pd.DataFrame, dataset_name: str = "dataset") -> dict[str, Any]:
    eda = generate_eda(df)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category", "string", "bool"]).columns.tolist()
    insights: list[dict[str, Any]] = []
    recommendations: list[str] = []

    overview = eda["overview"]
    if overview["missing_values"]:
        missing_pct = overview["missing_values"] / max(overview["rows"] * overview["columns"], 1)
        insights.append(
            {
                "type": "data_quality",
                "severity": "high" if missing_pct > 0.08 else "medium",
                "title": "Missing values need attention",
                "detail": f"{overview['missing_values']:,} sampled cells are missing ({missing_pct:.1%} of the analyzed grid).",
            }
        )
        recommendations.append("Prioritize imputation rules for high-impact columns before modeling or reporting.")
    else:
        insights.append(
            {
                "type": "data_quality",
                "severity": "low",
                "title": "No missing values found in the analyzed sample",
                "detail": "The sampled records are complete across the available columns.",
            }
        )

    if overview["duplicate_rows"]:
        insights.append(
            {
                "type": "data_quality",
                "severity": "medium",
                "title": "Duplicate records detected",
                "detail": f"{overview['duplicate_rows']:,} duplicate rows appear in the analyzed sample.",
            }
        )
        recommendations.append("Remove or reconcile duplicates before calculating aggregate KPIs.")

    for item in eda.get("strong_correlations", [])[:5]:
        direction = "move together" if item["correlation"] > 0 else "move in opposite directions"
        insights.append(
            {
                "type": "correlation",
                "severity": "medium",
                "title": f"{item['feature_a']} and {item['feature_b']} are strongly related",
                "detail": f"Correlation is {item['correlation']:.2f}, so these features tend to {direction}.",
            }
        )
        recommendations.append(f"Review whether {item['feature_a']} or {item['feature_b']} can act as a driver metric.")

    if numeric_cols:
        _, outlier_report = detect_outliers(df, method="iqr", columns=numeric_cols[:12])
        if outlier_report["outlier_count"]:
            insights.append(
                {
                    "type": "anomaly",
                    "severity": "medium",
                    "title": "Outliers may affect averages",
                    "detail": f"IQR detected {outlier_report['outlier_count']:,} outlier rows in the sampled numeric columns.",
                }
            )
            recommendations.append("Compare retained, capped, and removed outlier scenarios before publishing metrics.")

    if numeric_cols and categorical_cols:
        insights.extend(_segment_insights(df, numeric_cols, categorical_cols))

    trend = _trend_insight(df, numeric_cols)
    if trend:
        insights.append(trend)

    executive_summary = _build_summary(dataset_name, overview, insights)
    if not recommendations:
        recommendations = [
            "Use the correlation heatmap and segmented distributions to identify the most actionable drivers.",
            "Create a saved clean copy before exporting final visual and PDF reports.",
        ]
    return json_safe(
        {
            "executive_summary": executive_summary,
            "insights": insights[:12],
            "recommendations": list(dict.fromkeys(recommendations))[:8],
            "natural_language_explanation": _explain_dataset(dataset_name, overview, numeric_cols, categorical_cols),
        }
    )


def _segment_insights(df: pd.DataFrame, numeric_cols: list[str], categorical_cols: list[str]) -> list[dict[str, Any]]:
    results = []
    for category in categorical_cols[:4]:
        if df[category].nunique(dropna=True) < 2 or df[category].nunique(dropna=True) > 30:
            continue
        for metric in numeric_cols[:4]:
            grouped = df.groupby(category, dropna=False)[metric].mean().sort_values(ascending=False)
            if len(grouped) < 2:
                continue
            top_label, top_value = grouped.index[0], grouped.iloc[0]
            bottom_label, bottom_value = grouped.index[-1], grouped.iloc[-1]
            if pd.notna(top_value) and pd.notna(bottom_value) and top_value != bottom_value:
                lift = (top_value - bottom_value) / (abs(bottom_value) or 1)
                if abs(lift) >= 0.1:
                    results.append(
                        {
                            "type": "segment",
                            "severity": "low",
                            "title": f"{metric} varies by {category}",
                            "detail": f"{top_label} averages {top_value:.2f}, about {lift:.1%} above {bottom_label}.",
                        }
                    )
                    break
        if len(results) >= 3:
            break
    return results


def _trend_insight(df: pd.DataFrame, numeric_cols: list[str]) -> dict[str, Any] | None:
    if not numeric_cols:
        return None
    date_column = None
    for column in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[column]):
            parsed = df[column]
        elif df[column].dtype in {"object", "string", "category"}:
            parsed = pd.to_datetime(df[column], errors="coerce", format="mixed")
        else:
            continue
        if parsed.notna().mean() > 0.8 and parsed.nunique() > 4:
            date_column = column
            break
    if date_column is None:
        return None
    metric = numeric_cols[0]
    temp = df[[date_column, metric]].copy()
    temp[date_column] = pd.to_datetime(temp[date_column], errors="coerce", format="mixed")
    temp = temp.dropna().sort_values(date_column)
    if len(temp) < 10:
        return None
    first = temp[metric].head(max(5, len(temp) // 10)).mean()
    last = temp[metric].tail(max(5, len(temp) // 10)).mean()
    if not first:
        return None
    change = (last - first) / abs(first)
    return {
        "type": "trend",
        "severity": "medium" if abs(change) >= 0.1 else "low",
        "title": f"{metric} changed over time",
        "detail": f"{metric} changed by {change:.1%} from the earliest to latest {date_column} records.",
    }


def _build_summary(dataset_name: str, overview: dict[str, Any], insights: list[dict[str, Any]]) -> str:
    headline = f"{dataset_name} contains {overview['rows']:,} analyzed rows and {overview['columns']:,} features."
    if not insights:
        return headline + " The dataset is ready for deeper exploration."
    focus = insights[0]["detail"]
    return f"{headline} {focus}"


def _explain_dataset(
    dataset_name: str,
    overview: dict[str, Any],
    numeric_cols: list[str],
    categorical_cols: list[str],
) -> str:
    numeric_text = ", ".join(numeric_cols[:5]) or "no numeric measures"
    categorical_text = ", ".join(categorical_cols[:5]) or "no categorical dimensions"
    return (
        f"{dataset_name} is structured for analysis with {overview['rows']:,} records. "
        f"Numeric measures include {numeric_text}; categorical dimensions include {categorical_text}. "
        "Use cleaning, outlier review, and segmented visualizations before final reporting."
    )
