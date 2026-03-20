import re
from pathlib import Path

import fitz


def _normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def _infer_title_from_text(text: str) -> str | None:
    lines = [_normalize_line(line) for line in text.splitlines() if _normalize_line(line)]
    candidates: list[str] = []
    for line in lines[:12]:
        if 8 <= len(line) <= 200 and not line.lower().startswith(("abstract", "index terms", "keywords")):
            candidates.append(line)
        if len(candidates) >= 2:
            break
    if not candidates:
        return None
    if len(candidates) >= 2 and len(candidates[0]) < 40:
        return f"{candidates[0]} {candidates[1]}".strip()
    return candidates[0]


def _infer_year(text: str, metadata: dict) -> int | None:
    for candidate in [metadata.get("creationDate", ""), text[:1500]]:
        match = re.search(r"(19|20)\d{2}", candidate or "")
        if match:
            return int(match.group(0))
    return None


def extract_pdf_metadata(file_path: str, fallback_name: str) -> dict:
    path = Path(file_path)
    title = Path(fallback_name).stem.replace("_", " ").replace("-", " ")
    year = None

    with fitz.open(path) as doc:
        metadata = doc.metadata or {}
        meta_title = _normalize_line(metadata.get("title", ""))
        first_page_text = doc[0].get_text("text") if doc.page_count else ""
        inferred_title = _infer_title_from_text(first_page_text)
        title = meta_title or inferred_title or title
        year = _infer_year(first_page_text, metadata)

    return {
        "title": title,
        "year": year,
        "venue": None,
    }
