from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DecisionEffectivenessBreakdownItem(BaseModel):
    label: str
    count: int
    effective_count: int
    partially_effective_count: int
    failed_count: int
    observing_count: int
    insufficient_count: int
    average_score: int


class DecisionEffectivenessRecentItem(BaseModel):
    ticker: str
    display_name: str
    action: str
    outcome_status: str
    summary: str
    review_date: str


class DecisionEffectivenessSummaryData(BaseModel):
    generated_at: datetime
    available: bool
    empty_message: str | None = None
    overall_summary: str
    overall_score: int
    review_count: int
    effective_count: int
    partially_effective_count: int
    failed_count: int
    observing_count: int
    insufficient_count: int
    action_breakdown: list[DecisionEffectivenessBreakdownItem] = Field(
        default_factory=list
    )
    role_breakdown: list[DecisionEffectivenessBreakdownItem] = Field(
        default_factory=list
    )
    theme_breakdown: list[DecisionEffectivenessBreakdownItem] = Field(
        default_factory=list
    )
    recent_successes: list[DecisionEffectivenessRecentItem] = Field(default_factory=list)
    recent_failures: list[DecisionEffectivenessRecentItem] = Field(default_factory=list)
