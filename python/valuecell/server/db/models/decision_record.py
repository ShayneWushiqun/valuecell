from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from .base import Base


class DecisionRecord(Base):
    __tablename__ = "decision_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    generated_at = Column(DateTime(timezone=True), nullable=False)
    record_date = Column(String(20), nullable=False, index=True)
    ticker = Column(String(50), nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    holding_id = Column(Integer, nullable=False, index=True)
    lifecycle_stage = Column(String(50), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    confidence = Column(Integer, nullable=False)
    summary = Column(Text, nullable=False)
    thesis = Column(Text, nullable=False)
    evidence_json = Column(JSON, nullable=False, default=list)
    disagreement_json = Column(JSON, nullable=False, default=list)
    invalid_conditions_json = Column(JSON, nullable=False, default=list)
    risk_controls_json = Column(JSON, nullable=False, default=list)
    theme_name = Column(String(200), nullable=True)
    role_label = Column(String(50), nullable=True)
    tradeability_state = Column(String(100), nullable=True)
    expectation_state = Column(String(100), nullable=True)
    source = Column(String(50), nullable=False, index=True)
    dedupe_key = Column(String(255), nullable=False, index=True)
    context_window_id = Column(Integer, nullable=True, index=True)
    linked_event_ids_json = Column(JSON, nullable=False, default=list)
    context_snapshot_json = Column(JSON, nullable=False, default=dict)
    outcome_status = Column(String(50), nullable=False, default="待复盘")
    review_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.id,
            "user_id": self.user_id,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "record_date": self.record_date,
            "ticker": self.ticker,
            "display_name": self.display_name,
            "holding_id": self.holding_id,
            "lifecycle_stage": self.lifecycle_stage,
            "action": self.action,
            "confidence": self.confidence,
            "summary": self.summary,
            "thesis": self.thesis,
            "evidence": list(self.evidence_json or []),
            "disagreement": list(self.disagreement_json or []),
            "invalid_conditions": list(self.invalid_conditions_json or []),
            "risk_controls": list(self.risk_controls_json or []),
            "theme_name": self.theme_name,
            "role_label": self.role_label,
            "tradeability_state": self.tradeability_state,
            "expectation_state": self.expectation_state,
            "source": self.source,
            "context_window_id": self.context_window_id,
            "linked_event_ids_json": list(self.linked_event_ids_json or []),
            "context_snapshot_json": self.context_snapshot_json or {},
            "outcome_status": self.outcome_status,
            "review_note": self.review_note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
