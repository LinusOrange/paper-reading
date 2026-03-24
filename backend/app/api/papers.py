from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.config import settings
from backend.app.db import get_db
from backend.app.models import Paper, PaperTag, ProcessingTask
from backend.app.schemas import (
    ImportBibtexRequest,
    ImportDOIRequest,
    ImportURLRequest,
    PaperCreateRequest,
    PaperDetail,
    PaperStatus,
    PaperSummary,
    PaperUpdateRequest,
    TagCreateRequest,
    TagInfo,
    TagUpdateRequest,
)
from backend.app.services.pdf_parser import extract_pdf_metadata

router = APIRouter(prefix="/papers", tags=["papers"])


def _fallback_summary() -> PaperSummary:
    return PaperSummary(
        problem="等待分析流水线生成摘要。",
        method="待分析。",
        scenario="机载 SAR / 高分辨率",
        contributions=[],
        datasets_or_simulation=[],
        metrics=[],
        limitations=[],
    )


def _resolve_pdf_path(paper: Paper) -> Path | None:
    if not paper.pdf_object_key:
        return None
    path = Path(paper.pdf_object_key)
    return path if path.exists() else None


def _paper_to_schema(paper: Paper) -> PaperDetail:
    summary_json = paper.analysis.summary_json if paper.analysis else None
    summary = PaperSummary(**summary_json) if summary_json else _fallback_summary()
    pdf_path = _resolve_pdf_path(paper)
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
        pdf_preview_url=f"/api/papers/{paper.id}/pdf" if pdf_path else None,
        full_text_available=bool(paper.full_text),
        summary=summary,
        created_at=paper.created_at,
        updated_at=paper.updated_at,
    )


def _tag_to_schema(tag: PaperTag) -> TagInfo:
    return TagInfo(
        id=int(tag.id),
        paper_id=int(tag.paper_id),
        tag_name=tag.tag_name,
        tag_category=tag.tag_category,
        source=tag.source,
        created_at=tag.created_at,
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


def _normalize_direction_hint(value: str | None) -> list[str]:
    if not value:
        return ["airborne-sar"]
    return [item.strip() for item in value.split(",") if item.strip()]


@router.post("", response_model=PaperDetail)
def create_paper(payload: PaperCreateRequest, db: Session = Depends(get_db)) -> PaperDetail:
    if payload.doi:
        existing = db.scalar(select(Paper).where(Paper.doi == payload.doi))
        if existing:
            raise HTTPException(status_code=409, detail="doi already exists")

    paper = Paper(
        title=payload.title,
        abstract=payload.abstract,
        year=payload.year,
        venue=payload.venue,
        doi=payload.doi,
        source_url=payload.source_url,
        status="metadata_ready",
    )
    db.add(paper)
    db.flush()

    for tag_name in payload.tags:
        cleaned = tag_name.strip()
        if cleaned:
            db.add(PaperTag(paper_id=paper.id, tag_name=cleaned, tag_category="topic", source="manual"))

    db.commit()
    db.refresh(paper)
    paper = db.scalar(select(Paper).options(selectinload(Paper.tags), selectinload(Paper.analysis)).where(Paper.id == paper.id))
    return _paper_to_schema(paper)


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
def import_by_pdf(
    file: UploadFile = File(...),
    direction_hint: str | None = Form(default=None),
    auto_analyze: bool = Form(default=True),
    db: Session = Depends(get_db),
) -> dict:
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename or "upload.pdf").suffix or ".pdf"
    object_name = f"{uuid4().hex}{suffix}"
    destination = upload_dir / object_name
    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        parsed_metadata = extract_pdf_metadata(str(destination), file.filename or object_name)
    except Exception:
        parsed_metadata = {
            "title": Path(file.filename or object_name).stem or "Untitled PDF",
            "year": None,
            "venue": None,
        }

    paper = Paper(
        title=parsed_metadata["title"],
        abstract="Imported from uploaded PDF.",
        year=parsed_metadata["year"] or datetime.now(timezone.utc).year,
        venue=parsed_metadata["venue"],
        pdf_object_key=str(destination),
        status="metadata_ready",
    )
    db.add(paper)
    db.flush()
    _attach_direction_tags(db, paper.id, _normalize_direction_hint(direction_hint))
    _create_processing_task(db, paper.id, "extract_text")
    if auto_analyze:
        _create_processing_task(db, paper.id, "generate_summary")
        _create_processing_task(db, paper.id, "extract_entities")
        _create_processing_task(db, paper.id, "recommend_tags")
    db.commit()

    return {
        "message": "PDF uploaded and metadata parsed",
        "paper_id": paper.id,
        "pdf_object_key": str(destination),
        "pdf_preview_url": f"/api/papers/{paper.id}/pdf",
        "filename": file.filename,
        "parsed_title": parsed_metadata["title"],
        "parsed_year": parsed_metadata["year"],
    }


