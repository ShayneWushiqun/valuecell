"""
ValueCell Server - Holding Diagnosis Model

This module defines persisted structured diagnosis results for user holdings.
"""

from typing import Any, Dict

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from .base import Base


class HoldingDiagnosis(Base):
    """Structured diagnosis record for a single holding."""

    __tablename__ = "holding_diagnoses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    holding_id = Column(
        Integer,
        ForeignKey("user_holdings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    diagnosis_date = Column(Date, nullable=False, index=True)
    action = Column(String(20), nullable=False)
    risk_level = Column(String(20), nullable=False)
    confidence = Column(String(20), nullable=False)
    summary = Column(Text, nullable=False)
    key_risk = Column(String(200), nullable=True)
    reasons_json = Column(JSON, nullable=False)
    trigger_conditions_json = Column(JSON, nullable=False)
    invalid_conditions_json = Column(JSON, nullable=False)
    is_focus = Column(Boolean, nullable=False, default=False)
    raw_context_json = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert diagnosis model to a serializable dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "holding_id": self.holding_id,
            "diagnosis_date": self.diagnosis_date.isoformat(),
            "action": self.action,
            "risk_level": self.risk_level,
            "confidence": self.confidence,
            "summary": self.summary,
            "key_risk": self.key_risk,
            "reasons": list(self.reasons_json or []),
            "trigger_conditions": list(self.trigger_conditions_json or []),
            "invalid_conditions": list(self.invalid_conditions_json or []),
            "is_focus": self.is_focus,
            "raw_context": self.raw_context_json or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
