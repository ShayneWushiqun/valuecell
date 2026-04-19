from __future__ import annotations

from pydantic import BaseModel, Field


class StockAnalysisPlanningPreferenceData(BaseModel):
    planning_profile: str = "balanced"
    feedback_window_size: int = 0
    feedback_signals_used: list[str] = Field(default_factory=list)
    preferred_first_action: str = "explicit_context"
    preferred_evidence_order: list[str] = Field(default_factory=list)
    prefer_compare_first: bool = False
    prefer_refresh_first: bool = False
    prefer_internal_first: bool = False
    prefer_external_confirmation: bool = False
    avoid_over_research: bool = False
    planning_adjustments: list[str] = Field(default_factory=list)
    adjustment_reasoning: str = ""
    confidence_hint: str | None = None


class StockAnalysisAdaptivePlanningData(BaseModel):
    planning_profile: str = "balanced"
    feedback_window_size: int = 0
    feedback_signals_used: list[str] = Field(default_factory=list)
    preferred_first_action: str = "explicit_context"
    preferred_evidence_order: list[str] = Field(default_factory=list)
    prefer_compare_first: bool = False
    prefer_refresh_first: bool = False
    prefer_internal_first: bool = False
    prefer_external_confirmation: bool = False
    avoid_over_research: bool = False
    planning_adjustments: list[str] = Field(default_factory=list)
    adjustment_reasoning: str = ""
    confidence_hint: str | None = None
    preferences: StockAnalysisPlanningPreferenceData | None = None


class StockAnalysisEvidenceStepData(BaseModel):
    source_type: str
    provider: str | None = None
    reason: str
    required: bool = True
    status: str = "planned"
    result_summary: str | None = None
    conflict_flag: bool = False


class StockAnalysisEvidenceOrchestrationData(BaseModel):
    evidence_plan_summary: str = ""
    evidence_order: list[str] = Field(default_factory=list)
    evidence_steps: list[StockAnalysisEvidenceStepData] = Field(default_factory=list)
    stop_conditions: list[str] = Field(default_factory=list)
    executed_evidence_sources: list[str] = Field(default_factory=list)
    skipped_evidence_sources: list[str] = Field(default_factory=list)
    evidence_conflict_summary: str | None = None
    evidence_confidence_hint: str | None = None
    evidence_merge_notes: list[str] = Field(default_factory=list)
