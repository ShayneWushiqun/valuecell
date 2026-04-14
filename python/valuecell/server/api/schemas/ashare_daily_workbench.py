from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AShareWorkbenchMarketDigest(BaseModel):
    market_state: str | None = None
    emotion_stage: str | None = None
    temperature_score: int | None = None
    action_rhythm: str | None = None
    summary: str | None = None


class AShareWorkbenchAttentionDigest(BaseModel):
    unread_alert_count: int
    risk_alert_count: int
    near_entry_count: int
    holding_risk_count: int
    holding_profit_protection_count: int


class AShareWorkbenchAlertItem(BaseModel):
    id: int | None = None
    ticker: str
    display_name: str
    alert_type: str
    priority: str
    title: str
    body: str
    next_action: str


class AShareWorkbenchOpportunityItem(BaseModel):
    ticker: str
    display_name: str
    topic_name: str | None = None
    action: str | None = None
    candidate_state: str
    tradeability_state: str
    priority_score: int


class AShareWorkbenchHoldingItem(BaseModel):
    holding_id: int
    ticker: str
    asset_name: str
    action: str
    confidence: int
    summary: str
    profit_protection_view: str


class AShareWorkbenchActionQueueItem(BaseModel):
    title: str
    reason: str
    target_path: str


class AShareWorkbenchQuickLinks(BaseModel):
    opportunities: str
    alerts: str
    strategy_preferences: str
    portfolio: str


class AShareDailyWorkbenchOverviewData(BaseModel):
    generated_at: datetime
    available: bool
    empty_message: str | None = None
    market_digest: AShareWorkbenchMarketDigest
    attention_digest: AShareWorkbenchAttentionDigest
    top_alerts: list[AShareWorkbenchAlertItem] = Field(default_factory=list)
    top_opportunities: list[AShareWorkbenchOpportunityItem] = Field(default_factory=list)
    top_holdings_to_handle: list[AShareWorkbenchHoldingItem] = Field(default_factory=list)
    top_holdings_stable: list[AShareWorkbenchHoldingItem] = Field(default_factory=list)
    today_action_queue: list[AShareWorkbenchActionQueueItem] = Field(default_factory=list)
    quick_links: AShareWorkbenchQuickLinks


class AShareDailyWorkbenchRefreshData(BaseModel):
    generated_at: datetime
    success: bool
    message: str
    refreshed_alert_count: int
    refreshed_holding_signal_count: int
    opportunity_candidate_count: int
    near_entry_count: int
    holding_action_count: int
