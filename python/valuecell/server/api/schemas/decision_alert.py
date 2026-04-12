from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DecisionAlertItem(BaseModel):
    ticker: str = Field(..., description="Alert ticker")
    display_name: str = Field(..., description="Display name")
    topic_name: str | None = Field(None, description="Related topic name")
    alert_type: str = Field(..., description="Alert type")
    priority: str = Field(..., description="Priority level")
    title: str = Field(..., description="Alert title")
    body: str = Field(..., description="Alert body")
    next_action: str = Field(..., description="Next observation action")
    action: str = Field(..., description="Source action")
    confidence: int = Field(..., description="Confidence score")
    source: str = Field(..., description="Alert source")
    reasons: list[str] = Field(default_factory=list, description="Alert reasons")


class DecisionAlertSummaryData(BaseModel):
    generated_at: datetime = Field(..., description="Generation time")
    available: bool = Field(..., description="Whether alerts are available")
    items: list[DecisionAlertItem] = Field(default_factory=list)
    count: int = Field(..., description="Alert count")
    empty_message: str | None = Field(None, description="Empty fallback message")
