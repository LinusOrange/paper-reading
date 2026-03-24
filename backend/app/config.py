import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field


ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE_PATH = ROOT_DIR / ".env"
load_dotenv(ENV_FILE_PATH, override=False)


class Settings(BaseModel):
    app_name: str = Field(default="SAR Literature Demo API")
    app_version: str = Field(default="0.1.0")
    api_prefix: str = Field(default="/api")
    primary_topic: str = Field(default="airborne high-resolution SAR imaging")
    openai_enabled: bool = Field(default=True)
    database_url: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://sar_demo:sar_demo@postgres:5432/sar_demo",
        )
    )
    openai_api_key: str | None = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    openai_base_url: str = Field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://us.novaiapi.com/v1"))
    openai_model: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL", "[次]gemini-3-pro-preview"))
    openai_forward_pdf_source: bool = Field(default_factory=lambda: os.getenv("OPENAI_FORWARD_PDF_SOURCE", "true").lower() in {"1", "true", "yes", "on"})
    upload_dir: str = Field(default_factory=lambda: os.getenv("UPLOAD_DIR", "/app/data/uploads"))
    task_worker_enabled: bool = Field(default_factory=lambda: os.getenv("TASK_WORKER_ENABLED", "true").lower() in {"1", "true", "yes", "on"})
    task_worker_poll_interval_seconds: float = Field(default_factory=lambda: float(os.getenv("TASK_WORKER_POLL_INTERVAL_SECONDS", "3")))
    env_file_path: str = Field(default=str(ENV_FILE_PATH))
    env_file_exists: bool = Field(default=ENV_FILE_PATH.exists())


settings = Settings()
