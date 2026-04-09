"""
ValueCell Server - Daily Briefing Model

This module defines persisted daily briefing results for the portfolio home view.
"""

from typing import Any, Dict

from sqlalchemy import JSON, Column, Date, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from .base import Base


class DailyBriefing(Base):
    """Daily portfolio briefing record."""

    __tablename__ = "daily_briefings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    briefing_date = Column(Date, nullable=False, index=True)
    content_markdown = Column(Text, nullable=False)
    summary_json = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "briefing_date", name="uq_daily_briefing_user_date"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert briefing model to a serializable dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "briefing_date": self.briefing_date.isoformat(),
            "content_markdown": self.content_markdown,
            "summary": self.summary_json or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
