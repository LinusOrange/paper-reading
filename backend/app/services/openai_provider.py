from openai import OpenAI

from backend.app.config import settings


def build_openai_client() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)


def get_openai_runtime_config() -> dict:
    return {
        "base_url": settings.openai_base_url,
        "model": settings.openai_model,
        "configured": bool(settings.openai_api_key),
    }
