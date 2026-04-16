from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ExitRiskItemData(BaseModel):
    holding_id: int
    ticker: str
    display_name: str
    action: str
    confidence: int
    risk_type: str
    summary: str
    thesis: str
    evidence: list[str] = Field(default_factory=list)
    disagreement: list[str] = Field(default_factory=list)
    invalid_conditions: list[str] = Field(default_factory=list)
    risk_controls: list[str] = Field(default_factory=list)
    liquidity_warning: str | None = None
    expected_exit_plan: str
    has_active_alerts: bool
    theme_name: str | None = None
    role_label: str | None = None


class ExitRiskCenterOverviewData(BaseModel):
    generated_at: datetime
    available: bool
    empty_message: str | None = None
    high_priority_items: list[ExitRiskItemData] = Field(default_factory=list)
    profit_protection_items: list[ExitRiskItemData] = Field(default_factory=list)
    discipline_stop_items: list[ExitRiskItemData] = Field(default_factory=list)
    watch_items: list[ExitRiskItemData] = Field(default_factory=list)
    risk_buckets: dict[str, int] = Field(default_factory=dict)
    count: int


class ExitRiskCenterRefreshData(ExitRiskCenterOverviewData):
    refreshed_count: int = 0
