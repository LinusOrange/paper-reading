import os

from pydantic import BaseModel, Field


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
    openai_base_url: str = Field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://once.novai.su/v1"))
    openai_model: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-5.4"))
    upload_dir: str = Field(default_factory=lambda: os.getenv("UPLOAD_DIR", "/app/data/uploads"))


settings = Settings()
