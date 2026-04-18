from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .stock_analysis_thread import StockAnalysisThreadDuplicateData


class StockAnalysisCompareTargetItemData(BaseModel):
    target_type: str
    ref: str
    label: str
    source_module: str
    source_ref: str
    role: str = "secondary"
    order: int = 0


class StockAnalysisCompareTargetListData(BaseModel):
    thread_id: int
    focus_type: str
    compare_targets: list[StockAnalysisCompareTargetItemData] = Field(default_factory=list)
    compared_tickers: list[str] = Field(default_factory=list)
    compared_themes: list[str] = Field(default_factory=list)
    comparison_mode: bool = False


class StockAnalysisCompareTargetUpdateRequest(BaseModel):
    compare_targets: list[dict[str, Any]] = Field(default_factory=list)


class StockAnalysisThreadForkRequest(BaseModel):
    title: str | None = None
    selected_context_ids: list[int] = Field(default_factory=list)
    include_compare_targets: bool = True
    pin_imported_contexts: bool = False
    seed_from_active_memory: bool = False
    focus_type_override: str | None = None


class StockAnalysisThreadForkData(StockAnalysisThreadDuplicateData):
    context_count: int = 0
