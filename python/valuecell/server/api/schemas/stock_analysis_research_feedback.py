from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class StockAnalysisResearchFeedbackItemData(BaseModel):
    feedback_id: int
    thread_id: int
    user_id: str
    anchor_message_id: str
    title: str
    anchor_question_intent: str | None = None
    anchor_response_strategy: str | None = None
    anchor_mode: str | None = None
    anchor_plan_summary: str | None = None
    anchor_validation_status: str | None = None
    linked_task_ids_json: list[int] = Field(default_factory=list)
    linked_context_ids_json: list[int] = Field(default_factory=list)
    linked_memory_id: int | None = None
    linked_compression_id: int | None = None
    linked_compare_targets_json: list[dict[str, Any]] = Field(default_factory=list)
    linked_tickers_json: list[str] = Field(default_factory=list)
    linked_themes_json: list[str] = Field(default_factory=list)
    linked_outcome_review_ids_json: list[int] = Field(default_factory=list)
    linked_effectiveness_snapshot_json: dict[str, Any] = Field(default_factory=dict)
    linked_risk_sizing_snapshot_json: dict[str, Any] = Field(default_factory=dict)
    outcome_alignment_status: str
    process_quality_status: str
    compare_helpful: bool = False
    refresh_helpful: bool = False
    tooling_helpful: bool = False
    validation_helpful: bool = False
    what_helped_json: list[str] = Field(default_factory=list)
    what_hurt_json: list[str] = Field(default_factory=list)
    process_adjustments_json: list[str] = Field(default_factory=list)
    task_followup_suggestions_json: list[dict[str, Any]] = Field(default_factory=list)
    summary: str
    detail_note: str | None = None
    version: int = 1
    created_at: datetime
    updated_at: datetime


class StockAnalysisResearchFeedbackListData(BaseModel):
    thread_id: int
    items: list[StockAnalysisResearchFeedbackItemData] = Field(default_factory=list)
    latest_feedback: StockAnalysisResearchFeedbackItemData | None = None
    count: int = 0
    generated_at: datetime


class StockAnalysisResearchFeedbackCaptureRequest(BaseModel):
    anchor_message_id: str | None = None
    related_task_ids: list[int] = Field(default_factory=list)
    related_tickers: list[str] = Field(default_factory=list)
    title: str | None = None
    note: str | None = None


class StockAnalysisResearchFeedbackRefreshRequest(BaseModel):
    title: str | None = None
    note: str | None = None
    related_task_ids: list[int] = Field(default_factory=list)
    related_tickers: list[str] = Field(default_factory=list)


class StockAnalysisResearchFeedbackMutationData(BaseModel):
    thread_id: int
    feedback: StockAnalysisResearchFeedbackItemData
