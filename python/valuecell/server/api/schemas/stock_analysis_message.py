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


class StockAnalysisMessageListData(BaseModel):
    conversation_id: str
    thread_id: int
    items: list[StockAnalysisMessageItemData] = Field(default_factory=list)
    count: int


class StockAnalysisMessageCreateRequest(BaseModel):
    message: str
    force_tooling: bool = False
    refresh_before_answer: bool = False


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
    user_message: StockAnalysisMessageItemData
    assistant_message: StockAnalysisMessageItemData
