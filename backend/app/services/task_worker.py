from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.orm import selectinload, sessionmaker

from backend.app.models import Paper, ProcessingTask
from backend.app.services.analysis_pipeline import run_pipeline_task


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
                .options(selectinload(ProcessingTask.paper).selectinload(Paper.analysis), selectinload(ProcessingTask.paper).selectinload(Paper.tags))
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
                run_pipeline_task(db, task)
                task.state = "completed"
                task.error_message = None
                db.commit()
            except Exception as exc:  # pragma: no cover - demo runtime safety
                failed_task = db.get(ProcessingTask, task.id)
                if failed_task:
                    failed_task.state = "failed"
                    failed_task.error_message = str(exc)[:1000]
                    db.commit()
            return True
