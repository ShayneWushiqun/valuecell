from __future__ import annotations

from pydantic import BaseModel, Field


class StrategyPreferenceTemplateData(BaseModel):
    template_id: str = Field(..., description="Template id")
    title: str = Field(..., description="Template title")
    summary: str = Field(..., description="Template summary")
    preferred_themes: list[str] = Field(default_factory=list)
    holding_period_days: int = Field(..., description="Holding period days")
    risk_style: str = Field(..., description="Risk style")
    buy_style: str = Field(..., description="Buy style")
    avoid_risks: list[str] = Field(default_factory=list)
    accept_high_position: bool = Field(..., description="Whether high position is accepted")
    prefer_expectation_gap: bool = Field(..., description="Whether expectation gap is preferred")
    prefer_leader_or_core: bool = Field(..., description="Whether leader/core is preferred")
    note: str = Field("", description="Template note")


class StrategyPreferenceTemplateListData(BaseModel):
    items: list[StrategyPreferenceTemplateData] = Field(default_factory=list)
    count: int = Field(..., description="Template count")


class StrategyPreferenceProfileData(BaseModel):
    profile_id: int | None = Field(None, description="Stored profile id")
    kind: str = Field(..., description="Profile kind")
    schema_version: int = Field(..., description="Schema version")
    template_id: str = Field(..., description="Selected template id")
    template_title: str | None = Field(None, description="Selected template title")
    preferred_themes: list[str] = Field(default_factory=list)
    holding_period_days: int = Field(..., description="Holding period days")
    risk_style: str = Field(..., description="Risk style")
    buy_style: str = Field(..., description="Buy style")
    avoid_risks: list[str] = Field(default_factory=list)
    accept_high_position: bool = Field(..., description="Whether high position is accepted")
    prefer_expectation_gap: bool = Field(..., description="Whether expectation gap is preferred")
    prefer_leader_or_core: bool = Field(..., description="Whether leader/core is preferred")
    note: str = Field("", description="Natural language note")


class UpdateStrategyPreferenceRequest(BaseModel):
    template_id: str = Field(..., description="Selected template id")
    preferred_themes: list[str] = Field(default_factory=list)
    holding_period_days: int = Field(..., ge=1, le=60)
    risk_style: str = Field(..., description="steady / balanced / aggressive")
    buy_style: str = Field(..., description="pullback / breakout / low_absorb / right_side")
    avoid_risks: list[str] = Field(default_factory=list)
    accept_high_position: bool = Field(...)
    prefer_expectation_gap: bool = Field(...)
    prefer_leader_or_core: bool = Field(...)
    note: str = Field("", max_length=2000)
