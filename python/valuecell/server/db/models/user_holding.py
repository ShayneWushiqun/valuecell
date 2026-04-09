"""
ValueCell Server - User Holding Model

This module defines the database model for user-managed A-share holdings.
"""

from typing import Any, Dict

from sqlalchemy import Column, Date, DateTime, Integer, Numeric, String, Text
from sqlalchemy.sql import func

from .base import Base


class UserHolding(Base):
    """User holding model for manually maintained A-share positions."""

    __tablename__ = "user_holdings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    ticker = Column(String(50), nullable=False, index=True)
    exchange = Column(String(20), nullable=False, index=True)
    asset_name = Column(String(200), nullable=True)
    quantity = Column(Numeric(20, 4), nullable=False)
    cost_price = Column(Numeric(20, 4), nullable=False)
    position_weight = Column(Numeric(10, 4), nullable=True)
    buy_date = Column(Date, nullable=True)
    thesis_note = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert holding model to a serializable dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "ticker": self.ticker,
            "exchange": self.exchange,
            "asset_name": self.asset_name,
            "quantity": float(self.quantity),
            "cost_price": float(self.cost_price),
            "position_weight": (
                float(self.position_weight) if self.position_weight is not None else None
            ),
            "buy_date": self.buy_date.isoformat() if self.buy_date else None,
            "thesis_note": self.thesis_note,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
