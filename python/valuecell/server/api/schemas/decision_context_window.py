from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DecisionContextEventSummaryData(BaseModel):
    event_id: int | None = None
    event_type: str
    layer: str
    source: str
    direction: str
    importance_score: int | None = None
    summary: str
    tradeability_hint: str | None = None


class DecisionContextWindowItemData(BaseModel):
    window_id: int
    user_id: str
    ticker: str
    display_name: str
    topic_name: str | None = None
    window_start: str
    window_end: str
    window_size: int
    market_state: str | None = None
    position_state: str | None = None
    expectation_state: str | None = None
    tradeability_state: str | None = None
    role_label: str | None = None
    trend_quality: str | None = None
    exit_liquidity_plan: str | None = None
    support_events_json: list[DecisionContextEventSummaryData] = Field(default_factory=list)
    opposing_events_json: list[DecisionContextEventSummaryData] = Field(default_factory=list)
    risk_events_json: list[DecisionContextEventSummaryData] = Field(default_factory=list)
    summary: str
    judgement_snapshot_json: dict[str, Any] = Field(default_factory=dict)
    available: bool
    linked_tags_json: list[str] = Field(default_factory=list)
    risk_level: str = "低"
    disagreement_level: str = "低"
    support_count: int = 0
    opposing_count: int = 0
    risk_count: int = 0
    has_holding: bool = False
    has_watchlist: bool = False
    has_opportunity: bool = False


class DecisionContextWindowListData(BaseModel):
    generated_at: datetime
    items: list[DecisionContextWindowItemData] = Field(default_factory=list)
    count: int


class DecisionContextWindowRefreshRequest(BaseModel):
    ticker: str | None = None
