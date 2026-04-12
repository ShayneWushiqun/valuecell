from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class EntryTimingSignalItem(BaseModel):
    ticker: str = Field(..., description="Signal ticker")
    display_name: str = Field(..., description="Display name")
    topic_name: str | None = Field(None, description="Related topic name")
    action: str = Field(..., description="Conservative action")
    confidence: int = Field(..., description="Confidence score from 0 to 100")
    summary: str = Field(..., description="Signal summary")
    reasons: list[str] = Field(default_factory=list, description="Signal reasons")
    tradeability_state: str = Field(..., description="Tradeability state")
    expectation_gap_view: str = Field(..., description="Expectation gap interpretation")
    missing_confirmations: list[str] = Field(default_factory=list)
    invalid_conditions: list[str] = Field(default_factory=list)
    candidate_state: str = Field(..., description="Candidate state from opportunity pool")
    priority_score: int = Field(..., description="Candidate priority score")
    time_horizon: str = Field(..., description="Time horizon")


class EntryTimingData(BaseModel):
    generated_at: datetime = Field(..., description="Generation time")
    available: bool = Field(..., description="Whether signals are available")
    items: list[EntryTimingSignalItem] = Field(default_factory=list)
    count: int = Field(..., description="Signal count")
    empty_message: str | None = Field(None, description="Empty fallback message")
