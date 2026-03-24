from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models import Paper, PaperAnalysis, PaperTag, ProcessingTask
from backend.app.services.openai_provider import build_openai_client
from backend.app.services.pdf_parser import extract_pdf_metadata
from backend.app.services.prompt_templates import ENTITIES_PROMPT, QUALITY_REVIEW_PROMPT, SUMMARY_PROMPT


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
        summary = generate_structured_summary(paper)
        quality_review = run_quality_review(paper, summary)
        if quality_review.get("revision_advice"):
            summary["limitations"] = _ensure_list(summary.get("limitations")) + [
                f"质量审计建议：{'; '.join(quality_review['revision_advice'][:2])}"
            ]

        analysis.summary_json = summary
        analysis.analysis_model = settings.openai_model if settings.openai_api_key else "中文流水线回退"
        analysis.prompt_version = "pipeline-v2"
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
                return f"{title}\n\n该文本来自已上传 PDF，来源：{venue}（{year}）。"
            except Exception:
                pass

    return f"{paper.title}\n\n{paper.abstract or '导入时未提供摘要。'}"


def generate_structured_summary(paper: Paper) -> dict:
    base = fallback_summary(paper)
    if not settings.openai_api_key:
        return base

    payload = _build_analysis_payload(paper)
    parsed = _openai_json_call(system_prompt=SUMMARY_PROMPT, user_payload=payload)
    if not parsed:
        return base

    merged = {**base, **{k: v for k, v in parsed.items() if k in SUMMARY_KEYS}}
    merged["contributions"] = _ensure_list(merged.get("contributions"))
    merged["datasets_or_simulation"] = _ensure_list(merged.get("datasets_or_simulation"))
    merged["metrics"] = _ensure_list(merged.get("metrics"))
    merged["limitations"] = _ensure_list(merged.get("limitations"))
    return merged


def generate_entities(paper: Paper, summary: dict) -> dict:
    payload = _build_analysis_payload(paper)
    payload += "\n\nSummary JSON:\n" + json.dumps(summary, ensure_ascii=False)

    if settings.openai_api_key:
        parsed = _openai_json_call(system_prompt=ENTITIES_PROMPT, user_payload=payload)
        if parsed:
            methods = _ensure_list(parsed.get("methods"))
            keywords = _ensure_list(parsed.get("keywords"))
            scenario = str(parsed.get("scenario") or summary.get("scenario") or "机载 SAR")
            return {
                "methods": sorted(set(methods)) or ["基于元数据推断"],
                "keywords": sorted(set(keywords)),
                "scenario": scenario,
            }

    text = f"{paper.title} {paper.abstract or ''} {summary.get('method', '')}".lower()
    methods: list[str] = []
    if "motion" in text:
        methods.append("运动补偿")
    if "squint" in text:
        methods.append("大斜视成像")
    if "speed" in text:
        methods.append("高速成像")
    if "autofocus" in text:
        methods.append("自聚焦")
    if not methods:
        methods.append("基于元数据推断")
    return {
        "methods": sorted(set(methods)),
        "keywords": [tag.tag_name for tag in paper.tags],
        "scenario": summary.get("scenario", "机载 SAR"),
    }


def run_quality_review(paper: Paper, summary: dict) -> dict:
    if not settings.openai_api_key:
        return {}

    payload = _build_analysis_payload(paper)
    payload += "\n\nCandidate summary JSON:\n" + json.dumps(summary, ensure_ascii=False)
    return _openai_json_call(system_prompt=QUALITY_REVIEW_PROMPT, user_payload=payload)


def ensure_recommended_tags(db: Session, paper: Paper, entities: dict, summary: dict) -> None:
    existing = {tag.tag_name for tag in paper.tags}
    inferred = {"机载SAR", "高分辨率"}

    text = f"{paper.title} {paper.abstract or ''} {summary.get('scenario', '')} {' '.join(entities.get('methods', []))}".lower()
    if "squint" in text:
        inferred.add("大斜视")
    if "speed" in text:
        inferred.add("高速")

    for tag_name in sorted(inferred - existing):
        db.add(PaperTag(paper_id=paper.id, tag_name=tag_name, tag_category="topic", source="pipeline"))


def fallback_summary(paper: Paper) -> dict:
    scenario_parts = ["机载 SAR", "high-resolution"]
    text = f"{paper.title} {paper.abstract or ''}".lower()
    if "squint" in text or paper.is_large_squint:
        scenario_parts.append("大斜视")
    if "speed" in text or paper.is_high_speed:
        scenario_parts.append("高速")
    return {
        "problem": paper.abstract or "该论文已导入，等待更深入的 AI 阅读分析。",
        "method": "当上游模型不可用时，系统根据元数据与已有文本生成结构化摘要。",
        "scenario": " / ".join(scenario_parts),
        "contributions": [
            "通过内置分析流水线生成了结构化摘要。",
            "为问答与标签推荐阶段准备了可用结构化数据。",
        ],
        "speed_related_issue": "关注高速平台运动带来的成像影响。" if ("speed" in text or paper.is_high_speed) else None,
        "squint_related_issue": "关注大斜视成像几何带来的影响。" if ("squint" in text or paper.is_large_squint) else None,
        "datasets_or_simulation": [paper.venue] if paper.venue else [],
        "metrics": ["流水线就绪"],
        "limitations": ["当上游模型输出不可用时，摘要会退化为元数据驱动结果。"],
    }


def _build_analysis_payload(paper: Paper) -> str:
    payload_parts = [
        f"Paper title: {paper.title}",
        f"Paper year: {paper.year}",
        f"Paper venue: {paper.venue}",
        f"Paper DOI: {paper.doi}",
        "\nPaper text:\n" + (paper.full_text or paper.abstract or paper.title)[:16000],
    ]

    if settings.openai_forward_pdf_source and paper.pdf_object_key:
        pdf_path = Path(paper.pdf_object_key)
        if pdf_path.exists():
            payload_parts.append(f"\nPDF source file path (uploaded on server): {pdf_path.name}")

    return "\n".join([part for part in payload_parts if part])


def _openai_json_call(system_prompt: str, user_payload: str) -> dict:
    try:
        client = build_openai_client()

        if settings.openai_forward_pdf_source:
            # Some OpenAI-compatible providers support `responses` and file input; if unavailable, fallback to chat.
            try:
                response = client.responses.create(
                    model=settings.openai_model,
                    input=[
                        {
                            "role": "system",
                            "content": [{"type": "input_text", "text": system_prompt}],
                        },
                        {
                            "role": "user",
                            "content": [{"type": "input_text", "text": user_payload}],
                        },
                    ],
                    max_output_tokens=1200,
                )
                raw = getattr(response, "output_text", "") or ""
                parsed = _safe_parse_json(raw.strip())
                if parsed:
                    return parsed
            except Exception:
                pass

        completion = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_payload},
            ],
            temperature=0,
            max_tokens=1200,
        )
        raw = (completion.choices[0].message.content or "").strip() if completion.choices else ""
        return _safe_parse_json(raw)
    except Exception:
        return {}


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
