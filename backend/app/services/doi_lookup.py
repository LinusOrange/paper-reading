from __future__ import annotations

import json
import re

from backend.app.config import settings
from backend.app.services.openai_provider import build_openai_client


DOI_METADATA_PROMPT = """
You are a scholarly metadata assistant.
Given a DOI, use web search results to find the paper's metadata.

Return JSON only with this schema:
{
  "title": "string",
  "authors": ["string"],
  "year": 2024,
  "venue": "string|null",
  "abstract": "string|null",
  "source_url": "string|null"
}

Rules:
- Prefer publisher pages, IEEE, ACM, arXiv, DOI landing page, Crossref mirrors.
- If a field cannot be verified, set it to null (or [] for authors).
- Keep abstract concise (<= 1200 chars).
- Do not include markdown.
""".strip()


def lookup_doi_metadata(doi: str) -> dict | None:
    if not settings.openai_api_key or not settings.openai_enabled or not settings.openai_doi_web_search_enabled:
        return None

    client = build_openai_client()
    user_prompt = f"Find metadata for DOI: {doi}"

    try:
        response = client.responses.create(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": DOI_METADATA_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            tools=[{"type": "web_search"}],
            tool_choice="auto",
            max_output_tokens=1200,
        )
        output_text = getattr(response, "output_text", "") or ""
        parsed = _safe_parse_json(output_text)
        if not parsed:
            return None

        year = _parse_year(parsed.get("year"))
        return {
            "title": str(parsed.get("title") or "").strip() or None,
            "authors": _to_list(parsed.get("authors")),
            "year": year,
            "venue": _clean_nullable_text(parsed.get("venue")),
            "abstract": _clean_nullable_text(parsed.get("abstract")),
            "source_url": _clean_nullable_text(parsed.get("source_url")),
        }
    except Exception:
        return None


def _safe_parse_json(raw: str) -> dict:
    if not raw:
        return {}

    candidate = raw.strip()
    if "```" in candidate:
        blocks = candidate.split("```")
        if len(blocks) >= 3:
            candidate = blocks[-2].strip()
            if candidate.startswith("json"):
                candidate = candidate[4:].strip()

    try:
        parsed = json.loads(candidate)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        match = re.search(r"\{[\s\S]*\}", candidate)
        if not match:
            return {}
        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}


def _parse_year(value: object) -> int | None:
    if isinstance(value, int):
        return value if 1900 <= value <= 2100 else None
    if value is None:
        return None

    text = str(value)
    match = re.search(r"(19|20)\d{2}", text)
    if not match:
        return None
    year = int(match.group(0))
    return year if 1900 <= year <= 2100 else None


def _to_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def _clean_nullable_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
