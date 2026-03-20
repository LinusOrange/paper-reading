from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.admin import router as admin_router
from backend.app.api.analysis import qa_router, router as analysis_router
from backend.app.api.papers import router as papers_router
from backend.app.api.search import router as search_router
from backend.app.bootstrap import ensure_demo_data
from backend.app.config import settings
from backend.app.db import SessionLocal, engine
from backend.app.models import Base


@asynccontextmanager
async def lifespan(_: FastAPI):
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_demo_data(db)
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", tags=["system"])
def healthcheck() -> dict:
    return {
        "status": "ok",
        "topic": settings.primary_topic,
        "openai_enabled": settings.openai_enabled,
        "openai_configured": bool(settings.openai_api_key),
        "openai_base_url": settings.openai_base_url,
        "openai_model": settings.openai_model,
        "upload_dir": settings.upload_dir,
    }


app.include_router(papers_router, prefix=settings.api_prefix)
app.include_router(search_router, prefix=settings.api_prefix)
app.include_router(analysis_router, prefix=settings.api_prefix)
app.include_router(qa_router, prefix=settings.api_prefix)
app.include_router(admin_router, prefix=settings.api_prefix)
