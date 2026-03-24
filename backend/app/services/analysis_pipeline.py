from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models import Paper, PaperAnalysis, PaperTag, ProcessingTask
from backend.app.services.openai_provider import build_openai_client
from backend.app.services.pdf_parser import extract_pdf_metadata


SUMMARY_KEYS = {
    "problem",
    "method",
    "scenario",
    "contributions",
    "speed_related_issue",
    "squint_related_issue",
    "datasets_or_simulation",
    "metrics",
    "limitations",
}


def run_pipeline_task(db: Session, task: ProcessingTask) -> None:
    if not task.paper:
        raise RuntimeError("task paper not found")

    paper = task.paper
    analysis = ensure_analysis(db, paper)

    if task.task_name == "extract_text":
        paper.full_text = build_full_text(paper)
        if paper.status == "metadata_ready":
            paper.status = "parsed"
        return

    if task.task_name == "generate_summary":
        analysis.summary_json = generate_structured_summary(paper)
        analysis.analysis_model = settings.openai_model if settings.openai_api_key else "pipeline-fallback"
        analysis.prompt_version = "pipeline-v1"
        paper.status = "analyzed"
        return

    if task.task_name == "extract_entities":
        analysis.entities_json = generate_entities(paper, analysis.summary_json or {})
        if paper.status == "metadata_ready":
            paper.status = "parsed"
        return

    if task.task_name == "recommend_tags":
        ensure_recommended_tags(db, paper, analysis.entities_json or {}, analysis.summary_json or {})
        return

    if task.task_name in {"build_embeddings", "fetch_metadata", "deduplicate"}:
        paper.status = paper.status or "metadata_ready"
        return

    raise RuntimeError(f"unsupported task: {task.task_name}")


def ensure_analysis(db: Session, paper: Paper) -> PaperAnalysis:
    if paper.analysis:
        return paper.analysis
    analysis = PaperAnalysis(paper_id=paper.id, summary_json={}, entities_json={}, qa_cache=[])
    db.add(analysis)
    db.flush()
    paper.analysis = analysis
    return analysis


def build_full_text(paper: Paper) -> str:
    if paper.full_text:
        return paper.full_text

    if paper.pdf_object_key:
        pdf_path = Path(paper.pdf_object_key)
        if pdf_path.exists():
            try:
                metadata = extract_pdf_metadata(str(pdf_path), paper.title)
                title = metadata.get("title") or paper.title
                venue = metadata.get("venue") or paper.venue or "unknown venue"
                year = metadata.get("year") or paper.year or "unknown year"
                return f"{title}\n\nImported from PDF for {venue} ({year})."
            except Exception:
                pass

    return f"{paper.title}\n\n{paper.abstract or 'No abstract was provided during import.'}"


def generate_structured_summary(paper: Paper) -> dict:
    base = fallback_summary(paper)
    if not settings.openai_api_key:
        return base

    content = (paper.full_text or paper.abstract or paper.title)[:12000]
    try:
        client = build_openai_client()
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a SAR literature analyst. Return JSON only with keys: problem, method, scenario, contributions, speed_related_issue, squint_related_issue, datasets_or_simulation, metrics, limitations.",
                },
                {
                    "role": "user",
                    "content": f"Paper title: {paper.title}\n\nPaper content:\n{content}",
                },
            ],
            temperature=0,
            max_tokens=1000,
        )
        raw = (response.choices[0].message.content or "").strip() if response.choices else ""
        parsed = _safe_parse_json(raw)
        if not parsed:
            return base
        merged = {**base, **{k: v for k, v in parsed.items() if k in SUMMARY_KEYS}}
        merged["contributions"] = _ensure_list(merged.get("contributions"))
        merged["datasets_or_simulation"] = _ensure_list(merged.get("datasets_or_simulation"))
        merged["metrics"] = _ensure_list(merged.get("metrics"))
        merged["limitations"] = _ensure_list(merged.get("limitations"))
        return merged
    except Exception:
        return base


def generate_entities(paper: Paper, summary: dict) -> dict:
    text = f"{paper.title} {paper.abstract or ''} {summary.get('method', '')}".lower()
    methods: list[str] = []
    if "motion" in text:
        methods.append("motion-compensation")
    if "squint" in text:
        methods.append("large-squint-imaging")
    if "speed" in text:
        methods.append("high-speed-imaging")
    if "autofocus" in text:
        methods.append("autofocus")
    if not methods:
        methods.append("metadata-derived")
    return {
        "methods": sorted(set(methods)),
        "keywords": [tag.tag_name for tag in paper.tags],
        "scenario": summary.get("scenario", "airborne SAR"),
    }


def ensure_recommended_tags(db: Session, paper: Paper, entities: dict, summary: dict) -> None:
    existing = {tag.tag_name for tag in paper.tags}
    inferred = {"airborne-sar", "high-resolution"}

    text = f"{paper.title} {paper.abstract or ''} {summary.get('scenario', '')} {' '.join(entities.get('methods', []))}".lower()
    if "squint" in text:
        inferred.add("large-squint")
    if "speed" in text:
        inferred.add("high-speed")

    for tag_name in sorted(inferred - existing):
        db.add(PaperTag(paper_id=paper.id, tag_name=tag_name, tag_category="topic", source="pipeline"))


def fallback_summary(paper: Paper) -> dict:
    scenario_parts = ["airborne SAR", "high-resolution"]
    text = f"{paper.title} {paper.abstract or ''}".lower()
    if "squint" in text or paper.is_large_squint:
        scenario_parts.append("large-squint")
    if "speed" in text or paper.is_high_speed:
        scenario_parts.append("high-speed")
    return {
        "problem": paper.abstract or "Imported paper awaiting deeper OpenAI reading.",
        "method": "Pipeline fallback generated a structured summary from metadata and available text.",
        "scenario": " / ".join(scenario_parts),
        "contributions": [
            "Generated structured summary through the built-in analysis pipeline.",
            "Prepared data for QA and tag recommendation stages.",
        ],
        "speed_related_issue": "Covers high-speed platform dynamics." if ("speed" in text or paper.is_high_speed) else None,
        "squint_related_issue": "Covers large-squint imaging geometry." if ("squint" in text or paper.is_large_squint) else None,
        "datasets_or_simulation": [paper.venue] if paper.venue else [],
        "metrics": ["pipeline-ready"],
        "limitations": ["Fallback summary is metadata-driven when OpenAI output is unavailable."],
    }


def _ensure_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if value is None:
        return []
    as_text = str(value).strip()
    return [as_text] if as_text else []


def _safe_parse_json(raw: str) -> dict:
    if not raw:
        return {}
    candidate = raw
    if "```" in raw:
        candidate = raw.split("```")[-2] if len(raw.split("```")) >= 3 else raw
        candidate = candidate.replace("json", "", 1).strip()

    try:
        parsed = json.loads(candidate)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}
