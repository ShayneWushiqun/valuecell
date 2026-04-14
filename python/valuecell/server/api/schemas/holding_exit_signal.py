from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HoldingExitSignalData(BaseModel):
    generated_at: datetime
    holding_id: int
    ticker: str
    asset_name: str
    available: bool
    action: str
    confidence: int
    summary: str
    thesis: str
    evidence: list[str] = Field(default_factory=list)
    disagreement: list[str] = Field(default_factory=list)
    invalid_conditions: list[str] = Field(default_factory=list)
    risk_controls: list[str] = Field(default_factory=list)
    profit_protection_view: str
    time_horizon: str
    context_snapshot: dict[str, Any]
    empty_message: str | None = None


class HoldingExitSignalListData(BaseModel):
    generated_at: datetime
    items: list[HoldingExitSignalData] = Field(default_factory=list)
    count: int
