from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator

from .stock_analysis_thread import StockAnalysisThreadItemData


ALLOWED_CONTEXT_TYPES = {
    "tradingagents_run",
    "holding",
    "opportunity",
    "watchlist",
    "theme",
    "alert",
    "ticker",
}
ALLOWED_CONTEXT_MODES = {"append", "replace"}


class AnalysisContextCardItemData(BaseModel):
    context_id: int
    thread_id: int
    user_id: str
    context_type: str
    title: str
    subtitle: str | None = None
    ticker_refs_json: list[str] = Field(default_factory=list)
    theme_refs_json: list[str] = Field(default_factory=list)
    summary: str
    snapshot_payload_json: dict[str, Any] = Field(default_factory=dict)
    source_module: str
    source_ref: str | None = None
    staleness_hint: str | None = None
    is_pinned: bool = False
    created_at: datetime
    updated_at: datetime


class AnalysisContextCardListData(BaseModel):
    generated_at: datetime
    items: list[AnalysisContextCardItemData] = Field(default_factory=list)
    count: int


class AnalysisContextCardCreateRequest(BaseModel):
    context_type: str
    title: str
    subtitle: str | None = None
    ticker_refs_json: list[str] = Field(default_factory=list)
    theme_refs_json: list[str] = Field(default_factory=list)
    summary: str
    snapshot_payload_json: dict[str, Any] = Field(default_factory=dict)
    source_module: str
    source_ref: str | None = None
    staleness_hint: str | None = None
    is_pinned: bool = False
    mode: str = "append"

    @field_validator("context_type")
    @classmethod
    def validate_context_type(cls, value: str) -> str:
        if value not in ALLOWED_CONTEXT_TYPES:
            raise ValueError("Unsupported context_type")
        return value

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        if value not in ALLOWED_CONTEXT_MODES:
            raise ValueError("Unsupported mode")
        return value


class AnalysisContextCardUpdateRequest(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    summary: str | None = None
    staleness_hint: str | None = None
    is_pinned: bool | None = None


class StockAnalysisContextImportData(BaseModel):
    thread: StockAnalysisThreadItemData
    context_card: AnalysisContextCardItemData
    contexts: list[AnalysisContextCardItemData] = Field(default_factory=list)
