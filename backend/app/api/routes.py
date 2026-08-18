from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from app.config import get_settings
from app.database import (
    create_dataset,
    delete_dataset,
    get_dataset,
    latest_analysis,
    list_datasets,
    recent_analyses,
    record_analysis,
    register_report,
    update_dataset,
)
from app.oop import DataCleaningPipeline, DatasetAnalyzer, VisualizationBuilder
from app.schemas import ChartRequest, CleaningRequest, OutlierRequest, TransformRequest
from app.services.data_cleaner import analyze_quality
from app.services.data_loader import (
    UnsupportedDatasetError,
    get_dataset_profile,
    read_dataset,
    read_dataset_window,
    read_sampled_dataset,
    save_dataframe,
    validate_extension,
)
from app.services.data_transformer import apply_transformations
from app.services.outlier_detector import apply_outlier_strategy, detect_outliers
from app.services.report_generator import (
    generate_cleaning_report,
    generate_excel_report,
    generate_pdf_report,
    generate_visualization_report,
)
from app.services.statistics_engine import generate_eda
from app.services.visualization_service import create_default_visualizations
from app.utils import json_safe, safe_filename


router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "DataInsight Pro API"}


@router.get("/dashboard")
def dashboard() -> dict:
    datasets = list_datasets()
    total_records = sum(int(dataset.get("row_count") or 0) for dataset in datasets)
    total_features = sum(int(dataset.get("column_count") or 0) for dataset in datasets)
    missing_values = sum(
        int(dataset.get("metadata", {}).get("missing_cells_in_sample") or 0) for dataset in datasets
    )
    health_scores = [
        int(dataset.get("metadata", {}).get("health_score"))
        for dataset in datasets
        if dataset.get("metadata", {}).get("health_score") is not None
    ]
    return json_safe(
        {
            "dataset_count": len(datasets),
            "total_records": total_records,
            "total_features": total_features,
            "missing_values": missing_values,
            "average_health_score": round(sum(health_scores) / len(health_scores), 1) if health_scores else 100,
            "datasets": datasets[:8],
            "recent_analysis_history": recent_analyses(10),
        }
    )


@router.get("/datasets")
def datasets() -> list[dict]:
    return list_datasets()


@router.post("/datasets/upload")
async def upload_dataset(file: UploadFile = File(...)) -> dict:
    settings = get_settings()
    original_name = file.filename or "dataset.csv"
    extension = Path(original_name).suffix.lower()
    try:
        validate_extension(Path(original_name))
    except UnsupportedDatasetError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    destination = settings.upload_dir / safe_filename(original_name)
    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    max_bytes = settings.max_upload_mb * 1024 * 1024
    if destination.stat().st_size > max_bytes:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_mb} MB upload limit.")

    return _register_dataset(destination, original_name, extension)


@router.post("/datasets/sample")
def import_sample_dataset() -> dict:
    settings = get_settings()
    sample = settings.sample_dataset_path
    if not sample.exists():
        raise HTTPException(status_code=404, detail=f"Sample dataset not found at {sample}.")
    return _register_dataset(sample, sample.name, sample.suffix.lower(), name="Gen Z Social Media Usage 1M")


@router.get("/datasets/{dataset_id}")
def dataset_detail(dataset_id: str) -> dict:
    dataset = _require_dataset(dataset_id)
    return dataset


@router.delete("/datasets/{dataset_id}")
def remove_dataset(dataset_id: str) -> dict[str, str]:
    dataset = get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    settings = get_settings()
    for key in ("file_path", "active_file_path"):
        path = Path(dataset[key])
        try:
            if settings.storage_dir in path.resolve().parents and path.exists():
                path.unlink()
        except OSError:
            pass
    delete_dataset(dataset_id)
    return {"status": "deleted"}


