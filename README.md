# DataInsight Pro

A full-stack Python-based data analytics application for uploading datasets, analyzing data quality, cleaning records, detecting outliers, performing Exploratory Data Analysis (EDA), creating interactive visualizations, transforming data, generating reports, and producing AI-style insights.

## Overview

DataInsight Pro provides an end-to-end workflow for working with real-world datasets.

The application allows users to:

- Upload and load datasets
- Profile dataset quality
- Clean missing and inconsistent data
- Detect and handle outliers
- Perform statistical analysis and EDA
- Generate interactive Plotly visualizations
- Transform dataset columns
- Generate AI-style analytical insights
- Export analysis results to PDF and Excel reports
- Store metadata and analysis history

For large datasets, the backend uses sampling for computationally intensive EDA, insights, and visualization operations while preserving full-file operations for supported cleaning, outlier, and transformation workflows.

## Key Features

### Data Analysis
- Dataset loading and profiling
- Descriptive statistics
- Exploratory Data Analysis (EDA)
- Data quality analysis

### Data Cleaning
- Missing-value handling
- Data preprocessing
- Data transformation
- Outlier detection and handling

### Visualization
- Interactive Plotly charts
- Matplotlib visualizations
- Seaborn visualizations
- Visual exploration of dataset patterns

### Reporting
- PDF report generation
- Excel report export
- Analysis history and metadata

### Application Architecture
- React-based frontend
- FastAPI backend
- Pandas-based data processing
- REST API architecture
- SQLite metadata storage

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React, Vite, JavaScript, Tailwind CSS |
| State & Data Management | React Query, Zustand |
| Visualization | Plotly, Matplotlib, Seaborn |
| Backend | Python, FastAPI |
| Data Processing | Pandas, NumPy |
| Machine Learning | Scikit-learn |
| Reports | ReportLab, Excel |
| Database | SQLite |
| Development | Git, GitHub, Docker |

## Project Structure

```text
DataInsight-Pro/
│
├── backend/
│   └── app/
│       ├── api/
│       │   └── routes.py
│       ├── services/
│       │   ├── data_loader.py
│       │   ├── data_cleaner.py
│       │   ├── outlier_detector.py
│       │   ├── statistics_engine.py
│       │   ├── visualization_service.py
│       │   ├── report_generator.py
│       │   ├── ai_insights.py
│       │   └── data_transformer.py
│       ├── config.py
│       ├── database.py
│       └── main.py
│
├── frontend/
│   └── src/
│       ├── api/
│       ├── components/
│       └── store/
│
├── docs/
│   ├── API.md
│   └── DATABASE_SCHEMA.sql
│
├── sample_datasets/
│
├── docker-compose.yml
└── README.md

- API reference: `docs/API.md`
- SQLite schema: `docs/DATABASE_SCHEMA.sql`
