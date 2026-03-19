from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    abstract: Mapped[str | None] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(Integer)
    doi: Mapped[str | None] = mapped_column(Text, unique=True)
    venue: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    pdf_object_key: Mapped[str | None] = mapped_column(Text)
    full_text: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="new")
    is_airborne_sar: Mapped[bool] = mapped_column(Boolean, default=True)
    is_high_resolution: Mapped[bool] = mapped_column(Boolean, default=True)
    is_high_speed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_large_squint: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    analysis: Mapped[PaperAnalysis | None] = relationship(back_populates="paper", uselist=False)
    tags: Mapped[list[PaperTag]] = relationship(back_populates="paper", cascade="all, delete-orphan")
    tasks: Mapped[list[ProcessingTask]] = relationship(back_populates="paper", cascade="all, delete-orphan")


class PaperAnalysis(Base):
    __tablename__ = "paper_analysis"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"), unique=True)
    summary_json: Mapped[dict] = mapped_column(JSON, default=dict)
    entities_json: Mapped[dict] = mapped_column(JSON, default=dict)
    qa_cache: Mapped[list] = mapped_column(JSON, default=list)
    embedding_model: Mapped[str | None] = mapped_column(Text)
    analysis_model: Mapped[str | None] = mapped_column(Text)
    prompt_version: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    paper: Mapped[Paper] = relationship(back_populates="analysis")


class PaperTag(Base):
    __tablename__ = "paper_tags"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"))
    tag_name: Mapped[str] = mapped_column(Text)
    tag_category: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text, default="openai")
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    paper: Mapped[Paper] = relationship(back_populates="tags")


class ProcessingTask(Base):
    __tablename__ = "processing_tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    paper_id: Mapped[int | None] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"))
    task_name: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(Text)
    provider: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    paper: Mapped[Paper | None] = relationship(back_populates="tasks")
