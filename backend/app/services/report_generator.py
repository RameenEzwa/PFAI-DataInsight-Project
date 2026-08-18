from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
import seaborn as sns
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.config import get_settings
from app.utils import json_safe

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def generate_pdf_report(
    dataset: dict[str, Any],
    df: pd.DataFrame,
    eda: dict[str, Any],
    insights: dict[str, Any],
    report_type: str = "full",
) -> Path:
    settings = get_settings()
    output = settings.report_dir / f"{dataset['id']}-{report_type}-report.pdf"
    doc = SimpleDocTemplate(str(output), pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("DataInsight Pro Report", styles["Title"]),
        Paragraph(dataset["name"], styles["Heading2"]),
        Spacer(1, 12),
        Paragraph("Executive Summary", styles["Heading2"]),
        Paragraph(insights.get("executive_summary", "No executive summary generated."), styles["BodyText"]),
        Spacer(1, 12),
    ]
    overview = eda.get("overview", {})
    story.append(Paragraph("Dataset Overview", styles["Heading2"]))
    story.append(
        _table(
            [
                ["Rows", f"{overview.get('rows', 0):,}"],
                ["Columns", f"{overview.get('columns', 0):,}"],
                ["Missing Values", f"{overview.get('missing_values', 0):,}"],
                ["Duplicate Rows", f"{overview.get('duplicate_rows', 0):,}"],
                ["Memory Usage MB", f"{overview.get('memory_usage_mb', 0):.2f}"],
            ]
        )
    )
    story.append(Spacer(1, 12))
    story.append(Paragraph("Key Findings", styles["Heading2"]))
    for insight in insights.get("insights", [])[:8]:
        story.append(Paragraph(f"<b>{insight.get('title', 'Insight')}</b>: {insight.get('detail', '')}", styles["BodyText"]))
        story.append(Spacer(1, 6))
    chart = _correlation_image(df)
    if chart:
        story.append(PageBreak())
        story.append(Paragraph("Correlation Heatmap", styles["Heading2"]))
        story.append(Image(str(chart), width=480, height=340))
    story.append(PageBreak())
    story.append(Paragraph("Recommendations", styles["Heading2"]))
    for recommendation in insights.get("recommendations", [])[:10]:
        story.append(Paragraph(f"- {recommendation}", styles["BodyText"]))
        story.append(Spacer(1, 6))
    doc.build(story)
    return output


def generate_excel_report(
    dataset: dict[str, Any],
    df: pd.DataFrame,
    eda: dict[str, Any],
    insights: dict[str, Any],
    report_type: str = "full",
) -> Path:
    settings = get_settings()
    output = settings.report_dir / f"{dataset['id']}-{report_type}-report.xlsx"
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        pd.DataFrame([eda.get("overview", {})]).to_excel(writer, sheet_name="Overview", index=False)
        pd.DataFrame(eda.get("column_statistics", [])).to_excel(writer, sheet_name="Column Stats", index=False)
        pd.DataFrame(eda.get("strong_correlations", [])).to_excel(writer, sheet_name="Correlations", index=False)
        pd.DataFrame(insights.get("insights", [])).to_excel(writer, sheet_name="Insights", index=False)
        pd.DataFrame({"recommendations": insights.get("recommendations", [])}).to_excel(
            writer, sheet_name="Recommendations", index=False
        )
        df.head(10_000).to_excel(writer, sheet_name="Data Sample", index=False)
    return output


def generate_cleaning_report(dataset: dict[str, Any], cleaning_report: dict[str, Any]) -> Path:
    settings = get_settings()
    output = settings.report_dir / f"{dataset['id']}-cleaning-report.xlsx"
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        pd.DataFrame([cleaning_report.get("before", {})]).to_excel(writer, sheet_name="Before", index=False)
        pd.DataFrame([cleaning_report.get("after", {})]).to_excel(writer, sheet_name="After", index=False)
        pd.DataFrame(cleaning_report.get("changes", [])).to_excel(writer, sheet_name="Changes", index=False)
    return output


def generate_visualization_report(dataset: dict[str, Any], charts: list[dict[str, Any]]) -> Path:
    settings = get_settings()
    output = settings.report_dir / f"{dataset['id']}-visualization-report.xlsx"
    rows = []
    for index, chart in enumerate(charts, start=1):
        figure = chart.get("figure", {})
        rows.append(
            {
                "chart_number": index,
                "type": chart.get("type"),
                "title": figure.get("layout", {}).get("title", {}).get("text", "Chart"),
            }
        )
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        pd.DataFrame(rows).to_excel(writer, sheet_name="Charts", index=False)
    return output


def _table(rows: list[list[str]]) -> Table:
    table = Table(rows, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D1D5DB")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _correlation_image(df: pd.DataFrame) -> Path | None:
    numeric = df.select_dtypes(include=[np.number])
    if numeric.shape[1] < 2:
        return None
    settings = get_settings()
    output = settings.report_dir / "correlation-heatmap.png"
    corr = numeric.iloc[:, :12].corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(8, 5.5))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=ax)
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)
    return output

