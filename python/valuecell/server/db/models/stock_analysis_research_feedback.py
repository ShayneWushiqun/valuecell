from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from .base import Base


class StockAnalysisResearchFeedback(Base):
    __tablename__ = "stock_analysis_research_feedback"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    anchor_message_id = Column(String(120), nullable=False, index=True)
    title = Column(String(255), nullable=False, default="")
    anchor_question_intent = Column(String(64), nullable=True, index=True)
    anchor_response_strategy = Column(String(64), nullable=True, index=True)
    anchor_mode = Column(String(32), nullable=True, index=True)
    anchor_plan_summary = Column(String(2000), nullable=True)
    anchor_validation_status = Column(String(64), nullable=True, index=True)
    linked_task_ids_json = Column(JSON, nullable=False, default=list)
    linked_context_ids_json = Column(JSON, nullable=False, default=list)
    linked_memory_id = Column(Integer, nullable=True)
    linked_compression_id = Column(Integer, nullable=True)
    linked_compare_targets_json = Column(JSON, nullable=False, default=list)
    linked_tickers_json = Column(JSON, nullable=False, default=list)
    linked_themes_json = Column(JSON, nullable=False, default=list)
    linked_outcome_review_ids_json = Column(JSON, nullable=False, default=list)
    linked_effectiveness_snapshot_json = Column(JSON, nullable=False, default=dict)
    linked_risk_sizing_snapshot_json = Column(JSON, nullable=False, default=dict)
    outcome_alignment_status = Column(
        String(32),
        nullable=False,
        default="unclear",
        index=True,
    )
    process_quality_status = Column(
        String(32),
        nullable=False,
        default="mixed",
        index=True,
    )
    compare_helpful = Column(Boolean, nullable=False, default=False)
    refresh_helpful = Column(Boolean, nullable=False, default=False)
    tooling_helpful = Column(Boolean, nullable=False, default=False)
    validation_helpful = Column(Boolean, nullable=False, default=False)
    what_helped_json = Column(JSON, nullable=False, default=list)
    what_hurt_json = Column(JSON, nullable=False, default=list)
    process_adjustments_json = Column(JSON, nullable=False, default=list)
    task_followup_suggestions_json = Column(JSON, nullable=False, default=list)
    summary = Column(String(2000), nullable=False, default="")
    detail_note = Column(String(4000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "feedback_id": self.id,
            "thread_id": self.thread_id,
            "user_id": self.user_id,
            "anchor_message_id": self.anchor_message_id,
            "title": self.title,
            "anchor_question_intent": self.anchor_question_intent,
            "anchor_response_strategy": self.anchor_response_strategy,
            "anchor_mode": self.anchor_mode,
            "anchor_plan_summary": self.anchor_plan_summary,
            "anchor_validation_status": self.anchor_validation_status,
            "linked_task_ids_json": list(self.linked_task_ids_json or []),
            "linked_context_ids_json": list(self.linked_context_ids_json or []),
            "linked_memory_id": self.linked_memory_id,
            "linked_compression_id": self.linked_compression_id,
            "linked_compare_targets_json": list(self.linked_compare_targets_json or []),
            "linked_tickers_json": list(self.linked_tickers_json or []),
            "linked_themes_json": list(self.linked_themes_json or []),
            "linked_outcome_review_ids_json": list(
                self.linked_outcome_review_ids_json or []
            ),
            "linked_effectiveness_snapshot_json": dict(
                self.linked_effectiveness_snapshot_json or {}
            ),
            "linked_risk_sizing_snapshot_json": dict(
                self.linked_risk_sizing_snapshot_json or {}
            ),
            "outcome_alignment_status": self.outcome_alignment_status,
            "process_quality_status": self.process_quality_status,
            "compare_helpful": bool(self.compare_helpful),
            "refresh_helpful": bool(self.refresh_helpful),
            "tooling_helpful": bool(self.tooling_helpful),
            "validation_helpful": bool(self.validation_helpful),
            "what_helped_json": list(self.what_helped_json or []),
            "what_hurt_json": list(self.what_hurt_json or []),
            "process_adjustments_json": list(self.process_adjustments_json or []),
            "task_followup_suggestions_json": list(
                self.task_followup_suggestions_json or []
            ),
            "summary": self.summary,
            "detail_note": self.detail_note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
