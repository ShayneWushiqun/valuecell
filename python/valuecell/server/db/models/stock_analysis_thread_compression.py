from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from .base import Base


class StockAnalysisThreadCompression(Base):
    __tablename__ = "stock_analysis_thread_compressions"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    conversation_id = Column(String(120), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(String(2000), nullable=False, default="")
    current_focus = Column(String(255), nullable=False, default="")
    covered_until_message_id = Column(String(120), nullable=True)
    covered_message_count = Column(Integer, nullable=False, default=0)
    source_message_ids_json = Column(JSON, nullable=False, default=list)
    resolved_topics_json = Column(JSON, nullable=False, default=list)
    open_questions_json = Column(JSON, nullable=False, default=list)
    recent_compare_notes_json = Column(JSON, nullable=False, default=list)
    recent_refresh_notes_json = Column(JSON, nullable=False, default=list)
    recent_tooling_notes_json = Column(JSON, nullable=False, default=list)
    recent_evidence_notes_json = Column(JSON, nullable=False, default=list)
    active_memory_id = Column(Integer, nullable=True)
    focus_tickers_json = Column(JSON, nullable=False, default=list)
    focus_themes_json = Column(JSON, nullable=False, default=list)
    compared_tickers_json = Column(JSON, nullable=False, default=list)
    next_questions_json = Column(JSON, nullable=False, default=list)
    compression_reason = Column(String(255), nullable=False, default="manual_capture")
    is_active = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "compression_id": self.id,
            "thread_id": self.thread_id,
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "title": self.title,
            "summary": self.summary,
            "current_focus": self.current_focus,
            "covered_until_message_id": self.covered_until_message_id,
            "covered_message_count": int(self.covered_message_count or 0),
            "source_message_ids_json": list(self.source_message_ids_json or []),
            "resolved_topics_json": list(self.resolved_topics_json or []),
            "open_questions_json": list(self.open_questions_json or []),
            "recent_compare_notes_json": list(self.recent_compare_notes_json or []),
            "recent_refresh_notes_json": list(self.recent_refresh_notes_json or []),
            "recent_tooling_notes_json": list(self.recent_tooling_notes_json or []),
            "recent_evidence_notes_json": list(self.recent_evidence_notes_json or []),
            "active_memory_id": self.active_memory_id,
            "focus_tickers_json": list(self.focus_tickers_json or []),
            "focus_themes_json": list(self.focus_themes_json or []),
            "compared_tickers_json": list(self.compared_tickers_json or []),
            "next_questions_json": list(self.next_questions_json or []),
            "compression_reason": self.compression_reason,
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
