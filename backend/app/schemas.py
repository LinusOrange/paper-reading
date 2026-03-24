from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PaperStatus(str, Enum):
    new = "new"
    metadata_ready = "metadata_ready"
    parsed = "parsed"
    analyzed = "analyzed"
    reviewed = "reviewed"
    archived = "archived"


class DirectionTag(str, Enum):
    airborne_sar = "airborne-sar"
    high_resolution = "high-resolution"
    high_speed = "high-speed"
    large_squint = "large-squint"


class PaperBase(BaseModel):
    title: str = Field(..., description="Paper title")
    year: int = Field(..., ge=1900, le=2100)
    venue: str | None = Field(default=None)
    doi: str | None = Field(default=None)
    source_url: str | None = Field(default=None)


class PaperSummary(BaseModel):
    problem: str
    method: str
    scenario: str
    contributions: list[str]
    speed_related_issue: str | None = None
    squint_related_issue: str | None = None
    datasets_or_simulation: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class PaperDetail(PaperBase):
    id: int
    status: PaperStatus = PaperStatus.new
    tags: list[str] = Field(default_factory=list)
    pdf_object_key: str | None = None
    pdf_preview_url: str | None = None
    full_text_available: bool = False
    summary: PaperSummary | None = None
    created_at: datetime
    updated_at: datetime


class ImportPaperRequest(BaseModel):
    direction_hint: list[DirectionTag] = Field(default_factory=list)
    auto_analyze: bool = True


class ImportDOIRequest(ImportPaperRequest):
    doi: str


class ImportURLRequest(ImportPaperRequest):
    url: str


class ImportBibtexRequest(ImportPaperRequest):
    bibtex: str


class PaperUpdateRequest(BaseModel):
    title: str | None = None
    year: int | None = Field(default=None, ge=1900, le=2100)
    venue: str | None = None
    doi: str | None = None
    source_url: str | None = None
    status: PaperStatus | None = None


class PaperCreateRequest(BaseModel):
    title: str
    year: int = Field(..., ge=1900, le=2100)
    venue: str | None = None
    doi: str | None = None
    source_url: str | None = None
    abstract: str | None = None
    tags: list[str] = Field(default_factory=list)


class PaperBatchDeleteRequest(BaseModel):
    paper_ids: list[int] = Field(default_factory=list, description="IDs of papers to delete")


class TagCreateRequest(BaseModel):
    tag_name: str
    tag_category: str = "topic"


class TagUpdateRequest(BaseModel):
    tag_name: str | None = None
    tag_category: str | None = None


class TagInfo(BaseModel):
    id: int
    paper_id: int
    tag_name: str
    tag_category: str
    source: str
    created_at: datetime


class PaperFilterRequest(BaseModel):
    query: str | None = None
    years: list[int] = Field(default_factory=list)
    tags: list[DirectionTag] = Field(default_factory=list)
    methods: list[str] = Field(default_factory=list)
    has_pdf: bool | None = None
    status: PaperStatus | None = None


class SemanticSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=10, ge=1, le=50)
    direction_hint: list[DirectionTag] = Field(default_factory=list)


class AnalysisTaskRequest(BaseModel):
    task_types: list[str] = Field(default_factory=lambda: ["generate_summary", "extract_entities", "recommend_tags"])
    provider: str = Field(default="openai")


class QARequest(BaseModel):
    question: str
    scope_tags: list[DirectionTag] = Field(default_factory=list)
    top_k: int = Field(default=8, ge=1, le=20)


class TaskInfo(BaseModel):
    id: str
    name: str
    paper_id: int | None = None
    paper_title: str | None = None
    state: str
    provider: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class CollectorRunRequest(BaseModel):
    query_group: str = Field(..., description="base/high_speed/large_squint")
    limit: int = Field(default=20, ge=1, le=200)


class PromptConfig(BaseModel):
    name: str
    version: str
    description: str
    output_schema: dict[str, str] = Field(default_factory=dict)
