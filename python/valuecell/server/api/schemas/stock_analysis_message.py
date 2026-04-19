from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class StockAnalysisMessageItemData(BaseModel):
    item_id: str
    role: str
    event: str | None = None
    conversation_id: str | None = None
    content: str
    answer_basis: str = "当前上下文"
    mode: str = "context_only"
    used_context_ids: list[int] = Field(default_factory=list)
    missing_context_hints: list[str] = Field(default_factory=list)
    compared_tickers: list[str] = Field(default_factory=list)
    comparison_mode: bool = False
    stale_context_ids: list[int] = Field(default_factory=list)
    refresh_recommended_context_ids: list[int] = Field(default_factory=list)
    tool_reason: str | None = None
    tool_calls_summary: list[str] = Field(default_factory=list)
    temporary_evidence_blocks: list[dict[str, Any]] = Field(default_factory=list)
    unavailable_tools: list[dict[str, Any]] = Field(default_factory=list)
    used_internal_sources: list[str] = Field(default_factory=list)
    used_external_sources: list[str] = Field(default_factory=list)
    provider_attempts: list[dict[str, Any]] = Field(default_factory=list)
    provider_used: list[str] = Field(default_factory=list)
    provider_fallback_chain: list[str] = Field(default_factory=list)
    evidence_generated_at: str | None = None
    evidence_staleness_hint: str | None = None
    refreshed_before_answer: bool = False
    refresh_run_summary: str | None = None
    refreshed_context_ids: list[int] = Field(default_factory=list)
    refresh_failed_context_ids: list[int] = Field(default_factory=list)
    refresh_skipped_context_ids: list[int] = Field(default_factory=list)
    refresh_changed_contexts: list[dict[str, Any]] = Field(default_factory=list)
    used_active_memory: bool = False
    active_memory_id: int | None = None
    active_memory_title: str | None = None
    active_memory_updated_at: str | None = None
    active_memory_version: int | None = None
    used_active_compression: bool = False
    active_compression_id: int | None = None
    active_compression_title: str | None = None
    active_compression_updated_at: str | None = None
    active_compression_version: int | None = None
    active_compression_covered_until_message_id: str | None = None
    active_compression_covered_message_count: int | None = None
    recent_raw_message_count: int = 0
    compression_recommended: bool = False
    compression_reason: str | None = None
    uncompressed_message_count: int = 0
    estimated_history_size: int = 0
    active_compression_stale: bool = False
    question_intent: str | None = None
    response_strategy: str | None = None
    routing_reason: str | None = None
    recommended_next_action: str | None = None
    followup_candidates: list[str] = Field(default_factory=list)
    suggested_task_titles: list[str] = Field(default_factory=list)
    execution_plan_summary: str | None = None
    executed_steps: list[dict[str, Any]] = Field(default_factory=list)
    skipped_steps: list[dict[str, Any]] = Field(default_factory=list)
    failed_steps: list[dict[str, Any]] = Field(default_factory=list)
    related_task_ids: list[int] = Field(default_factory=list)
    task_update_suggestions: list[dict[str, Any]] = Field(default_factory=list)
    validation_summary: dict[str, Any] = Field(default_factory=dict)
    thesis_change_hint: str | None = None
    focus_tickers: list[str] = Field(default_factory=list)
    focus_themes: list[str] = Field(default_factory=list)


class StockAnalysisMessageListData(BaseModel):
    conversation_id: str
    thread_id: int
    items: list[StockAnalysisMessageItemData] = Field(default_factory=list)
    count: int


class StockAnalysisMessageCreateRequest(BaseModel):
    message: str
    force_tooling: bool = False
    refresh_before_answer: bool = False
    research_task_id: int | None = None


class StockAnalysisMessageCreateData(BaseModel):
    conversation_id: str
    thread_id: int
    answer_basis: str = "当前上下文"
    mode: str = "context_only"
    used_context_ids: list[int] = Field(default_factory=list)
    missing_context_hints: list[str] = Field(default_factory=list)
    compared_tickers: list[str] = Field(default_factory=list)
    comparison_mode: bool = False
    stale_context_ids: list[int] = Field(default_factory=list)
    refresh_recommended_context_ids: list[int] = Field(default_factory=list)
    tool_reason: str | None = None
    tool_calls_summary: list[str] = Field(default_factory=list)
    temporary_evidence_blocks: list[dict[str, Any]] = Field(default_factory=list)
    unavailable_tools: list[dict[str, Any]] = Field(default_factory=list)
    used_internal_sources: list[str] = Field(default_factory=list)
    used_external_sources: list[str] = Field(default_factory=list)
    provider_attempts: list[dict[str, Any]] = Field(default_factory=list)
    provider_used: list[str] = Field(default_factory=list)
    provider_fallback_chain: list[str] = Field(default_factory=list)
    evidence_generated_at: str | None = None
    evidence_staleness_hint: str | None = None
    refreshed_before_answer: bool = False
    refresh_run_summary: str | None = None
    refreshed_context_ids: list[int] = Field(default_factory=list)
    refresh_failed_context_ids: list[int] = Field(default_factory=list)
    refresh_skipped_context_ids: list[int] = Field(default_factory=list)
    refresh_changed_contexts: list[dict[str, Any]] = Field(default_factory=list)
    used_active_memory: bool = False
    active_memory_id: int | None = None
    active_memory_title: str | None = None
    active_memory_updated_at: str | None = None
    active_memory_version: int | None = None
    used_active_compression: bool = False
    active_compression_id: int | None = None
    active_compression_title: str | None = None
    active_compression_updated_at: str | None = None
    active_compression_version: int | None = None
    active_compression_covered_until_message_id: str | None = None
    active_compression_covered_message_count: int | None = None
    recent_raw_message_count: int = 0
    compression_recommended: bool = False
    compression_reason: str | None = None
    uncompressed_message_count: int = 0
    estimated_history_size: int = 0
    active_compression_stale: bool = False
    question_intent: str | None = None
    response_strategy: str | None = None
    routing_reason: str | None = None
    recommended_next_action: str | None = None
    followup_candidates: list[str] = Field(default_factory=list)
    suggested_task_titles: list[str] = Field(default_factory=list)
    execution_plan_summary: str | None = None
    executed_steps: list[dict[str, Any]] = Field(default_factory=list)
    skipped_steps: list[dict[str, Any]] = Field(default_factory=list)
    failed_steps: list[dict[str, Any]] = Field(default_factory=list)
    related_task_ids: list[int] = Field(default_factory=list)
    task_update_suggestions: list[dict[str, Any]] = Field(default_factory=list)
    validation_summary: dict[str, Any] = Field(default_factory=dict)
    thesis_change_hint: str | None = None
    focus_tickers: list[str] = Field(default_factory=list)
    focus_themes: list[str] = Field(default_factory=list)
    user_message: StockAnalysisMessageItemData
    assistant_message: StockAnalysisMessageItemData
