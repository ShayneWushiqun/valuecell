from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from .base import Base


class StockAnalysisThread(Base):
    __tablename__ = "stock_analysis_threads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    focus_type = Column(String(50), nullable=False, index=True)
    ticker_refs_json = Column(JSON, nullable=False, default=list)
    theme_refs_json = Column(JSON, nullable=False, default=list)
    conversation_id = Column(String(120), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    archived_at = Column(DateTime(timezone=True), nullable=True, index=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "thread_id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "focus_type": self.focus_type,
            "ticker_refs_json": list(self.ticker_refs_json or []),
            "theme_refs_json": list(self.theme_refs_json or []),
            "conversation_id": self.conversation_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
        }
