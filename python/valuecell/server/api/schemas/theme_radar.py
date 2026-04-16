from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ThemeRadarSummaryData(BaseModel):
    active_theme_count: int
    strengthen_count: int
    split_count: int
    fading_count: int
    preferred_theme_hit_count: int
    watchlist_resonance_count: int
    opportunity_resonance_count: int


class ThemeRadarItemData(BaseModel):
    theme_code: str
    theme_name: str
    theme_state: str
    rank: int
    score: int
    hot_level: int
    preferred_market: str
    participation_hint: str
    etf_hint: dict[str, str] | None = None
    primary_representative: str | None = None
    representative_tickers: list[str] = Field(default_factory=list)
    core_leaders_json: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    watchlist_resonance_count: int
    opportunity_resonance_count: int
    has_preference_match: bool
    risk_tags: list[str] = Field(default_factory=list)
    observation_summary: str


class ThemeRadarGroupedData(BaseModel):
    strengthen_items: list[ThemeRadarItemData] = Field(default_factory=list)
    active_items: list[ThemeRadarItemData] = Field(default_factory=list)
    split_items: list[ThemeRadarItemData] = Field(default_factory=list)
    fading_items: list[ThemeRadarItemData] = Field(default_factory=list)


class ThemeRadarOverviewData(BaseModel):
    generated_at: datetime
    available: bool
    empty_message: str | None = None
    summary: ThemeRadarSummaryData
    items: list[ThemeRadarItemData] = Field(default_factory=list)
    grouped: ThemeRadarGroupedData
