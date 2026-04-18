from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class StockAnalysisRefreshChangedContextData(BaseModel):
    context_id: int
    title: str
    changed_fields: list[str] = Field(default_factory=list)
    after_freshness_label: str | None = None


class StockAnalysisRefreshItemData(BaseModel):
    context_id: int
    title: str
    source_module: str
    refresh_supported: bool
    status: str
    reason: str
    before_freshness_label: str | None = None
    after_freshness_label: str | None = None
    changed_fields: list[str] = Field(default_factory=list)
    new_generated_at: datetime | None = None
    new_data_time: datetime | None = None


class StockAnalysisRefreshRunRequest(BaseModel):
    context_ids: list[int] = Field(default_factory=list)
    include_supported_only: bool = True
    pin_refreshed_cards: bool = False


class StockAnalysisRefreshRunData(BaseModel):
    thread_id: int
    refreshed_count: int
    skipped_count: int
    failed_count: int
    items: list[StockAnalysisRefreshItemData] = Field(default_factory=list)
    summary: str
    generated_at: datetime
    refreshed_context_ids: list[int] = Field(default_factory=list)
    skipped_context_ids: list[int] = Field(default_factory=list)
    failed_context_ids: list[int] = Field(default_factory=list)
    changed_contexts: list[StockAnalysisRefreshChangedContextData] = Field(
        default_factory=list
    )
