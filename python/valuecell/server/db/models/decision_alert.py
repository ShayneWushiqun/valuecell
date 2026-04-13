from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from .base import Base


class DecisionAlert(Base):
    __tablename__ = "decision_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    ticker = Column(String(50), nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    topic_name = Column(String(200), nullable=True)
    alert_type = Column(String(50), nullable=False, index=True)
    priority = Column(String(20), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    body = Column(Text, nullable=False)
    next_action = Column(Text, nullable=False)
    action = Column(String(50), nullable=False, index=True)
    confidence = Column(Integer, nullable=False)
    source = Column(String(100), nullable=False)
    reasons_json = Column(JSON, nullable=False, default=list)
    payload_json = Column(JSON, nullable=False, default=dict)
    dedupe_key = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    read_at = Column(DateTime(timezone=True), nullable=True)
    dismissed_at = Column(DateTime(timezone=True), nullable=True, index=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "ticker": self.ticker,
            "display_name": self.display_name,
            "topic_name": self.topic_name,
            "alert_type": self.alert_type,
            "priority": self.priority,
            "title": self.title,
            "body": self.body,
            "next_action": self.next_action,
            "action": self.action,
            "confidence": self.confidence,
            "source": self.source,
            "reasons": list(self.reasons_json or []),
            "payload_json": self.payload_json or {},
            "dedupe_key": self.dedupe_key,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "dismissed_at": self.dismissed_at.isoformat() if self.dismissed_at else None,
        }
