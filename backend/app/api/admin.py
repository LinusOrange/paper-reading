from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.db import get_db
from backend.app.models import ProcessingTask
from backend.app.schemas import CollectorRunRequest, PromptConfig, TaskInfo

router = APIRouter(tags=["admin"])


@router.get("/tasks", response_model=list[TaskInfo])
def list_tasks(db: Session = Depends(get_db)) -> list[TaskInfo]:
    tasks = db.scalars(
        select(ProcessingTask)
        .options(selectinload(ProcessingTask.paper))
        .order_by(ProcessingTask.updated_at.desc(), ProcessingTask.created_at.desc())
        .limit(50)
    ).all()
    return [
        TaskInfo(
            id=str(task.id),
            name=task.task_name,
            paper_id=task.paper_id,
            paper_title=task.paper.title if task.paper else None,
            state=task.state,
            provider=task.provider,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
        for task in tasks
    ]


@router.post("/collectors/run", response_model=dict)
def run_collector(payload: CollectorRunRequest) -> dict:
    return {
        "message": "collector started",
        "query_group": payload.query_group,
        "limit": payload.limit,
    }


@router.get("/config/prompts", response_model=list[PromptConfig])
def get_prompts() -> list[PromptConfig]:
    return [
        PromptConfig(
            name="sar_paper_summary_prompt",
            version="v1",
            description="Generate structured SAR paper summaries for airborne high-resolution imaging.",
            output_schema={
                "problem": "string",
                "method": "string",
                "scenario": "string",
                "contributions": "string[]",
            },
        ),
        PromptConfig(
            name="sar_qa_prompt",
            version="v1",
            description="Answer SAR topic questions using grounded paper candidates.",
            output_schema={
                "answer": "string",
                "citations": "number[]",
            },
        ),
    ]


@router.patch("/config/prompts", response_model=dict)
def update_prompts(payload: PromptConfig) -> dict:
    return {"message": "prompt updated", "name": payload.name, "version": payload.version}
