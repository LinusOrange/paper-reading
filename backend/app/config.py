from pydantic import BaseModel, Field


class Settings(BaseModel):
    app_name: str = Field(default="SAR Literature Demo API")
    app_version: str = Field(default="0.1.0")
    api_prefix: str = Field(default="/api")
    primary_topic: str = Field(default="airborne high-resolution SAR imaging")
    openai_enabled: bool = Field(default=True)


settings = Settings()
