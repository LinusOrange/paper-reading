from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from backend.app.api.papers import _paper_to_schema
from backend.app.db import get_db
from backend.app.models import Paper, PaperTag
from backend.app.schemas import PaperDetail, PaperFilterRequest, SemanticSearchRequest

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/filter", response_model=list[PaperDetail])
def filter_papers(payload: PaperFilterRequest, db: Session = Depends(get_db)) -> list[PaperDetail]:
    stmt = select(Paper).options(selectinload(Paper.tags), selectinload(Paper.analysis))

    if payload.query:
        like_query = f"%{payload.query}%"
        stmt = stmt.where(or_(Paper.title.ilike(like_query), Paper.abstract.ilike(like_query), Paper.full_text.ilike(like_query)))
    if payload.years:
        stmt = stmt.where(Paper.year.in_(payload.years))
    if payload.status:
        stmt = stmt.where(Paper.status == payload.status.value)
    if payload.has_pdf is True:
        stmt = stmt.where(Paper.pdf_object_key.is_not(None))
    if payload.has_pdf is False:
        stmt = stmt.where(Paper.pdf_object_key.is_(None))
    if payload.tags:
        stmt = stmt.join(Paper.tags).where(PaperTag.tag_name.in_([tag.value for tag in payload.tags]))

    papers = db.scalars(stmt.order_by(Paper.created_at.desc()).distinct()).all()
    return [_paper_to_schema(paper) for paper in papers]


@router.post("/fulltext", response_model=list[PaperDetail])
def fulltext_search(payload: PaperFilterRequest, db: Session = Depends(get_db)) -> list[PaperDetail]:
    return filter_papers(payload, db)


@router.post("/semantic", response_model=list[PaperDetail])
def semantic_search(payload: SemanticSearchRequest, db: Session = Depends(get_db)) -> list[PaperDetail]:
    filter_payload = PaperFilterRequest(query=payload.query, tags=payload.direction_hint)
    papers = filter_papers(filter_payload, db)
    return papers[: payload.top_k]
