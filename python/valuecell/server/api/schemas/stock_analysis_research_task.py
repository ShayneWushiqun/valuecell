from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class StockAnalysisResearchTaskItemData(BaseModel):
    task_id: int
    thread_id: int
    user_id: str
    title: str
    summary: str
    task_type: str
    status: str
    priority: str
    source_kind: str
    source_ref: str | None = None
    related_tickers_json: list[str] = Field(default_factory=list)
    related_themes_json: list[str] = Field(default_factory=list)
    related_context_ids_json: list[int] = Field(default_factory=list)
    related_memory_id: int | None = None
    related_compression_id: int | None = None
    related_message_id: str | None = None
    resolution_note: str | None = None
    dismiss_reason: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    dismissed_at: datetime | None = None


class StockAnalysisResearchTaskListData(BaseModel):
    thread_id: int
    items: list[StockAnalysisResearchTaskItemData] = Field(default_factory=list)
    count: int = 0
    open_count: int = 0
    high_priority_open_count: int = 0
    last_generated_at: datetime | None = None
    has_actionable_gap: bool = False
    actionable_gap_summary: str | None = None
    generated_at: datetime


class StockAnalysisResearchTaskCreateRequest(BaseModel):
    title: str
    summary: str = ""
    task_type: str = "next_question"
    priority: str = "medium"
    source_kind: str = "manual"
    source_ref: str | None = None
    related_tickers_json: list[str] = Field(default_factory=list)
    related_themes_json: list[str] = Field(default_factory=list)
    related_context_ids_json: list[int] = Field(default_factory=list)
    related_memory_id: int | None = None
    related_compression_id: int | None = None
    related_message_id: str | None = None


class StockAnalysisResearchTaskGenerateRequest(BaseModel):
    pass


class StockAnalysisResearchTaskGenerateData(BaseModel):
    thread_id: int
    created_count: int = 0
    updated_count: int = 0
    items: list[StockAnalysisResearchTaskItemData] = Field(default_factory=list)
    last_generated_at: datetime | None = None
    summary: str | None = None


class StockAnalysisResearchTaskStateRequest(BaseModel):
    note: str | None = None


class StockAnalysisResearchTaskMutationData(BaseModel):
    thread_id: int
    task: StockAnalysisResearchTaskItemData
