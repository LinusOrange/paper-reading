from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload, sessionmaker

from backend.app.config import settings
from backend.app.models import Paper, PaperAnalysis, PaperTag, ProcessingTask
from backend.app.services.pdf_parser import extract_pdf_metadata




class TaskWorker:
    def __init__(self, session_factory: sessionmaker, poll_interval_seconds: float = 3.0):
        self._session_factory = session_factory
        self._poll_interval_seconds = poll_interval_seconds
        self._stop_event = asyncio.Event()
        self._runner: asyncio.Task | None = None
        self._is_running = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    async def start(self) -> None:
        if self._runner:
            return
        self._stop_event.clear()
        self._runner = asyncio.create_task(self._run_loop(), name="sar-task-worker")

    async def stop(self) -> None:
        if not self._runner:
            return
        self._stop_event.set()
        await self._runner
        self._runner = None

    async def _run_loop(self) -> None:
        self._is_running = True
        try:
            while not self._stop_event.is_set():
                processed = self._process_next_task()
                if processed:
                    await asyncio.sleep(0)
                    continue
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=self._poll_interval_seconds)
                except TimeoutError:
                    continue
        finally:
            self._is_running = False

    def _process_next_task(self) -> bool:
        with self._session_factory() as db:
            task = db.scalar(
                select(ProcessingTask)
                .options(selectinload(ProcessingTask.paper))
                .where(ProcessingTask.state == "queued")
                .order_by(ProcessingTask.created_at.asc())
                .limit(1)
            )
            if not task:
                return False

            task.state = "running"
            task.error_message = None
            db.commit()

            try:
                self._execute_task(db, task.id)
            except Exception as exc:  # pragma: no cover - best effort demo worker
                failed_task = db.get(ProcessingTask, task.id)
                if failed_task:
                    failed_task.state = "failed"
                    failed_task.error_message = str(exc)[:1000]
                    db.commit()
            return True

    def _execute_task(self, db: Session, task_id: int) -> None:
        task = db.scalar(
            select(ProcessingTask)
            .options(selectinload(ProcessingTask.paper).selectinload(Paper.analysis), selectinload(ProcessingTask.paper).selectinload(Paper.tags))
            .where(ProcessingTask.id == task_id)
        )
        if not task or not task.paper:
            raise RuntimeError("task paper not found")

        paper = task.paper
        analysis = _ensure_analysis(db, paper)

        if task.task_name == "extract_text":
            paper.full_text = _extract_text_placeholder(paper)
            if paper.status == "metadata_ready":
                paper.status = "parsed"
        elif task.task_name == "generate_summary":
            analysis.summary_json = _build_summary(paper)
            analysis.analysis_model = settings.openai_model if settings.openai_api_key else "demo-fallback"
            analysis.prompt_version = "worker-v1"
            paper.status = "analyzed"
        elif task.task_name == "extract_entities":
            analysis.entities_json = _build_entities(paper)
            if paper.status == "metadata_ready":
                paper.status = "parsed"
        elif task.task_name == "recommend_tags":
            _ensure_recommended_tags(db, paper)
        elif task.task_name in {"build_embeddings", "fetch_metadata", "deduplicate"}:
            paper.status = paper.status or "metadata_ready"
        else:
            raise RuntimeError(f"unsupported task: {task.task_name}")

        task.state = "completed"
        task.error_message = None
        db.commit()


def _ensure_analysis(db: Session, paper: Paper) -> PaperAnalysis:
    if paper.analysis:
        return paper.analysis
    analysis = PaperAnalysis(
        paper_id=paper.id,
        summary_json={},
        entities_json={},
        qa_cache=[],
    )
    db.add(analysis)
    db.flush()
    paper.analysis = analysis
    return analysis


def _extract_text_placeholder(paper: Paper) -> str:
    if paper.full_text:
        return paper.full_text

    if paper.pdf_object_key:
        pdf_path = Path(paper.pdf_object_key)
        if pdf_path.exists():
            try:
                metadata = extract_pdf_metadata(str(pdf_path), paper.title)
                title = metadata.get("title") or paper.title
                venue = metadata.get("venue") or paper.venue or "unknown venue"
                year = metadata.get("year") or paper.year or "unknown year"
                return f"{title}\n\nThis paper was imported from PDF and indexed for {venue} ({year})."
            except Exception:
                pass

    abstract = paper.abstract or "No abstract was provided during import."
    return f"{paper.title}\n\n{abstract}"


def _build_summary(paper: Paper) -> dict:
    tag_names = [tag.tag_name for tag in paper.tags]
    scenario_parts = ["airborne SAR", "high-resolution"]
    if "large-squint" in tag_names or paper.is_large_squint:
        scenario_parts.append("large-squint")
    if "high-speed" in tag_names or paper.is_high_speed:
        scenario_parts.append("high-speed")

    problem = paper.abstract or "Imported paper awaiting deeper OpenAI reading."
    method = "Demo worker generated a structured summary from the imported metadata and currently available text."
    contributions = [
        "Created a structured paper summary automatically from the queued worker.",
        "Prepared the paper for downstream QA and task visualization.",
    ]
    limitations = ["This built-in worker uses deterministic demo logic; it is not yet a full asynchronous OpenAI pipeline."]
    return {
        "problem": problem,
        "method": method,
        "scenario": " / ".join(scenario_parts),
        "contributions": contributions,
        "speed_related_issue": "Covers high-speed airborne motion effects." if ("high-speed" in tag_names or paper.is_high_speed) else None,
        "squint_related_issue": "Covers large-squint imaging geometry." if ("large-squint" in tag_names or paper.is_large_squint) else None,
        "datasets_or_simulation": [paper.venue] if paper.venue else [],
        "metrics": ["summary-ready", "task-completed"],
        "limitations": limitations,
    }


def _build_entities(paper: Paper) -> dict:
    text = f"{paper.title} {paper.abstract or ''}".lower()
    methods = []
    if "motion" in text:
        methods.append("motion-compensation")
    if "squint" in text:
        methods.append("large-squint-imaging")
    if "speed" in text:
        methods.append("high-speed-imaging")
    if not methods:
        methods.append("metadata-only-demo")
    return {
        "methods": methods,
        "keywords": [tag.tag_name for tag in paper.tags],
    }


def _ensure_recommended_tags(db: Session, paper: Paper) -> None:
    existing = {tag.tag_name for tag in paper.tags}
    inferred = {"airborne-sar", "high-resolution"}
    text = f"{paper.title} {paper.abstract or ''}".lower()
    if "squint" in text:
        inferred.add("large-squint")
    if "speed" in text:
        inferred.add("high-speed")

    for tag_name in sorted(inferred - existing):
        db.add(PaperTag(paper_id=paper.id, tag_name=tag_name, tag_category="topic", source="worker"))
