from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from .base import Base


class AnalysisContextCard(Base):
    __tablename__ = "analysis_context_cards"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    context_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    subtitle = Column(String(255), nullable=True)
    ticker_refs_json = Column(JSON, nullable=False, default=list)
    theme_refs_json = Column(JSON, nullable=False, default=list)
    summary = Column(Text, nullable=False)
    snapshot_payload_json = Column(JSON, nullable=False, default=dict)
    source_module = Column(String(100), nullable=False, index=True)
    source_ref = Column(String(120), nullable=True, index=True)
    staleness_hint = Column(String(255), nullable=True)
    is_pinned = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_id": self.id,
            "thread_id": self.thread_id,
            "user_id": self.user_id,
            "context_type": self.context_type,
            "title": self.title,
            "subtitle": self.subtitle,
            "ticker_refs_json": list(self.ticker_refs_json or []),
            "theme_refs_json": list(self.theme_refs_json or []),
            "summary": self.summary,
            "snapshot_payload_json": self.snapshot_payload_json or {},
            "source_module": self.source_module,
            "source_ref": self.source_ref,
            "staleness_hint": self.staleness_hint,
            "is_pinned": self.is_pinned,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
