from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class OpportunityCandidateItem(BaseModel):
    ticker: str = Field(..., description="Candidate ticker")
    display_name: str = Field(..., description="Display name")
    latest_price: str | None = Field(None, description="Latest price string")
    change_percent: float | None = Field(None, description="Latest change percent")
    topic_name: str | None = Field(None, description="Related topic or theme name")
    candidate_state: str = Field(..., description="Candidate state")
    priority_score: int = Field(..., description="Priority score from 0 to 100")
    expectation_gap_level: str = Field(..., description="Expectation gap level")
    expectation_gap_score: int = Field(..., description="Expectation gap score")
    continuity_score: int = Field(..., description="Continuity score")
    tradeability_state: str = Field(..., description="Tradeability state")
    role_label: str = Field(..., description="Role label")
    trend_quality: str = Field(..., description="Trend quality")
    ranking_bucket: str = Field(..., description="Ranking bucket")
    reasons: list[str] = Field(default_factory=list, description="Candidate reasons")
    time_horizon: str = Field(..., description="Expected time horizon")
    source_tags: list[str] = Field(default_factory=list, description="Source tags")
    action_hint: str = Field(..., description="Action hint")
    missing_confirmations: list[str] = Field(
        default_factory=list,
        description="Pending confirmations before action",
    )
    invalid_conditions: list[str] = Field(
        default_factory=list,
        description="Conditions that invalidate participation",
    )


class OpportunitySourceSummary(BaseModel):
    watchlist_count: int = Field(..., description="Watchlist observation count")
    theme_candidate_count: int = Field(..., description="Theme candidate count")
    candidate_count: int = Field(..., description="Final opportunity candidate count")


class OpportunityPoolData(BaseModel):
    generated_at: datetime = Field(..., description="Generation time")
    available: bool = Field(..., description="Whether candidates are available")
    items: list[OpportunityCandidateItem] = Field(default_factory=list)
    count: int = Field(..., description="Candidate count")
    empty_message: str | None = Field(None, description="Empty fallback message")
    source_summary: OpportunitySourceSummary = Field(..., description="Source summary")
