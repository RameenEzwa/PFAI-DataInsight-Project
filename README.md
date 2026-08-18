# DataInsight Pro

DataInsight Pro is a full-stack analytics application for uploading datasets, profiling quality, cleaning records, detecting outliers, generating EDA, building Plotly charts, transforming columns, producing reports, and surfacing AI-style insights with Pandas.

## Stack

- Frontend: Vite React, JavaScript, Tailwind CSS, React Query, Zustand, Plotly
- Backend: Python FastAPI, Pandas, NumPy, Scikit-learn
- Visualization: Plotly, Matplotlib, Seaborn
- Reports: PDF and Excel exports
- Database: SQLite metadata and analysis history

## Folder Structure

```text
backend/
  app/
    api/routes.py
    services/
      data_loader.py
      data_cleaner.py
      outlier_detector.py
      statistics_engine.py
      visualization_service.py
      report_generator.py
      ai_insights.py
      data_transformer.py
    config.py
    database.py
    main.py
frontend/
  src/
    api/client.js
    components/
    store/useAppStore.js
docs/
  API.md
  DATABASE_SCHEMA.sql
genz_social_media_usage_1M.csv
docker-compose.yml
```

## Local Installation

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs`

### Frontend

Use `npm.cmd` on Windows PowerShell if script execution blocks `npm`.

```bash
cd frontend
copy .env.example .env
npm.cmd install
npm.cmd run dev
```

App URL: `http://localhost:5173`

## Test With The Included Dataset

1. Start the backend and frontend.
2. Open `http://localhost:5173`.
3. Upload `genz_social_media_usage_1M.csv` from the project root.
4. Use Dashboard, Clean, Outliers, EDA, Visuals, Transform, Insights, and Reports.

The backend samples large files for heavy analysis and visualizations while preserving full-file operations for saved cleaning, outlier strategies, and transformations.

## Environment Variables

Backend variables are shown in `backend/.env.example`.
Frontend variables are shown in `frontend/.env.example`.

Important values:

- `SAMPLE_DATASET_PATH` - path to the included sample CSV.
- `DATABASE_PATH` - SQLite metadata database.
- `ANALYSIS_SAMPLE_ROWS` - row cap for EDA and insight scans.
- `VISUALIZATION_SAMPLE_ROWS` - row cap for Plotly charts.
- `VITE_API_URL` - frontend API base URL.

## Docker

```bash
copy backend\.env.example backend\.env
docker compose up --build
```

Frontend: `http://localhost:5173`
Backend: `http://localhost:8000`

## Production Deployment

1. Build and publish the backend image from `backend/Dockerfile`.
2. Build and publish the frontend image from `frontend/Dockerfile` with `VITE_API_URL` pointing to the production API.
3. Mount persistent storage for `backend/storage`.
4. Set CORS origins to the deployed frontend domain.
5. Put the FastAPI service behind HTTPS and a reverse proxy/load balancer.
6. Run database backups for `datainsight.db` and storage backups for uploaded/processed datasets.

## API And Schema

- API reference: `docs/API.md`
- SQLite schema: `docs/DATABASE_SCHEMA.sql`
