from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ShortCycleContextEventItemData(BaseModel):
    event_id: int
    user_id: str
    ticker: str
    display_name: str
    topic_name: str | None = None
    layer: str
    event_type: str
    source: str
    occurred_at: datetime
    ingested_at: datetime
    importance_score: int
    direction: str
    time_horizon: str
    tradeability_hint: str | None = None
    summary: str
    payload_json: dict[str, Any] = Field(default_factory=dict)
    record_date: str
    is_active: bool


class ShortCycleContextEventListData(BaseModel):
    generated_at: datetime
    items: list[ShortCycleContextEventItemData] = Field(default_factory=list)
    count: int


class ShortCycleContextEventRefreshRequest(BaseModel):
    ticker: str | None = None
