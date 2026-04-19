from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from .base import Base


class StockAnalysisResearchTask(Base):
    __tablename__ = "stock_analysis_research_tasks"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(String(2000), nullable=False, default="")
    task_type = Column(String(64), nullable=False, default="next_question", index=True)
    status = Column(String(32), nullable=False, default="open", index=True)
    priority = Column(String(32), nullable=False, default="medium", index=True)
    source_kind = Column(String(64), nullable=False, default="manual", index=True)
    source_ref = Column(String(255), nullable=True)
    related_tickers_json = Column(JSON, nullable=False, default=list)
    related_themes_json = Column(JSON, nullable=False, default=list)
    related_context_ids_json = Column(JSON, nullable=False, default=list)
    related_memory_id = Column(Integer, nullable=True)
    related_compression_id = Column(Integer, nullable=True)
    related_message_id = Column(String(120), nullable=True)
    resolution_note = Column(String(1000), nullable=True)
    dismiss_reason = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)
    dismissed_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.id,
            "thread_id": self.thread_id,
            "user_id": self.user_id,
            "title": self.title,
            "summary": self.summary,
            "task_type": self.task_type,
            "status": self.status,
            "priority": self.priority,
            "source_kind": self.source_kind,
            "source_ref": self.source_ref,
            "related_tickers_json": list(self.related_tickers_json or []),
            "related_themes_json": list(self.related_themes_json or []),
            "related_context_ids_json": list(self.related_context_ids_json or []),
            "related_memory_id": self.related_memory_id,
            "related_compression_id": self.related_compression_id,
            "related_message_id": self.related_message_id,
            "resolution_note": self.resolution_note,
            "dismiss_reason": self.dismiss_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "dismissed_at": self.dismissed_at.isoformat() if self.dismissed_at else None,
        }
