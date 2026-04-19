from __future__ import annotations

from pydantic import BaseModel, Field


class StockAnalysisEvidenceConflictSummaryData(BaseModel):
    conflict_level: str = "low"
    supporting_evidence: list[str] = Field(default_factory=list)
    opposing_evidence: list[str] = Field(default_factory=list)
    risk_evidence: list[str] = Field(default_factory=list)
    neutral_evidence: list[str] = Field(default_factory=list)
    conflict_reason: str = ""
    resolution_suggestion: str = ""
    should_weaken_thesis: bool = False
    should_recheck_before_concluding: bool = False
