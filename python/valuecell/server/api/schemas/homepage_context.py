from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class HomepageSignalData(BaseModel):
    label: str = Field(..., description="Signal label")
    value: Any = Field(..., description="Signal value")


class HomepageStagePointData(BaseModel):
    trading_date: str = Field(..., description="Trading date")
    cycle_stage: str = Field(..., description="Cycle stage")
    stage_score: int = Field(..., description="Stage score")


class HomepageTurningPointData(BaseModel):
    trading_date: str = Field(..., description="Trading date")
    from_stage: str = Field(..., description="Previous stage")
    to_stage: str = Field(..., description="Current stage")


class HomepageMarketOverviewData(BaseModel):
    available: bool = Field(..., description="Whether market snapshot is available")
    market_state: Optional[str] = Field(None, description="Market state")
    summary: Optional[str] = Field(None, description="Readable market summary")
    confidence: Optional[str] = Field(None, description="Confidence level")
    action_hint: Optional[str] = Field(None, description="Action hint")
    signals: list[HomepageSignalData] = Field(default_factory=list)
    score: Optional[int] = Field(None, description="Market score")
    empty_message: Optional[str] = Field(None, description="Fallback message")


class HomepageEmotionCycleData(BaseModel):
    available: bool = Field(..., description="Whether emotion cycle is available")
    cycle_stage: Optional[str] = Field(None, description="Current cycle stage")
    summary: Optional[str] = Field(None, description="Readable cycle summary")
    action_hint: Optional[str] = Field(None, description="Action hint")
    trend_direction: Optional[str] = Field(None, description="Recent direction")
    stage_points: list[HomepageStagePointData] = Field(default_factory=list)
    turning_points: list[HomepageTurningPointData] = Field(default_factory=list)
    empty_message: Optional[str] = Field(None, description="Fallback message")


class HomepageThemeInstitutionData(BaseModel):
    source: str = Field(..., description="Institution proxy source")
    net_inflow: float = Field(..., description="Net inflow amount")


class HomepageThemeMetricsData(BaseModel):
    score: int = Field(..., description="Theme score")
    change_value: float = Field(..., description="Theme daily change")
    ths_flow_value: float = Field(..., description="THS flow")
    dc_flow_value: float = Field(..., description="DC flow")
    kpl_count: int = Field(..., description="Short-term co-move count")
    hot_count: int = Field(..., description="Hot list count")


class HomepageThemeItemData(BaseModel):
    trading_date: Optional[str] = Field(None, description="Trading date")
    theme_name: str = Field(..., description="Theme name")
    theme_code: str = Field(..., description="Theme code")
    theme_state: str = Field(..., description="Theme state")
    summary: str = Field(..., description="Theme summary")
    representative_tickers_json: list[str] = Field(default_factory=list)
    rank: int = Field(..., description="Theme rank")
    expectation_gap_level: str = Field(..., description="Expectation gap level")
    core_leaders_json: list[str] = Field(default_factory=list)
    core_institutions_json: list[HomepageThemeInstitutionData] = Field(
        default_factory=list
    )
    metrics: HomepageThemeMetricsData = Field(..., description="Theme metrics")


class HomepageThemeFocusData(BaseModel):
    available: bool = Field(..., description="Whether theme focus is available")
    items: list[HomepageThemeItemData] = Field(default_factory=list)
    empty_message: Optional[str] = Field(None, description="Fallback message")


class HomepageActionFrameworkData(BaseModel):
    available: bool = Field(..., description="Whether action framework is available")
    title: str = Field(..., description="Section title")
    summary: Optional[str] = Field(None, description="Framework summary")
    focus_points: list[str] = Field(default_factory=list)
    avoid_points: list[str] = Field(default_factory=list)
    empty_message: Optional[str] = Field(None, description="Fallback message")


class HomepageWatchlistObservationItemData(BaseModel):
    ticker: str = Field(..., description="Ticker")
    display_name: str = Field(..., description="Display name")
    watchlist_name: str = Field(..., description="Watchlist name")
    price: Optional[str] = Field(None, description="Formatted price")
    change_percent: Optional[float] = Field(None, description="Change percent")
    status: str = Field(..., description="Observation status")
    reason: str = Field(..., description="Observation reason")
    theme_name: Optional[str] = Field(None, description="Related theme name")


class HomepageWatchlistObservationData(BaseModel):
    available: bool = Field(..., description="Whether watchlist observation is available")
    items: list[HomepageWatchlistObservationItemData] = Field(default_factory=list)
    empty_message: Optional[str] = Field(None, description="Fallback message")


class HomepageMetricData(BaseModel):
    label: str = Field(..., description="Metric label")
    value: str = Field(..., description="Metric value")


class HomepagePortfolioHandlingData(BaseModel):
    available: bool = Field(..., description="Whether portfolio handling is available")
    summary: Optional[str] = Field(None, description="Summary")
    holding_count: int = Field(..., description="Holding count")
    focus_count: int = Field(..., description="Focus holding count")
    action_breakdown: list[HomepageMetricData] = Field(default_factory=list)
    empty_message: Optional[str] = Field(None, description="Fallback message")


class HomepageRiskControlData(BaseModel):
    available: bool = Field(..., description="Whether risk control section is available")
    summary: str = Field(..., description="Risk control summary")
    position_suggestion: str = Field(..., description="Position suggestion")
    signals: list[str] = Field(default_factory=list)
    empty_message: Optional[str] = Field(None, description="Fallback message")


class HomepageContextData(BaseModel):
    generated_at: datetime = Field(..., description="Generation timestamp")
    market_overview: HomepageMarketOverviewData = Field(...)
    emotion_cycle: HomepageEmotionCycleData = Field(...)
    theme_focus: HomepageThemeFocusData = Field(...)
    action_framework: HomepageActionFrameworkData = Field(...)
    watchlist_observation: HomepageWatchlistObservationData = Field(...)
    portfolio_handling: HomepagePortfolioHandlingData = Field(...)
    risk_control: HomepageRiskControlData = Field(...)
