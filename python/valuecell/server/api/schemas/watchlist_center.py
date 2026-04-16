from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class WatchlistCenterSummaryData(BaseModel):
    total_count: int
    focus_count: int
    normal_count: int
    theme_resonance_count: int
    opportunity_linked_count: int
    active_alert_count: int
    holding_linked_count: int


class WatchlistCenterItemData(BaseModel):
    ticker: str
    display_name: str
    watchlist_name: str
    theme_name: str | None = None
    status: str
    reason: str
    tradeability_state: str
    expectation_gap_level: str
    role_label: str
    trend_quality: str
    latest_price: str | None = None
    change_percent: float | None = None
    has_theme_resonance: bool
    has_opportunity_link: bool
    has_active_alert: bool
    has_holding: bool
    holding_action: str | None = None
    linked_candidate_state: str | None = None
    linked_judge_action: str | None = None
    observation_priority: str
    quick_note: str


class WatchlistCenterGroupedData(BaseModel):
    focus_items: list[WatchlistCenterItemData] = Field(default_factory=list)
    resonance_items: list[WatchlistCenterItemData] = Field(default_factory=list)
    normal_items: list[WatchlistCenterItemData] = Field(default_factory=list)
    holding_linked_items: list[WatchlistCenterItemData] = Field(default_factory=list)


class WatchlistCenterOverviewData(BaseModel):
    generated_at: datetime
    available: bool
    empty_message: str | None = None
    summary: WatchlistCenterSummaryData
    items: list[WatchlistCenterItemData] = Field(default_factory=list)
    grouped: WatchlistCenterGroupedData
