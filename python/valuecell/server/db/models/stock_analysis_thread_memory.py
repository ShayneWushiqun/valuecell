from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from .base import Base


class StockAnalysisThreadMemory(Base):
    __tablename__ = "stock_analysis_thread_memories"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(String(2000), nullable=False, default="")
    stance = Column(String(64), nullable=False, default="继续观察")
    confidence = Column(Float, nullable=False, default=0.35)
    time_horizon = Column(String(64), nullable=False, default="短线到波段")
    focus_tickers_json = Column(JSON, nullable=False, default=list)
    focus_themes_json = Column(JSON, nullable=False, default=list)
    compared_tickers_json = Column(JSON, nullable=False, default=list)
    support_points_json = Column(JSON, nullable=False, default=list)
    opposing_points_json = Column(JSON, nullable=False, default=list)
    risk_points_json = Column(JSON, nullable=False, default=list)
    key_uncertainties_json = Column(JSON, nullable=False, default=list)
    invalidation_conditions_json = Column(JSON, nullable=False, default=list)
    next_questions_json = Column(JSON, nullable=False, default=list)
    next_data_to_check_json = Column(JSON, nullable=False, default=list)
    linked_context_ids_json = Column(JSON, nullable=False, default=list)
    linked_message_ids_json = Column(JSON, nullable=False, default=list)
    linked_compare_targets_json = Column(JSON, nullable=False, default=list)
    source_snapshot_json = Column(JSON, nullable=False, default=dict)
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
            "memory_id": self.id,
            "thread_id": self.thread_id,
            "user_id": self.user_id,
            "title": self.title,
            "summary": self.summary,
            "stance": self.stance,
            "confidence": float(self.confidence or 0.0),
            "time_horizon": self.time_horizon,
            "focus_tickers_json": list(self.focus_tickers_json or []),
            "focus_themes_json": list(self.focus_themes_json or []),
            "compared_tickers_json": list(self.compared_tickers_json or []),
            "support_points_json": list(self.support_points_json or []),
            "opposing_points_json": list(self.opposing_points_json or []),
            "risk_points_json": list(self.risk_points_json or []),
            "key_uncertainties_json": list(self.key_uncertainties_json or []),
            "invalidation_conditions_json": list(
                self.invalidation_conditions_json or []
            ),
            "next_questions_json": list(self.next_questions_json or []),
            "next_data_to_check_json": list(self.next_data_to_check_json or []),
            "linked_context_ids_json": list(self.linked_context_ids_json or []),
            "linked_message_ids_json": list(self.linked_message_ids_json or []),
            "linked_compare_targets_json": list(self.linked_compare_targets_json or []),
            "source_snapshot_json": dict(self.source_snapshot_json or {}),
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
