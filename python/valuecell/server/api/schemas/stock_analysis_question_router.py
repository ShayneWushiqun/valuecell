from __future__ import annotations

from pydantic import BaseModel, Field


class StockAnalysisQuestionRoutingData(BaseModel):
    question_intent: str = "general_followup"
    response_strategy: str = "answer_from_context"
    routing_reason: str = ""
    recommended_next_action: str = ""
    followup_candidates: list[str] = Field(default_factory=list)
    suggested_task_titles: list[str] = Field(default_factory=list)
    should_focus_compare_targets: bool = False
    should_revisit_active_memory: bool = False
    should_revisit_active_compression: bool = False
