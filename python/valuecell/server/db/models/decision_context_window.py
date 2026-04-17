from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from .base import Base


class DecisionContextWindow(Base):
    __tablename__ = "decision_context_windows"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    ticker = Column(String(50), nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    topic_name = Column(String(200), nullable=True)
    window_start = Column(String(20), nullable=False, index=True)
    window_end = Column(String(20), nullable=False, index=True)
    window_size = Column(Integer, nullable=False, index=True)
    market_state = Column(String(100), nullable=True)
    position_state = Column(String(100), nullable=True)
    expectation_state = Column(String(100), nullable=True)
    tradeability_state = Column(String(100), nullable=True)
    role_label = Column(String(50), nullable=True)
    trend_quality = Column(String(50), nullable=True)
    exit_liquidity_plan = Column(Text, nullable=True)
    support_events_json = Column(JSON, nullable=False, default=list)
    opposing_events_json = Column(JSON, nullable=False, default=list)
    risk_events_json = Column(JSON, nullable=False, default=list)
    summary = Column(Text, nullable=False)
    judgement_snapshot_json = Column(JSON, nullable=False, default=dict)
    available = Column(Boolean, nullable=False, default=True)
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
            "window_id": self.id,
            "user_id": self.user_id,
            "ticker": self.ticker,
            "display_name": self.display_name,
            "topic_name": self.topic_name,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "window_size": self.window_size,
            "market_state": self.market_state,
            "position_state": self.position_state,
            "expectation_state": self.expectation_state,
            "tradeability_state": self.tradeability_state,
            "role_label": self.role_label,
            "trend_quality": self.trend_quality,
            "exit_liquidity_plan": self.exit_liquidity_plan,
            "support_events_json": list(self.support_events_json or []),
            "opposing_events_json": list(self.opposing_events_json or []),
            "risk_events_json": list(self.risk_events_json or []),
            "summary": self.summary,
            "judgement_snapshot_json": self.judgement_snapshot_json or {},
            "available": self.available,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
