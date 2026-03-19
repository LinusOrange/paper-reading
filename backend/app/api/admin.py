from fastapi import APIRouter

from backend.app.schemas import CollectorRunRequest, PromptConfig, TaskInfo

router = APIRouter(tags=["admin"])


@router.get("/tasks", response_model=list[TaskInfo])
def list_tasks() -> list[TaskInfo]:
    from datetime import datetime, timezone

    return [
        TaskInfo(
            id="task-demo-1",
            name="generate_summary",
            paper_id=1,
            state="queued",
            created_at=datetime.now(timezone.utc),
        )
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
        )
    ]


@router.patch("/config/prompts", response_model=dict)
def update_prompts(payload: PromptConfig) -> dict:
    return {"message": "prompt updated", "name": payload.name, "version": payload.version}
