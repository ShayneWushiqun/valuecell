from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

ALLOWED_FOCUS_TYPES = {
    "ticker",
    "theme",
    "comparison",
    "holding",
    "tradingagents_followup",
    "mixed",
}
ALLOWED_IMPORT_MODES = {"append", "replace"}


class StockAnalysisThreadItemData(BaseModel):
    thread_id: int
    user_id: str
    title: str
    focus_type: str
    ticker_refs_json: list[str] = Field(default_factory=list)
    theme_refs_json: list[str] = Field(default_factory=list)
    conversation_id: str
    context_count: int = 0
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None


class StockAnalysisThreadListData(BaseModel):
    generated_at: datetime
    items: list[StockAnalysisThreadItemData] = Field(default_factory=list)
    count: int


class StockAnalysisThreadCreateRequest(BaseModel):
    title: str
    focus_type: str = "mixed"
    ticker_refs_json: list[str] = Field(default_factory=list)
    theme_refs_json: list[str] = Field(default_factory=list)

    @field_validator("focus_type")
    @classmethod
    def validate_focus_type(cls, value: str) -> str:
        if value not in ALLOWED_FOCUS_TYPES:
            raise ValueError("Unsupported focus_type")
        return value


class StockAnalysisThreadUpdateRequest(BaseModel):
    title: str | None = None
    focus_type: str | None = None
    ticker_refs_json: list[str] | None = None
    theme_refs_json: list[str] | None = None

    @field_validator("focus_type")
    @classmethod
    def validate_optional_focus_type(cls, value: str | None) -> str | None:
        if value is not None and value not in ALLOWED_FOCUS_TYPES:
            raise ValueError("Unsupported focus_type")
        return value


class StockAnalysisThreadDuplicateData(BaseModel):
    thread: StockAnalysisThreadItemData
    contexts: list[dict[str, Any]] = Field(default_factory=list)


class StockAnalysisWorkspaceOverviewData(BaseModel):
    generated_at: datetime
    threads: list[StockAnalysisThreadItemData] = Field(default_factory=list)
    current_thread: StockAnalysisThreadItemData | None = None
    context_count: int
    available: bool
    empty_message: str | None = None


class StockAnalysisContextImportRequest(BaseModel):
    source_module: str
    source_ref: str
    target_thread_id: int | None = None
    create_new_thread: bool = False
    mode: str = "append"

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        if value not in ALLOWED_IMPORT_MODES:
            raise ValueError("Unsupported mode")
        return value
