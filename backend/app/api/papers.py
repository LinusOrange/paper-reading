from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from backend.app.schemas import (
    ImportBibtexRequest,
    ImportDOIRequest,
    ImportURLRequest,
    PaperDetail,
    PaperStatus,
    PaperSummary,
)

router = APIRouter(prefix="/papers", tags=["papers"])


_SAMPLE_SUMMARY = PaperSummary(
    problem="Improve airborne high-resolution SAR imaging under motion and squint constraints.",
    method="Use motion compensation with a scene-adaptive imaging formulation.",
    scenario="airborne SAR / high-resolution / large-squint",
    contributions=[
        "Models geometry distortion under non-ideal motion.",
        "Improves image focus for large-squint trajectories.",
    ],
    speed_related_issue="Handles platform dynamics during high-speed acquisition.",
    squint_related_issue="Addresses azimuth-variant effects under large squint angles.",
    datasets_or_simulation=["simulated flight path"],
    metrics=["PSLR", "ISLR", "resolution"],
    limitations=["Needs careful parameter tuning for severe motion error."],
)


@router.post("/import/doi", response_model=dict)
def import_by_doi(payload: ImportDOIRequest) -> dict:
    return {
        "message": "DOI import accepted",
        "doi": payload.doi,
        "queued_tasks": ["fetch_metadata", "generate_summary", "build_embeddings"],
    }


@router.post("/import/url", response_model=dict)
def import_by_url(payload: ImportURLRequest) -> dict:
    return {
        "message": "URL import accepted",
        "url": payload.url,
        "queued_tasks": ["fetch_metadata", "extract_text", "generate_summary"],
    }


@router.post("/import/bibtex", response_model=dict)
def import_by_bibtex(payload: ImportBibtexRequest) -> dict:
    return {
        "message": "BibTeX import accepted",
        "size": len(payload.bibtex),
        "queued_tasks": ["deduplicate", "fetch_metadata"],
    }


@router.post("/import/pdf", response_model=dict)
def import_by_pdf() -> dict:
    return {
        "message": "PDF upload endpoint scaffolded",
        "queued_tasks": ["extract_text", "fetch_metadata", "generate_summary"],
    }


@router.get("", response_model=list[PaperDetail])
def list_papers() -> list[PaperDetail]:
    now = datetime.now(timezone.utc)
    return [
        PaperDetail(
            id=1,
            title="Large-Squint Airborne SAR Imaging Demo Paper",
            year=2024,
            venue="Demo Venue",
            doi="10.0000/demo",
            source_url="https://example.org/paper",
            status=PaperStatus.analyzed,
            tags=["airborne-sar", "high-resolution", "large-squint"],
            pdf_object_key="papers/demo.pdf",
            full_text_available=True,
            summary=_SAMPLE_SUMMARY,
            created_at=now,
            updated_at=now,
        )
    ]


@router.get("/{paper_id}", response_model=PaperDetail)
def get_paper(paper_id: int) -> PaperDetail:
    now = datetime.now(timezone.utc)
    return PaperDetail(
        id=paper_id,
        title="High-Speed Airborne SAR Imaging Demo Paper",
        year=2023,
        venue="IEEE Demo",
        doi="10.0000/highspeed",
        source_url="https://example.org/highspeed",
        status=PaperStatus.reviewed,
        tags=["airborne-sar", "high-resolution", "high-speed"],
        pdf_object_key=f"papers/{paper_id}.pdf",
        full_text_available=True,
        summary=_SAMPLE_SUMMARY,
        created_at=now,
        updated_at=now,
    )


@router.patch("/{paper_id}", response_model=dict)
def update_paper(paper_id: int, payload: dict) -> dict:
    return {"paper_id": paper_id, "updated_fields": sorted(payload.keys())}


@router.get("/{paper_id}/similar", response_model=list[dict])
def similar_papers(paper_id: int) -> list[dict]:
    return [
        {"paper_id": paper_id, "similar_paper_id": 2, "reason": "shared large-squint imaging scenario"},
        {"paper_id": paper_id, "similar_paper_id": 3, "reason": "shared motion-compensation strategy"},
    ]
