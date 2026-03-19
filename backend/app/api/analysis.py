from fastapi import APIRouter

from backend.app.schemas import PaperSummary, QARequest
from backend.app.api.papers import _SAMPLE_SUMMARY

router = APIRouter(prefix="/analysis", tags=["analysis"])
qa_router = APIRouter(prefix="/qa", tags=["qa"])


@router.post("/{paper_id}/summary", response_model=PaperSummary)
def generate_summary(paper_id: int) -> PaperSummary:
    _ = paper_id
    return _SAMPLE_SUMMARY


@router.post("/{paper_id}/extract", response_model=dict)
def extract_entities(paper_id: int) -> dict:
    return {
        "paper_id": paper_id,
        "entities": {
            "scenario": ["airborne-sar", "large-squint"],
            "methods": ["motion-compensation", "omega-k"],
            "issues": ["phase-error", "azimuth-variant"],
        },
    }


@router.post("/{paper_id}/tags", response_model=dict)
def recommend_tags(paper_id: int) -> dict:
    return {
        "paper_id": paper_id,
        "tags": ["airborne-sar", "high-resolution", "large-squint"],
    }


@qa_router.post("/ask", response_model=dict)
def ask_question(payload: QARequest) -> dict:
    return {
        "question": payload.question,
        "answer": "Demo answer: use OpenAI over the SAR paper corpus for grounded topic summaries.",
        "citations": [1],
    }
