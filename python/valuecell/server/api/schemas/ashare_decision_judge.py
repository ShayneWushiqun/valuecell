from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AShareDecisionJudgeRequest(BaseModel):
    ticker: str = Field(..., min_length=1, description="Target ticker")
    enable_agent: bool = Field(False, description="Whether to enable agent mode")
    force_refresh_context: bool = Field(
        False,
        description="Whether to refresh persisted alert context before judgement",
    )
    user_note: str | None = Field(
        None,
        max_length=2000,
        description="Optional user note for judgement context",
    )


class AShareDecisionJudgeData(BaseModel):
    generated_at: datetime
    ticker: str
    available: bool
    mode: str
    agent_enabled: bool
    agent_unavailable_reason: str | None = None
    action: str
    confidence: int
    summary: str
    thesis: str
    evidence: list[str] = Field(default_factory=list)
    disagreement: list[str] = Field(default_factory=list)
    missing_confirmations: list[str] = Field(default_factory=list)
    invalid_conditions: list[str] = Field(default_factory=list)
    risk_controls: list[str] = Field(default_factory=list)
    time_horizon: str
    context_snapshot: dict[str, Any]
    raw_agent_output: str | None = None
    empty_message: str | None = None
