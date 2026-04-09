"""API schemas for phase one portfolio operations."""

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class HoldingDiagnosisData(BaseModel):
    """Structured diagnosis data for a holding."""

    id: int = Field(..., description="Diagnosis ID")
    holding_id: int = Field(..., description="Holding ID")
    diagnosis_date: date = Field(..., description="Diagnosis date")
    action: str = Field(..., description="Primary action")
    risk_level: str = Field(..., description="Risk level")
    confidence: str = Field(..., description="Confidence level")
    summary: str = Field(..., description="Readable diagnosis summary")
    key_risk: Optional[str] = Field(None, description="Primary risk label")
    reasons: list[str] = Field(default_factory=list, description="Diagnosis reasons")
    trigger_conditions: list[str] = Field(
        default_factory=list,
        description="Conditions that confirm the suggested action",
    )
    invalid_conditions: list[str] = Field(
        default_factory=list,
        description="Conditions that invalidate the suggestion",
    )
    is_focus: bool = Field(..., description="Whether this item needs focus")
    raw_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw context snapshot for frontend display",
    )
    created_at: datetime = Field(..., description="Creation timestamp")


class HoldingMarketSnapshotData(BaseModel):
    """Derived market snapshot for a holding row."""

    current_price: Optional[float] = Field(None, description="Current price")
    latest_change_percent: Optional[float] = Field(
        None,
        description="Latest daily change percent",
    )
    profit_percent: Optional[float] = Field(
        None,
        description="Profit percent versus cost price",
    )


class UserHoldingData(BaseModel):
    """Holding data with latest diagnosis."""

    id: int = Field(..., description="Holding ID")
    user_id: str = Field(..., description="User ID")
    ticker: str = Field(..., description="A-share ticker")
    exchange: str = Field(..., description="Exchange code")
    asset_name: Optional[str] = Field(None, description="Display name")
    quantity: float = Field(..., description="Holding quantity")
    cost_price: float = Field(..., description="Average cost price")
    position_weight: Optional[float] = Field(None, description="Position weight")
    buy_date: Optional[date] = Field(None, description="Buy date")
    thesis_note: Optional[str] = Field(None, description="Investment thesis note")
    notes: Optional[str] = Field(None, description="General notes")
    latest_diagnosis: Optional[HoldingDiagnosisData] = Field(
        None,
        description="Latest diagnosis result",
    )
    market_snapshot: HoldingMarketSnapshotData = Field(
        ...,
        description="Derived market snapshot",
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")


class CreateHoldingRequest(BaseModel):
    """Request schema for creating a holding."""

    ticker: str = Field(..., description="A-share ticker or 6-digit symbol")
    asset_name: Optional[str] = Field(None, description="Optional display name")
    quantity: float = Field(..., gt=0, description="Holding quantity")
    cost_price: float = Field(..., gt=0, description="Average cost price")
    position_weight: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Portfolio weight percentage",
    )
    buy_date: Optional[date] = Field(None, description="Buy date")
    thesis_note: Optional[str] = Field(None, description="Investment thesis")
    notes: Optional[str] = Field(None, description="Other notes")


class UpdateHoldingRequest(CreateHoldingRequest):
    """Request schema for updating a holding."""


class HoldingListData(BaseModel):
    """Response payload for holding list."""

    items: list[UserHoldingData] = Field(..., description="Holding rows")
    count: int = Field(..., description="Holding count")


class DailyBriefingFocusItemData(BaseModel):
    """Daily briefing focus item."""

    type: str = Field(..., description="Focus item type")
    ticker: str = Field(..., description="Ticker")
    title: str = Field(..., description="Short title")
    summary: str = Field(..., description="Readable summary")


class DailyBriefingMetricData(BaseModel):
    """Daily briefing aggregated metric."""

    label: str = Field(..., description="Metric label")
    value: str = Field(..., description="Metric value")


class WatchlistHighlightData(BaseModel):
    """Watchlist highlight item."""

    ticker: str = Field(..., description="Ticker")
    display_name: Optional[str] = Field(None, description="Display name")
    change_percent: float = Field(..., description="Price change percent")
    signal: str = Field(..., description="Highlight signal")


class DailyBriefingSummaryData(BaseModel):
    """Structured summary payload for daily briefing."""

    headline: str = Field(..., description="Headline")
    focus_items: list[DailyBriefingFocusItemData] = Field(
        default_factory=list,
        description="Focus items",
    )
    holding_actions: list[DailyBriefingMetricData] = Field(
        default_factory=list,
        description="Holding action metrics",
    )
    watchlist_highlights: list[WatchlistHighlightData] = Field(
        default_factory=list,
        description="Watchlist highlights",
    )


class DailyBriefingData(BaseModel):
    """Daily briefing response schema."""

    id: int = Field(..., description="Briefing ID")
    user_id: str = Field(..., description="User ID")
    briefing_date: date = Field(..., description="Briefing date")
    content_markdown: str = Field(..., description="Readable markdown content")
    summary: DailyBriefingSummaryData = Field(..., description="Structured summary")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")


class PortfolioOverviewData(BaseModel):
    """Portfolio home overview payload."""

    briefing: DailyBriefingData = Field(..., description="Latest daily briefing")
    holdings: list[UserHoldingData] = Field(
        default_factory=list,
        description="Latest holdings",
    )
    holding_count: int = Field(..., description="Holding count")
