from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request

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
    if settings.openai_api_key and settings.openai_enabled and settings.openai_doi_web_search_enabled:
        openai_result = _openai_lookup(doi)
        if openai_result and openai_result.get("title"):
            return openai_result

    crossref_result = _crossref_lookup(doi)
    if crossref_result and crossref_result.get("title"):
        return crossref_result
    return None


def _openai_lookup(doi: str) -> dict | None:
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


def _crossref_lookup(doi: str) -> dict | None:
    try:
        encoded = urllib.parse.quote(doi, safe="")
        request = urllib.request.Request(
            url=f"https://api.crossref.org/works/{encoded}",
            headers={"User-Agent": "sar-literature-demo/0.1 (metadata lookup)"},
        )
        with urllib.request.urlopen(request, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))

        message = payload.get("message", {}) if isinstance(payload, dict) else {}
        titles = message.get("title") or []
        title = str(titles[0]).strip() if titles else None

        container = message.get("container-title") or []
        venue = str(container[0]).strip() if container else None

        year = None
        issued = message.get("issued", {})
        date_parts = issued.get("date-parts") if isinstance(issued, dict) else None
        if isinstance(date_parts, list) and date_parts and isinstance(date_parts[0], list) and date_parts[0]:
            year = _parse_year(date_parts[0][0])

        authors: list[str] = []
        for author in message.get("author", []) if isinstance(message.get("author"), list) else []:
            given = str(author.get("given") or "").strip()
            family = str(author.get("family") or "").strip()
            full_name = " ".join(item for item in [given, family] if item).strip()
            if full_name:
                authors.append(full_name)

        abstract = _strip_tags(str(message.get("abstract") or "").strip()) or None
        doi_url = f"https://doi.org/{doi}"
        source_url = _clean_nullable_text(message.get("URL")) or doi_url

        return {
            "title": title,
            "authors": authors,
            "year": year,
            "venue": venue,
            "abstract": abstract,
            "source_url": source_url,
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


def _strip_tags(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"<[^>]+>", " ", text).strip()
