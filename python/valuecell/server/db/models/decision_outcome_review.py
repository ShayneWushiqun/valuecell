from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func

from .base import Base


class DecisionOutcomeReview(Base):
    __tablename__ = "decision_outcome_reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    record_id = Column(Integer, nullable=False, index=True)
    ticker = Column(String(50), nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    action = Column(String(50), nullable=False, index=True)
    lifecycle_stage = Column(String(100), nullable=True)
    record_date = Column(String(20), nullable=False, index=True)
    review_date = Column(String(20), nullable=False, index=True)
    review_horizon_days = Column(Integer, nullable=False, index=True)
    available = Column(Boolean, nullable=False, default=True)
    outcome_status = Column(String(50), nullable=False, index=True)
    outcome_score = Column(Integer, nullable=False, default=0)
    price_change_pct = Column(Float, nullable=True)
    max_favorable_excursion_pct = Column(Float, nullable=True)
    max_adverse_excursion_pct = Column(Float, nullable=True)
    entry_reference_price = Column(Float, nullable=True)
    exit_reference_price = Column(Float, nullable=True)
    summary = Column(Text, nullable=False)
    what_happened = Column(Text, nullable=False)
    what_was_right = Column(Text, nullable=False)
    what_was_wrong = Column(Text, nullable=False)
    followup_view = Column(Text, nullable=False)
    risk_after_signal = Column(Text, nullable=False)
    context_consistency = Column(Text, nullable=False)
    linked_context_window_id = Column(Integer, nullable=True, index=True)
    linked_event_ids_json = Column(JSON, nullable=False, default=list)
    empty_message = Column(Text, nullable=True)
    dedupe_key = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.id,
            "user_id": self.user_id,
            "record_id": self.record_id,
            "ticker": self.ticker,
            "display_name": self.display_name,
            "action": self.action,
            "lifecycle_stage": self.lifecycle_stage,
            "record_date": self.record_date,
            "review_date": self.review_date,
            "review_horizon_days": self.review_horizon_days,
            "available": self.available,
            "outcome_status": self.outcome_status,
            "outcome_score": self.outcome_score,
            "price_change_pct": self.price_change_pct,
            "max_favorable_excursion_pct": self.max_favorable_excursion_pct,
            "max_adverse_excursion_pct": self.max_adverse_excursion_pct,
            "entry_reference_price": self.entry_reference_price,
            "exit_reference_price": self.exit_reference_price,
            "summary": self.summary,
            "what_happened": self.what_happened,
            "what_was_right": self.what_was_right,
            "what_was_wrong": self.what_was_wrong,
            "followup_view": self.followup_view,
            "risk_after_signal": self.risk_after_signal,
            "context_consistency": self.context_consistency,
            "linked_context_window_id": self.linked_context_window_id,
            "linked_event_ids_json": list(self.linked_event_ids_json or []),
            "empty_message": self.empty_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
