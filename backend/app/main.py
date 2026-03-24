import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.admin import router as admin_router
from backend.app.api.analysis import qa_router, router as analysis_router
from backend.app.api.papers import router as papers_router
from backend.app.api.search import router as search_router
from backend.app.bootstrap import ensure_demo_data
from backend.app.config import settings
from backend.app.db import SessionLocal, engine
from backend.app.models import Base
from backend.app.services.openai_provider import build_openai_client
from backend.app.services.task_worker import TaskWorker


task_worker = TaskWorker(SessionLocal, poll_interval_seconds=settings.task_worker_poll_interval_seconds)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_demo_data(db)
    if settings.task_worker_enabled:
        await task_worker.start()
    yield
    await task_worker.stop()


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _mask_secret(secret: str | None) -> str | None:
    if not secret:
        return None
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:4]}...{secret[-4:]}"


@app.get("/healthz", tags=["system"])
def healthcheck() -> dict:
    openai_configured = bool(settings.openai_api_key)
    analysis_available = settings.openai_enabled and openai_configured
    worker_running = settings.task_worker_enabled and task_worker.is_running
    return {
        "status": "ok",
        "topic": settings.primary_topic,
        "openai_enabled": settings.openai_enabled,
        "openai_configured": openai_configured,
        "analysis_available": analysis_available,
        "task_worker_enabled": settings.task_worker_enabled,
        "task_worker_running": worker_running,
        "task_worker_poll_interval_seconds": settings.task_worker_poll_interval_seconds,
        "openai_base_url": settings.openai_base_url,
        "openai_model": settings.openai_model,
        "openai_key_hint": _mask_secret(settings.openai_api_key),
        "env_file_path": settings.env_file_path,
        "env_file_exists": settings.env_file_exists,
        "upload_dir": settings.upload_dir,
        "status_message": "OpenAI 分析已启用，内置 worker 正在轮询任务。"
        if analysis_available and worker_running
        else "当前 OpenAI 已配置，但内置 worker 尚未运行。" if analysis_available
        else "当前还没有配置 OPENAI_API_KEY。论文导入、浏览和检索仍可正常使用，但分析与问答功能会保持不可用。",
    }


@app.get("/healthz/openai", tags=["system"])
def check_openai_api() -> dict:
    if not settings.openai_api_key:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY is not configured")

    started_at = time.perf_counter()
    client = build_openai_client()

    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "Return exactly: pong"},
                {"role": "user", "content": "ping"},
            ],
            max_tokens=8,
            temperature=0,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI API check failed: {exc}") from exc

    elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
    answer = ""
    if response.choices:
        answer = (response.choices[0].message.content or "").strip()

    return {
        "status": "ok",
        "provider": "openai",
        "base_url": settings.openai_base_url,
        "model": settings.openai_model,
        "latency_ms": elapsed_ms,
        "response_preview": answer[:120],
        "usage": response.usage.model_dump() if response.usage else None,
    }


app.include_router(papers_router, prefix=settings.api_prefix)
app.include_router(search_router, prefix=settings.api_prefix)
app.include_router(analysis_router, prefix=settings.api_prefix)
app.include_router(qa_router, prefix=settings.api_prefix)
app.include_router(admin_router, prefix=settings.api_prefix)
