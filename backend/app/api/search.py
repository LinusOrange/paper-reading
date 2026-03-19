from fastapi import APIRouter

from backend.app.schemas import PaperDetail, PaperFilterRequest, SemanticSearchRequest
from backend.app.api.papers import list_papers

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/filter", response_model=list[PaperDetail])
def filter_papers(_: PaperFilterRequest) -> list[PaperDetail]:
    return list_papers()


@router.post("/fulltext", response_model=list[PaperDetail])
def fulltext_search(_: PaperFilterRequest) -> list[PaperDetail]:
    return list_papers()


@router.post("/semantic", response_model=list[PaperDetail])
def semantic_search(_: SemanticSearchRequest) -> list[PaperDetail]:
    return list_papers()
