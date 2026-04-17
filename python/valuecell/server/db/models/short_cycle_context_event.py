from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from .base import Base


class ShortCycleContextEvent(Base):
    __tablename__ = "short_cycle_context_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    ticker = Column(String(50), nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    topic_name = Column(String(200), nullable=True)
    layer = Column(String(50), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    source = Column(String(100), nullable=False, index=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    ingested_at = Column(DateTime(timezone=True), nullable=False)
    importance_score = Column(Integer, nullable=False, default=50)
    direction = Column(String(20), nullable=False, index=True)
    time_horizon = Column(String(50), nullable=False, default="10-40个交易日")
    tradeability_hint = Column(String(100), nullable=True)
    summary = Column(Text, nullable=False)
    dedupe_key = Column(String(255), nullable=False, index=True)
    payload_json = Column(JSON, nullable=False, default=dict)
    record_date = Column(String(20), nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.id,
            "user_id": self.user_id,
            "ticker": self.ticker,
            "display_name": self.display_name,
            "topic_name": self.topic_name,
            "layer": self.layer,
            "event_type": self.event_type,
            "source": self.source,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
            "ingested_at": self.ingested_at.isoformat() if self.ingested_at else None,
            "importance_score": self.importance_score,
            "direction": self.direction,
            "time_horizon": self.time_horizon,
            "tradeability_hint": self.tradeability_hint,
            "summary": self.summary,
            "payload_json": self.payload_json or {},
            "record_date": self.record_date,
            "is_active": self.is_active,
        }
