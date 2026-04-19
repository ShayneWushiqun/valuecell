from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class StockAnalysisOverviewTaskItemData(BaseModel):
    task_id: int
    thread_id: int
    thread_title: str
    title: str
    summary: str
    priority: str
    status: str
    task_type: str
    suggested_action: str | None = None
    reason: str | None = None


class StockAnalysisOverviewActionQueueItemData(BaseModel):
    kind: str
    thread_id: int
    title: str
    summary: str
    priority: str
    reason: str
    suggested_action: str
    target_ref: str | None = None


class StockAnalysisResearchQualitySummaryData(BaseModel):
    effective_count: int = 0
    mixed_count: int = 0
    under_evidenced_count: int = 0
    over_researched_count: int = 0
    confirmed_count: int = 0
    partially_confirmed_count: int = 0
    unclear_count: int = 0
    contradicted_count: int = 0


class StockAnalysisPlanningProfileSummaryData(BaseModel):
    balanced_count: int = 0
    refresh_first_count: int = 0
    compare_first_count: int = 0
    internal_first_count: int = 0
    external_confirm_first_count: int = 0
    lightweight_research_count: int = 0


class StockAnalysisRecentFeedbackSummaryData(BaseModel):
    total_feedback_count: int = 0
    effective_thread_count: int = 0
    high_conflict_thread_count: int = 0
    needs_refresh_thread_count: int = 0
    follow_up_required_thread_count: int = 0
    latest_alignment_statuses: list[str] = Field(default_factory=list)


class StockAnalysisThreadOverviewItemData(BaseModel):
    thread_id: int
    title: str
    focus_type: str
    updated_at: datetime
    context_count: int = 0
    compare_target_count: int = 0
    open_task_count: int = 0
    high_priority_task_count: int = 0
    active_memory_available: bool = False
    active_compression_available: bool = False
    refresh_recommended_count: int = 0
    stale_context_count: int = 0
    latest_planning_profile: str | None = None
    latest_conflict_level: str | None = None
    latest_validation_status: str | None = None
    latest_feedback_alignment_status: str | None = None
    latest_process_quality_status: str | None = None
    thread_health_status: str
    thread_health_score: int
    thread_health_reason: str
    headline_summary: str
    next_best_action: str
    next_best_action_reason: str


class StockAnalysisOverviewData(BaseModel):
    generated_at: datetime
    available: bool
    summary: str
    thread_overview_items: list[StockAnalysisThreadOverviewItemData] = Field(
        default_factory=list
    )
    high_priority_tasks: list[StockAnalysisOverviewTaskItemData] = Field(
        default_factory=list
    )
    high_conflict_threads: list[StockAnalysisThreadOverviewItemData] = Field(
        default_factory=list
    )
    refresh_needed_threads: list[StockAnalysisThreadOverviewItemData] = Field(
        default_factory=list
    )
    research_quality_summary: StockAnalysisResearchQualitySummaryData = Field(
        default_factory=StockAnalysisResearchQualitySummaryData
    )
    planning_profile_summary: StockAnalysisPlanningProfileSummaryData = Field(
        default_factory=StockAnalysisPlanningProfileSummaryData
    )
    recent_feedback_summary: StockAnalysisRecentFeedbackSummaryData = Field(
        default_factory=StockAnalysisRecentFeedbackSummaryData
    )
    action_queue: list[StockAnalysisOverviewActionQueueItemData] = Field(
        default_factory=list
    )
    empty_message: str | None = None