@router.get("/datasets/{dataset_id}/preview")
def preview_dataset(
    dataset_id: str,
    rows: int = Query(default=100, ge=5, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict:
    dataset = _require_dataset(dataset_id)
    df = read_dataset_window(dataset["active_file_path"], offset=offset, nrows=rows)
    analyzer = DatasetAnalyzer(df, dataset_name=dataset["name"])
    return analyzer.preview(rows=rows, offset=offset, total_rows=int(dataset["row_count"]))


@router.get("/datasets/{dataset_id}/quality")
def quality_report(dataset_id: str) -> dict:
    dataset = _require_dataset(dataset_id)
    df = read_sampled_dataset(dataset["active_file_path"])
    analyzer = DatasetAnalyzer(df, dataset_name=dataset["name"])
    quality = analyzer.quality_report(total_row_count=int(dataset["row_count"]))
    record_analysis(dataset_id, "quality", "Data quality scan", quality)
    return quality


@router.post("/datasets/{dataset_id}/clean")
def clean(dataset_id: str, request: CleaningRequest) -> dict:
    dataset = _require_dataset(dataset_id)
    df = read_dataset(dataset["active_file_path"]) if request.persist else read_sampled_dataset(dataset["active_file_path"])
    pipeline = DataCleaningPipeline(df)
    cleaned, report = pipeline.clean(mode=request.mode, actions=request.actions)
    if request.persist:
        destination = get_settings().processed_dir / f"{dataset_id}-cleaned.csv"
        save_dataframe(cleaned, destination)
        metadata = get_dataset_profile(destination)
        update_dataset(
            dataset_id,
            active_file_path=str(destination),
            row_count=metadata["row_count"],
            column_count=metadata["column_count"],
            metadata=metadata,
        )
    record_analysis(dataset_id, "cleaning", "Automated data cleaning", report)
    return report


@router.post("/datasets/{dataset_id}/outliers")
def outliers(dataset_id: str, request: OutlierRequest) -> dict:
    dataset = _require_dataset(dataset_id)
    needs_full = request.persist and request.strategy in {"remove", "cap"}
    df = read_dataset(dataset["active_file_path"]) if needs_full else read_sampled_dataset(dataset["active_file_path"])
    mask, report = detect_outliers(
        df,
        method=request.method,
        columns=request.columns,
        contamination=request.contamination,
        z_threshold=request.z_threshold,
    )
    strategy_report = {"strategy": request.strategy, "rows_changed": 0}
    if request.strategy != "retain":
        transformed, strategy_report = apply_outlier_strategy(
            df,
            mask=mask,
            method=request.method,
            columns=request.columns,
            strategy=request.strategy,
        )
        if request.persist:
            destination = get_settings().processed_dir / f"{dataset_id}-outliers-{request.strategy}.csv"
            save_dataframe(transformed, destination)
            metadata = get_dataset_profile(destination)
            update_dataset(
                dataset_id,
                active_file_path=str(destination),
                row_count=metadata["row_count"],
                column_count=metadata["column_count"],
                metadata=metadata,
            )
    payload = {"detection": report, "strategy": strategy_report}
    record_analysis(dataset_id, "outliers", f"{request.method} outlier detection", payload)
    return json_safe(payload)


@router.get("/datasets/{dataset_id}/eda")
def eda(dataset_id: str) -> dict:
    dataset = _require_dataset(dataset_id)
    df = read_sampled_dataset(dataset["active_file_path"])
    analyzer = DatasetAnalyzer(df, dataset_name=dataset["name"])
    report = analyzer.eda_report()
    record_analysis(dataset_id, "eda", "Exploratory data analysis", report)
    return report


@router.get("/datasets/{dataset_id}/visualizations")
def default_visualizations(dataset_id: str) -> dict:
    dataset = _require_dataset(dataset_id)
    settings = get_settings()
    df = read_dataset(dataset["active_file_path"], nrows=settings.visualization_sample_rows)
    builder = VisualizationBuilder(df)
    charts = builder.default_charts()
    payload = {"charts": charts}
    record_analysis(dataset_id, "visualization", "Default chart set", {"chart_count": len(charts)})
    return json_safe(payload)


@router.post("/datasets/{dataset_id}/visualizations")
def visualization(dataset_id: str, request: ChartRequest) -> dict:
    dataset = _require_dataset(dataset_id)
    settings = get_settings()
    df = read_dataset(dataset["active_file_path"], nrows=settings.visualization_sample_rows)
    builder = VisualizationBuilder(df)
    chart = builder.chart(
        chart_type=request.chart_type,
        x=request.x,
        y=request.y,
        color=request.color,
        columns=request.columns,
        title=request.title,
        filters=request.filters,
    )
    record_analysis(
        dataset_id,
        "visualization",
        f"{request.chart_type} chart",
        {"chart_type": request.chart_type, "x": request.x, "y": request.y, "color": request.color},
    )
    return json_safe(chart)


@router.post("/datasets/{dataset_id}/transform")
def transform(dataset_id: str, request: TransformRequest) -> dict:
    dataset = _require_dataset(dataset_id)
    df = read_dataset(dataset["active_file_path"]) if request.persist else read_sampled_dataset(dataset["active_file_path"])
    transformed, report = apply_transformations(df, request.operations)
    if request.persist:
        destination = get_settings().processed_dir / f"{dataset_id}-transformed.csv"
        save_dataframe(transformed, destination)
        metadata = get_dataset_profile(destination)
        update_dataset(
            dataset_id,
            active_file_path=str(destination),
            row_count=metadata["row_count"],
            column_count=metadata["column_count"],
            metadata=metadata,
        )
    record_analysis(dataset_id, "transformation", "Data transformation", report)
    return report


@router.get("/datasets/{dataset_id}/insights")
def insights(dataset_id: str) -> dict:
    dataset = _require_dataset(dataset_id)
    df = read_sampled_dataset(dataset["active_file_path"])
    analyzer = DatasetAnalyzer(df, dataset_name=dataset["name"])
    report = analyzer.insights()
    record_analysis(dataset_id, "insights", "AI analysis assistant", report)
    return report


@router.get("/datasets/{dataset_id}/reports")
def download_report(
    dataset_id: str,
    format: str = Query(default="pdf", pattern="^(pdf|xlsx)$"),
    type: str = Query(default="full", pattern="^(full|cleaning|visualization)$"),
) -> FileResponse:
    dataset = _require_dataset(dataset_id)
    df = read_sampled_dataset(dataset["active_file_path"])
    if type == "cleaning":
        last_cleaning = latest_analysis(dataset_id, "cleaning")
        payload = last_cleaning["payload"] if last_cleaning else {"before": analyze_quality(df), "after": analyze_quality(df), "changes": []}
        path = generate_cleaning_report(dataset, payload)
    elif type == "visualization":
        charts = create_default_visualizations(df)
        path = generate_visualization_report(dataset, charts)
    else:
        eda_report = generate_eda(df)
        insight_report = generate_insights(df, dataset_name=dataset["name"])
        path = generate_pdf_report(dataset, df, eda_report, insight_report, report_type=type) if format == "pdf" else generate_excel_report(dataset, df, eda_report, insight_report, report_type=type)

    register_report(dataset_id, f"{type}-{format}", path)
    media_type = "application/pdf" if path.suffix == ".pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return FileResponse(path, media_type=media_type, filename=path.name)


@router.get("/datasets/{dataset_id}/reports/cleaned-csv")
def download_cleaned_csv(dataset_id: str) -> FileResponse:
    dataset = _require_dataset(dataset_id)
    active_path = Path(dataset["active_file_path"])
    settings = get_settings()
    if active_path.suffix.lower() == ".csv":
        path = active_path
    else:
        df = read_dataset(active_path)
        path = settings.report_dir / f"{dataset_id}-cleaned-data.csv"
        save_dataframe(df, path)
    register_report(dataset_id, "cleaned-csv", path)
    filename = f"{dataset['name'].replace(' ', '-').lower()}-cleaned-data.csv"
    return FileResponse(path, media_type="text/csv", filename=filename)


def _register_dataset(path: Path, original_name: str, extension: str, name: str | None = None) -> dict:
    try:
        metadata = get_dataset_profile(path)
    except UnsupportedDatasetError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=f"Could not parse dataset: {exc}") from exc

    dataset_id = uuid4().hex
    dataset = create_dataset(
        {
            "id": dataset_id,
            "name": name or Path(original_name).stem.replace("_", " ").replace("-", " ").title(),
            "original_filename": original_name,
            "file_path": str(path),
            "active_file_path": str(path),
            "file_type": extension.lstrip("."),
            "row_count": metadata["row_count"],
            "column_count": metadata["column_count"],
            "metadata": metadata,
        }
    )
    record_analysis(dataset_id, "dataset", "Dataset imported", {"filename": original_name, "rows": metadata["row_count"]})
    return dataset


def _require_dataset(dataset_id: str) -> dict:
    dataset = get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    if not Path(dataset["active_file_path"]).exists():
        raise HTTPException(status_code=410, detail="Dataset file is missing from storage.")
    return dataset