@router.get("", response_model=list[PaperDetail])
def list_papers(tag: str | None = Query(default=None), db: Session = Depends(get_db)) -> list[PaperDetail]:
    stmt = select(Paper).options(selectinload(Paper.tags), selectinload(Paper.analysis)).order_by(Paper.created_at.desc())
    if tag:
        stmt = stmt.join(PaperTag).where(PaperTag.tag_name == tag)

    papers = db.scalars(stmt).all()
    dedup: dict[int, Paper] = {paper.id: paper for paper in papers}
    return [_paper_to_schema(paper) for paper in dedup.values()]


@router.get("/paper-tags", response_model=list[TagInfo])
def list_tags(db: Session = Depends(get_db)) -> list[TagInfo]:
    tags = db.scalars(select(PaperTag).order_by(PaperTag.created_at.desc())).all()
    return [_tag_to_schema(tag) for tag in tags]


@router.post("/paper-tags", response_model=TagInfo)
def create_tag(payload: TagCreateRequest, paper_id: int = Query(...), db: Session = Depends(get_db)) -> TagInfo:
    paper = db.scalar(select(Paper).where(Paper.id == paper_id))
    if not paper:
        raise HTTPException(status_code=404, detail="paper not found")

    tag = PaperTag(
        paper_id=paper_id,
        tag_name=payload.tag_name.strip(),
        tag_category=payload.tag_category.strip() or "topic",
        source="manual",
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return _tag_to_schema(tag)


@router.patch("/paper-tags/{tag_id}", response_model=TagInfo)
def update_tag(tag_id: int, payload: TagUpdateRequest, db: Session = Depends(get_db)) -> TagInfo:
    tag = db.scalar(select(PaperTag).where(PaperTag.id == tag_id))
    if not tag:
        raise HTTPException(status_code=404, detail="tag not found")

    if payload.tag_name is not None:
        tag.tag_name = payload.tag_name.strip()
    if payload.tag_category is not None:
        tag.tag_category = payload.tag_category.strip() or "topic"

    db.commit()
    db.refresh(tag)
    return _tag_to_schema(tag)


@router.delete("/paper-tags/{tag_id}", response_model=dict)
def delete_tag(tag_id: int, db: Session = Depends(get_db)) -> dict:
    tag = db.scalar(select(PaperTag).where(PaperTag.id == tag_id))
    if not tag:
        raise HTTPException(status_code=404, detail="tag not found")
    db.delete(tag)
    db.commit()
    return {"message": "tag deleted", "tag_id": tag_id}


@router.get("/{paper_id}", response_model=PaperDetail)
def get_paper(paper_id: int, db: Session = Depends(get_db)) -> PaperDetail:
    paper = db.scalar(
        select(Paper).options(selectinload(Paper.tags), selectinload(Paper.analysis)).where(Paper.id == paper_id)
    )
    if not paper:
        raise HTTPException(status_code=404, detail="paper not found")
    return _paper_to_schema(paper)


@router.get("/{paper_id}/pdf")
def preview_pdf(paper_id: int, db: Session = Depends(get_db)) -> FileResponse:
    paper = db.scalar(select(Paper).where(Paper.id == paper_id))
    if not paper:
        raise HTTPException(status_code=404, detail="paper not found")

    pdf_path = _resolve_pdf_path(paper)
    if not pdf_path:
        raise HTTPException(status_code=404, detail="pdf not found")

    return FileResponse(pdf_path, media_type="application/pdf", content_disposition_type="inline")


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


@router.delete("/{paper_id}", response_model=dict)
def delete_paper(paper_id: int, db: Session = Depends(get_db)) -> dict:
    paper = db.scalar(select(Paper).where(Paper.id == paper_id))
    if not paper:
        raise HTTPException(status_code=404, detail="paper not found")
    db.delete(paper)
    db.commit()
    return {"message": "paper deleted", "paper_id": paper_id}


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
