from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RiskSizingTickerData(BaseModel):
    ticker: str
    display_name: str
    available: bool
    risk_level: str
    suggested_position_range: str
    suggested_first_entry_range: str
    suggested_add_range: str
    stop_loss_style: str
    profit_protection_style: str
    liquidity_warning: str | None = None
    summary: str
    reasons: list[str] = Field(default_factory=list)
    empty_message: str | None = None


class RiskSizingSummaryData(BaseModel):
    generated_at: datetime
    available: bool
    empty_message: str | None = None
    market_risk_level: str
    suggested_total_exposure_range: str
    suggested_new_position_range: str
    suggested_add_position_range: str
    holding_risk_note: str
    entry_risk_note: str
    portfolio_balance_note: str
    action_queue_note: str
    ticker_suggestions: list[RiskSizingTickerData] = Field(default_factory=list)
