# DataInsight Pro API

Base URL: `http://localhost:8000/api`

Interactive OpenAPI docs are available at `http://localhost:8000/docs`.

## Health

- `GET /health` - API status.

## Dashboard

- `GET /dashboard` - Portfolio metrics, recent datasets, and recent analysis history.

## Dataset Management

- `GET /datasets` - List datasets.
- `POST /datasets/upload` - Multipart upload field `file`; supports CSV, XLSX, JSON, JSONL, SQLite DB, and SQL export files.
- `POST /datasets/sample` - Register the included `genz_social_media_usage_1M.csv` dataset if `SAMPLE_DATASET_PATH` is configured.
- `GET /datasets/{dataset_id}` - Dataset metadata.
- `DELETE /datasets/{dataset_id}` - Delete metadata and stored uploaded/processed files.
- `GET /datasets/{dataset_id}/preview?rows=100` - Tabular preview.

## Cleaning And Quality

- `GET /datasets/{dataset_id}/quality` - Missing values, duplicates, type mismatches, invalid entries, and cleaning suggestions.
- `POST /datasets/{dataset_id}/clean`

```json
{
  "mode": "auto",
  "actions": {},
  "persist": true
}
```

## Outliers

- `POST /datasets/{dataset_id}/outliers`

```json
{
  "method": "iqr",
  "columns": ["daily_usage_hours"],
  "strategy": "retain",
  "contamination": 0.03,
  "z_threshold": 3,
  "persist": false
}
```

Methods: `iqr`, `zscore`.
Strategies: `retain`, `remove`, `cap`.

## EDA

- `GET /datasets/{dataset_id}/eda` - Overview, descriptive statistics, correlations, distributions, frequencies, skewness, and kurtosis.

## Visualizations

- `GET /datasets/{dataset_id}/visualizations` - Auto-generated Plotly chart set.
- `POST /datasets/{dataset_id}/visualizations`

```json
{
  "chart_type": "scatter",
  "x": "daily_usage_hours",
  "y": "mental_health_score",
  "color": "gender",
  "columns": null,
  "title": "Usage vs Mental Health",
  "filters": {}
}
```

Chart types: `bar`, `line`, `pie`, `scatter`, `histogram`, `box`, `heatmap`, `correlation`, `pair`, `time_series`.

## Transformations

- `POST /datasets/{dataset_id}/transform`

```json
{
  "persist": true,
  "operations": [
    {
      "type": "normalize",
      "columns": ["daily_usage_hours"],
      "target_column": null,
      "separator": " ",
      "formula": null
    }
  ]
}
```

Operations: `normalize`, `standardize`, `encode`, `scale_minmax`, `merge_columns`, `split_column`, `date_parts`, `calculated_column`.

## Insights

- `GET /datasets/{dataset_id}/insights` - Local rule-based assistant summary, anomalies, correlations, trend notes, and recommendations.

## Reports

- `GET /datasets/{dataset_id}/reports?format=pdf&type=full`
- `GET /datasets/{dataset_id}/reports?format=xlsx&type=full`
- `GET /datasets/{dataset_id}/reports?format=xlsx&type=cleaning`
- `GET /datasets/{dataset_id}/reports?format=xlsx&type=visualization`
