from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class HoldingLifecycleItemData(BaseModel):
    holding_id: int
    ticker: str
    display_name: str
    lifecycle_stage: str
    action: str
    confidence: int
    summary: str
    theme_name: str | None = None
    role_label: str | None = None
    trend_quality: str | None = None
    tradeability_state: str | None = None
    expectation_state: str | None = None
    observation_window: str
    invalid_conditions: list[str] = Field(default_factory=list)
    risk_controls: list[str] = Field(default_factory=list)
    profit_protection_view: str | None = None
    position_hint: str
    has_active_alerts: bool
    decision_context_available: bool


class HoldingLifecycleSummaryData(BaseModel):
    total_count: int
    need_attention_count: int
    major_hold_count: int
    high_risk_count: int
    active_alert_count: int


class HoldingLifecycleOverviewData(BaseModel):
    generated_at: datetime
    available: bool
    empty_message: str | None = None
    items: list[HoldingLifecycleItemData] = Field(default_factory=list)
    count: int
    summary: HoldingLifecycleSummaryData


class HoldingLifecycleDetailData(BaseModel):
    generated_at: datetime
    available: bool
    empty_message: str | None = None
    item: HoldingLifecycleItemData
