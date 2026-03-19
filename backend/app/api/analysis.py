from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.api.papers import _fallback_summary
from backend.app.db import get_db
from backend.app.models import Paper
from backend.app.schemas import PaperSummary, QARequest

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


@qa_router.post("/ask", response_model=dict)
def ask_question(payload: QARequest, db: Session = Depends(get_db)) -> dict:
    stmt = select(Paper).options(selectinload(Paper.tags), selectinload(Paper.analysis)).limit(payload.top_k)
    papers = db.scalars(stmt).all()
    citations = [paper.id for paper in papers]
    return {
        "question": payload.question,
        "answer": "Demo answer: combine grounded SAR paper summaries from PostgreSQL and OpenAI analysis.",
        "citations": citations,
    }
