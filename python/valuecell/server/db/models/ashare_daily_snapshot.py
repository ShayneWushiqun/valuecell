from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from .base import Base


class AShareDailySnapshot(Base):
    __tablename__ = "ashare_daily_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    snapshot_date = Column(String(20), nullable=False, index=True)
    generated_at = Column(DateTime(timezone=True), nullable=False)
    market_digest_json = Column(JSON, nullable=False, default=dict)
    attention_digest_json = Column(JSON, nullable=False, default=dict)
    top_alerts_json = Column(JSON, nullable=False, default=list)
    top_opportunities_json = Column(JSON, nullable=False, default=list)
    top_holdings_to_handle_json = Column(JSON, nullable=False, default=list)
    top_holdings_stable_json = Column(JSON, nullable=False, default=list)
    today_action_queue_json = Column(JSON, nullable=False, default=list)
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "snapshot_date": self.snapshot_date,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "market_digest": self.market_digest_json or {},
            "attention_digest": self.attention_digest_json or {},
            "top_alerts": list(self.top_alerts_json or []),
            "top_opportunities": list(self.top_opportunities_json or []),
            "top_holdings_to_handle": list(self.top_holdings_to_handle_json or []),
            "top_holdings_stable": list(self.top_holdings_stable_json or []),
            "today_action_queue": list(self.today_action_queue_json or []),
            "metadata": self.metadata_json or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
