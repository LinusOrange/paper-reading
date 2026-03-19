from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.db import get_db
from backend.app.models import Paper, PaperAnalysis, PaperTag, ProcessingTask
from backend.app.schemas import (
    ImportBibtexRequest,
    ImportDOIRequest,
    ImportURLRequest,
    PaperDetail,
    PaperStatus,
    PaperSummary,
    PaperUpdateRequest,
)

router = APIRouter(prefix="/papers", tags=["papers"])


def _fallback_summary() -> PaperSummary:
    return PaperSummary(
        problem="Awaiting OpenAI summary generation.",
        method="Pending analysis.",
        scenario="airborne SAR / high-resolution",
        contributions=[],
        datasets_or_simulation=[],
        metrics=[],
        limitations=[],
    )


def _paper_to_schema(paper: Paper) -> PaperDetail:
    summary_json = paper.analysis.summary_json if paper.analysis else None
    summary = PaperSummary(**summary_json) if summary_json else _fallback_summary()
    return PaperDetail(
        id=paper.id,
        title=paper.title,
        year=paper.year or datetime.now(timezone.utc).year,
        venue=paper.venue,
        doi=paper.doi,
        source_url=paper.source_url,
        status=PaperStatus(paper.status),
        tags=[tag.tag_name for tag in paper.tags],
        pdf_object_key=paper.pdf_object_key,
        full_text_available=bool(paper.full_text),
        summary=summary,
        created_at=paper.created_at,
        updated_at=paper.updated_at,
    )


def _create_processing_task(db: Session, paper_id: int, task_name: str, provider: str = "openai") -> None:
    db.add(
        ProcessingTask(
            paper_id=paper_id,
            task_name=task_name,
            state="queued",
            provider=provider,
            payload={},
        )
    )


def _attach_direction_tags(db: Session, paper_id: int, direction_hint: list[str]) -> None:
    existing_tags = {
        tag.tag_name
        for tag in db.scalars(select(PaperTag).where(PaperTag.paper_id == paper_id)).all()
    }
    for tag_name in direction_hint:
        if tag_name not in existing_tags:
            db.add(PaperTag(paper_id=paper_id, tag_name=tag_name, tag_category="topic", source="request"))


@router.post("/import/doi", response_model=dict)
def import_by_doi(payload: ImportDOIRequest, db: Session = Depends(get_db)) -> dict:
    paper = db.scalar(select(Paper).where(Paper.doi == payload.doi))
    if paper:
        return {"message": "DOI already exists", "paper_id": paper.id, "doi": paper.doi}

    paper = Paper(
        title=f"Imported DOI {payload.doi}",
        abstract="Imported from DOI request.",
        year=datetime.now(timezone.utc).year,
        doi=payload.doi,
        source_url=f"https://doi.org/{payload.doi}",
        status="metadata_ready",
    )
    db.add(paper)
    db.flush()
    _attach_direction_tags(db, paper.id, [tag.value for tag in payload.direction_hint])
    if payload.auto_analyze:
        _create_processing_task(db, paper.id, "generate_summary")
        _create_processing_task(db, paper.id, "build_embeddings")
    db.commit()
    return {"message": "DOI import accepted", "paper_id": paper.id, "doi": payload.doi}


@router.post("/import/url", response_model=dict)
def import_by_url(payload: ImportURLRequest, db: Session = Depends(get_db)) -> dict:
    paper = Paper(
        title=f"Imported URL {payload.url}",
        abstract="Imported from URL request.",
        year=datetime.now(timezone.utc).year,
        source_url=payload.url,
        status="metadata_ready",
    )
    db.add(paper)
    db.flush()
    _attach_direction_tags(db, paper.id, [tag.value for tag in payload.direction_hint])
    if payload.auto_analyze:
        _create_processing_task(db, paper.id, "extract_text")
        _create_processing_task(db, paper.id, "generate_summary")
    db.commit()
    return {"message": "URL import accepted", "paper_id": paper.id, "url": payload.url}


@router.post("/import/bibtex", response_model=dict)
def import_by_bibtex(payload: ImportBibtexRequest, db: Session = Depends(get_db)) -> dict:
    title = payload.bibtex.split("title=")[-1][:80] if "title=" in payload.bibtex else "Imported BibTeX entry"
    paper = Paper(
        title=title,
        abstract="Imported from BibTeX request.",
        year=datetime.now(timezone.utc).year,
        status="metadata_ready",
    )
    db.add(paper)
    db.flush()
    _attach_direction_tags(db, paper.id, [tag.value for tag in payload.direction_hint])
    _create_processing_task(db, paper.id, "deduplicate")
    _create_processing_task(db, paper.id, "fetch_metadata")
    db.commit()
    return {"message": "BibTeX import accepted", "paper_id": paper.id, "size": len(payload.bibtex)}


@router.post("/import/pdf", response_model=dict)
def import_by_pdf(db: Session = Depends(get_db)) -> dict:
    paper = Paper(
        title="Uploaded PDF placeholder",
        abstract="PDF upload endpoint scaffolded for next phase.",
        year=datetime.now(timezone.utc).year,
        status="metadata_ready",
    )
    db.add(paper)
    db.flush()
    _create_processing_task(db, paper.id, "extract_text")
    _create_processing_task(db, paper.id, "generate_summary")
    db.commit()
    return {"message": "PDF upload endpoint scaffolded", "paper_id": paper.id}


@router.get("", response_model=list[PaperDetail])
def list_papers(db: Session = Depends(get_db)) -> list[PaperDetail]:
    papers = db.scalars(
        select(Paper).options(selectinload(Paper.tags), selectinload(Paper.analysis)).order_by(Paper.created_at.desc())
    ).all()
    return [_paper_to_schema(paper) for paper in papers]


@router.get("/{paper_id}", response_model=PaperDetail)
def get_paper(paper_id: int, db: Session = Depends(get_db)) -> PaperDetail:
    paper = db.scalar(
        select(Paper).options(selectinload(Paper.tags), selectinload(Paper.analysis)).where(Paper.id == paper_id)
    )
    if not paper:
        raise HTTPException(status_code=404, detail="paper not found")
    return _paper_to_schema(paper)


@router.patch("/{paper_id}", response_model=PaperDetail)
def update_paper(paper_id: int, payload: PaperUpdateRequest, db: Session = Depends(get_db)) -> PaperDetail:
    paper = db.scalar(
        select(Paper).options(selectinload(Paper.tags), selectinload(Paper.analysis)).where(Paper.id == paper_id)
    )
    if not paper:
        raise HTTPException(status_code=404, detail="paper not found")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(paper, field, value.value if isinstance(value, PaperStatus) else value)

    db.commit()
    db.refresh(paper)
    return _paper_to_schema(paper)


@router.get("/{paper_id}/similar", response_model=list[dict])
def similar_papers(paper_id: int, db: Session = Depends(get_db)) -> list[dict]:
    current = db.scalar(select(Paper).where(Paper.id == paper_id))
    if not current:
        raise HTTPException(status_code=404, detail="paper not found")

    other_papers = db.scalars(select(Paper).where(Paper.id != paper_id).limit(5)).all()
    return [
        {
            "paper_id": paper_id,
            "similar_paper_id": paper.id,
            "reason": "shared high-resolution airborne SAR topic",
        }
        for paper in other_papers
    ]
