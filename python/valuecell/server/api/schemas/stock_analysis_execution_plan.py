from __future__ import annotations

from pydantic import BaseModel, Field


class StockAnalysisExecutionStepData(BaseModel):
    step_id: str
    step_type: str
    title: str
    reason: str
    required: bool = True
    status: str = "planned"
    source: str = "planner"
    target_refs: list[str] = Field(default_factory=list)
    result_summary: str | None = None


class StockAnalysisTaskUpdateSuggestionData(BaseModel):
    task_id: int
    suggestion: str
    reason: str
    suggested_title: str | None = None


class StockAnalysisValidationSummaryData(BaseModel):
    thesis_status: str = "thesis_maintained"
    summary: str = ""
    support_points: list[str] = Field(default_factory=list)
    opposing_points: list[str] = Field(default_factory=list)
    risk_points: list[str] = Field(default_factory=list)
    thesis_change_hint: str | None = None


class StockAnalysisExecutionPlanData(BaseModel):
    plan_id: str | None = None
    question_intent: str
    response_strategy: str
    plan_summary: str
    planning_reason: str
    focus_tickers: list[str] = Field(default_factory=list)
    focus_themes: list[str] = Field(default_factory=list)
    related_task_ids: list[int] = Field(default_factory=list)
    primary_compare_targets: list[str] = Field(default_factory=list)
    requires_refresh: bool = False
    requires_tooling: bool = False
    requires_validation: bool = False
    steps: list[StockAnalysisExecutionStepData] = Field(default_factory=list)
