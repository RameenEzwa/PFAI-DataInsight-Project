from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    app_name: str = "DataInsight Pro"
    api_prefix: str = "/api"
    environment: str = "development"
    database_path: Path = BACKEND_DIR / "storage" / "datainsight.db"
    storage_dir: Path = BACKEND_DIR / "storage"
    upload_dir: Path = BACKEND_DIR / "storage" / "uploads"
    processed_dir: Path = BACKEND_DIR / "storage" / "processed"
    report_dir: Path = BACKEND_DIR / "storage" / "reports"
    sample_dataset_path: Path = PROJECT_ROOT / "genz_social_media_usage_1M.csv"
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
    max_upload_mb: int = 512
    preview_rows: int = 100
    analysis_sample_rows: int = 200_000
    visualization_sample_rows: int = 5_000
    outlier_index_limit: int = 1_000
    openai_api_key: str | None = Field(default=None, repr=False)

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    for field_name in (
        "database_path",
        "storage_dir",
        "upload_dir",
        "processed_dir",
        "report_dir",
        "sample_dataset_path",
    ):
        path = getattr(settings, field_name)
        if not path.is_absolute():
            setattr(settings, field_name, PROJECT_ROOT / path)
    for directory in (
        settings.storage_dir,
        settings.upload_dir,
        settings.processed_dir,
        settings.report_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    return settings
