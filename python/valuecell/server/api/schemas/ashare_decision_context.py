from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AShareDecisionMarketContext(BaseModel):
    market_state: str | None = None
    emotion_stage: str | None = None
    temperature_score: int | None = None
    action_rhythm: str | None = None
    summary: str | None = None


class AShareDecisionThemeContext(BaseModel):
    topic_name: str | None = None
    source_tags: list[str] = Field(default_factory=list)
    role_label: str | None = None
    trend_quality: str | None = None


class AShareDecisionCandidateContext(BaseModel):
    priority_score: int | None = None
    candidate_state: str | None = None
    tradeability_state: str | None = None
    expectation_gap_level: str | None = None
    matched_preferences: list[str] = Field(default_factory=list)
    preference_adjustments: list[dict[str, Any]] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    time_horizon: str | None = None


class AShareDecisionEntryTimingContext(BaseModel):
    action: str | None = None
    confidence: int | None = None
    summary: str | None = None
    reasons: list[str] = Field(default_factory=list)
    missing_confirmations: list[str] = Field(default_factory=list)
    invalid_conditions: list[str] = Field(default_factory=list)


class AShareDecisionAlertItem(BaseModel):
    id: int | None = None
    alert_type: str
    priority: str
    title: str
    body: str
    next_action: str
    action: str
    confidence: int
    reasons: list[str] = Field(default_factory=list)
    read_at: datetime | None = None
    dismissed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AShareDecisionAlertContext(BaseModel):
    active_count: int
    items: list[AShareDecisionAlertItem] = Field(default_factory=list)


class AShareDecisionPreferenceContext(BaseModel):
    template_id: str | None = None
    template_title: str | None = None
    risk_style: str | None = None
    buy_style: str | None = None
    preferred_themes: list[str] = Field(default_factory=list)
    avoid_risks: list[str] = Field(default_factory=list)
    accept_high_position: bool | None = None
    prefer_expectation_gap: bool | None = None
    prefer_leader_or_core: bool | None = None
    note: str | None = None


class AShareDecisionPortfolioContext(BaseModel):
    has_position: bool
    summary: str | None = None
    latest_action: str | None = None
    risk_level: str | None = None
    market_snapshot: dict[str, Any] | None = None


class AShareDecisionRiskContext(BaseModel):
    items: list[str] = Field(default_factory=list)


class AShareDecisionRuleBasedJudgement(BaseModel):
    action: str
    summary: str
    reasons: list[str] = Field(default_factory=list)
    missing_confirmations: list[str] = Field(default_factory=list)
    invalid_conditions: list[str] = Field(default_factory=list)


class AShareDecisionContextData(BaseModel):
    generated_at: datetime
    ticker: str
    available: bool
    empty_message: str | None = None
    market_context: AShareDecisionMarketContext
    theme_context: AShareDecisionThemeContext
    candidate_context: AShareDecisionCandidateContext
    entry_timing_context: AShareDecisionEntryTimingContext
    alert_context: AShareDecisionAlertContext
    preference_context: AShareDecisionPreferenceContext
    portfolio_context: AShareDecisionPortfolioContext
    risk_context: AShareDecisionRiskContext
    missing_context: list[str] = Field(default_factory=list)
    rule_based_judgement: AShareDecisionRuleBasedJudgement
    agent_prompt_preview: str
