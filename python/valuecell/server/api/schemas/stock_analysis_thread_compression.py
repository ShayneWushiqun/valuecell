from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class StockAnalysisThreadCompressionItemData(BaseModel):
    compression_id: int
    thread_id: int
    user_id: str
    conversation_id: str
    title: str
    summary: str
    current_focus: str
    covered_until_message_id: str | None = None
    covered_message_count: int = 0
    source_message_ids_json: list[str] = Field(default_factory=list)
    resolved_topics_json: list[str] = Field(default_factory=list)
    open_questions_json: list[str] = Field(default_factory=list)
    recent_compare_notes_json: list[str] = Field(default_factory=list)
    recent_refresh_notes_json: list[str] = Field(default_factory=list)
    recent_tooling_notes_json: list[str] = Field(default_factory=list)
    recent_evidence_notes_json: list[str] = Field(default_factory=list)
    active_memory_id: int | None = None
    focus_tickers_json: list[str] = Field(default_factory=list)
    focus_themes_json: list[str] = Field(default_factory=list)
    compared_tickers_json: list[str] = Field(default_factory=list)
    next_questions_json: list[str] = Field(default_factory=list)
    compression_reason: str
    is_active: bool = False
    version: int = 0
    source_message_count: int = 0
    covered_message_range_text: str | None = None
    created_at: datetime
    updated_at: datetime


class StockAnalysisThreadCompressionListData(BaseModel):
    thread_id: int
    active_compression: StockAnalysisThreadCompressionItemData | None = None
    items: list[StockAnalysisThreadCompressionItemData] = Field(default_factory=list)
    count: int
    compression_recommended: bool = False
    compression_reason: str | None = None
    uncompressed_message_count: int = 0
    estimated_history_size: int = 0
    active_compression_stale: bool = False
    generated_at: datetime


class StockAnalysisThreadCompressionCaptureRequest(BaseModel):
    title: str | None = None


class StockAnalysisThreadCompressionCaptureData(BaseModel):
    compression: StockAnalysisThreadCompressionItemData


class StockAnalysisThreadCompressionActivateData(BaseModel):
    thread_id: int
    compression: StockAnalysisThreadCompressionItemData
