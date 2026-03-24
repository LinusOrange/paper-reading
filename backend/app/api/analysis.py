from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.api.papers import _fallback_summary, _create_processing_task
from backend.app.config import settings
from backend.app.db import get_db
from backend.app.models import Paper, PaperTag
from backend.app.schemas import AnalysisTaskRequest, LiteratureWorkflowRequest, PaperSummary, QARequest
from backend.app.services.literature_workflow import run_literature_workflow
from backend.app.services.openai_provider import get_openai_runtime_config

router = APIRouter(prefix="/analysis", tags=["analysis"])
qa_router = APIRouter(prefix="/qa", tags=["qa"])


@router.post("/{paper_id}/summary", response_model=PaperSummary)
def generate_summary(paper_id: int, db: Session = Depends(get_db)) -> PaperSummary:
    paper = db.scalar(select(Paper).options(selectinload(Paper.analysis)).where(Paper.id == paper_id))
    if not paper:
        raise HTTPException(status_code=404, detail="paper not found")
    if paper.analysis and paper.analysis.summary_json:
        return PaperSummary(**paper.analysis.summary_json)
    return _fallback_summary()


@router.post("/{paper_id}/extract", response_model=dict)
def extract_entities(paper_id: int, db: Session = Depends(get_db)) -> dict:
    paper = db.scalar(select(Paper).options(selectinload(Paper.analysis)).where(Paper.id == paper_id))
    if not paper:
        raise HTTPException(status_code=404, detail="paper not found")
    entities = paper.analysis.entities_json if paper.analysis else {}
    return {"paper_id": paper_id, "entities": entities}


@router.post("/{paper_id}/tags", response_model=dict)
def recommend_tags(paper_id: int, db: Session = Depends(get_db)) -> dict:
    paper = db.scalar(select(Paper).options(selectinload(Paper.tags)).where(Paper.id == paper_id))
    if not paper:
        raise HTTPException(status_code=404, detail="paper not found")
    return {"paper_id": paper_id, "tags": [tag.tag_name for tag in paper.tags]}


@router.post("/{paper_id}/enqueue", response_model=dict)
def enqueue_openai_analysis(paper_id: int, payload: AnalysisTaskRequest, db: Session = Depends(get_db)) -> dict:
    paper = db.scalar(select(Paper).where(Paper.id == paper_id))
    if not paper:
        raise HTTPException(status_code=404, detail="paper not found")

    runtime_config = get_openai_runtime_config()
    if payload.provider == "openai" and not runtime_config["configured"]:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY is not configured")

    for task_name in payload.task_types:
        _create_processing_task(db, paper_id, task_name, provider=payload.provider)
    db.commit()
    return {
        "message": "analysis tasks queued",
        "paper_id": paper_id,
        "provider": payload.provider,
        "task_types": payload.task_types,
        "model": settings.openai_model,
        "base_url": settings.openai_base_url,
    }


@qa_router.post("/ask", response_model=dict)
def ask_question(payload: QARequest, db: Session = Depends(get_db)) -> dict:
    stmt = select(Paper).options(selectinload(Paper.tags), selectinload(Paper.analysis)).limit(payload.top_k)
    papers = db.scalars(stmt).all()
    citations = [paper.id for paper in papers]

    snippets: list[str] = []
    for paper in papers:
        summary = paper.analysis.summary_json if paper.analysis else {}
        method = summary.get("method", "method pending") if isinstance(summary, dict) else "method pending"
        scenario = summary.get("scenario", "scenario pending") if isinstance(summary, dict) else "scenario pending"
        snippets.append(f"[{paper.id}] {paper.title} | {scenario} | {method}")

    if snippets:
        answer = "基于当前入库论文的结构化摘要，候选方法如下：\n" + "\n".join(snippets)
    else:
        answer = "当前没有可用论文，请先导入论文并完成分析流水线任务。"

    return {
        "question": payload.question,
        "answer": answer,
        "citations": citations,
        "model": settings.openai_model,
    }


@router.post("/literature-workflow", response_model=dict)
def literature_workflow(payload: LiteratureWorkflowRequest, db: Session = Depends(get_db)) -> dict:
    result = run_literature_workflow(
        user_requirement=payload.user_requirement,
        prompt_template=payload.prompt_template,
        use_web_search=payload.use_web_search,
        compact_output=payload.compact_output,
    )
    if payload.store_to_library:
        stored = _store_literature_candidates(db, result.get("papers", []))
        result["stored"] = stored
    return result


def _store_literature_candidates(db: Session, papers: list[dict]) -> dict:
    created_ids: list[int] = []
    skipped_titles: list[str] = []

    for item in papers:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        if not title:
            continue

        doi = str(item.get("doi") or "").strip() or None
        year = item.get("year")
        year_value = int(year) if isinstance(year, int) else None

        existing = None
        if doi:
            existing = db.scalar(select(Paper).where(Paper.doi == doi))
        if not existing:
            existing = db.scalar(select(Paper).where(Paper.title == title, Paper.year == year_value))
        if existing:
            skipped_titles.append(title)
            continue

        paper = Paper(
            title=title,
            abstract=str(item.get("abstract_brief") or "UNVERIFIED").strip(),
            year=year_value,
            venue=str(item.get("venue") or "").strip() or None,
            doi=doi,
            source_url=str(item.get("source_url") or "").strip() or None,
            status="metadata_ready",
        )
        db.add(paper)
        db.flush()
        created_ids.append(paper.id)

        for tag_name in item.get("tags", []) if isinstance(item.get("tags"), list) else []:
            cleaned = str(tag_name).strip()
            if cleaned:
                db.add(PaperTag(paper_id=paper.id, tag_name=cleaned, tag_category="topic", source="literature_workflow"))

    db.commit()
    return {"created_count": len(created_ids), "created_ids": created_ids, "skipped_titles": skipped_titles}
