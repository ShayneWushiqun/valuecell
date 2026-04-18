from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class StockAnalysisThreadMemoryItemData(BaseModel):
    memory_id: int
    thread_id: int
    user_id: str
    title: str
    summary: str
    stance: str
    confidence: float
    time_horizon: str
    focus_tickers_json: list[str] = Field(default_factory=list)
    focus_themes_json: list[str] = Field(default_factory=list)
    compared_tickers_json: list[str] = Field(default_factory=list)
    support_points_json: list[str] = Field(default_factory=list)
    opposing_points_json: list[str] = Field(default_factory=list)
    risk_points_json: list[str] = Field(default_factory=list)
    key_uncertainties_json: list[str] = Field(default_factory=list)
    invalidation_conditions_json: list[str] = Field(default_factory=list)
    next_questions_json: list[str] = Field(default_factory=list)
    next_data_to_check_json: list[str] = Field(default_factory=list)
    linked_context_ids_json: list[int] = Field(default_factory=list)
    linked_message_ids_json: list[str] = Field(default_factory=list)
    linked_compare_targets_json: list[dict[str, Any]] = Field(default_factory=list)
    source_snapshot_json: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = False
    version: int = 0
    linked_context_count: int = 0
    linked_message_count: int = 0
    compare_target_count: int = 0
    created_at: datetime
    updated_at: datetime


class StockAnalysisThreadMemoryListData(BaseModel):
    thread_id: int
    active_memory: StockAnalysisThreadMemoryItemData | None = None
    items: list[StockAnalysisThreadMemoryItemData] = Field(default_factory=list)
    count: int
    generated_at: datetime


class StockAnalysisThreadMemoryCaptureRequest(BaseModel):
    title: str | None = None


class StockAnalysisThreadMemoryCaptureData(BaseModel):
    memory: StockAnalysisThreadMemoryItemData


class StockAnalysisThreadMemoryActivateData(BaseModel):
    thread_id: int
    memory: StockAnalysisThreadMemoryItemData

