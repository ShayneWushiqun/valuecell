from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DecisionRecordItemData(BaseModel):
    record_id: int
    generated_at: datetime
    record_date: str
    ticker: str
    display_name: str
    holding_id: int
    lifecycle_stage: str
    action: str
    confidence: int
    summary: str
    thesis: str
    evidence: list[str] = Field(default_factory=list)
    disagreement: list[str] = Field(default_factory=list)
    invalid_conditions: list[str] = Field(default_factory=list)
    risk_controls: list[str] = Field(default_factory=list)
    theme_name: str | None = None
    role_label: str | None = None
    tradeability_state: str | None = None
    expectation_state: str | None = None
    source: str
    context_window_id: int | None = None
    linked_event_ids_json: list[int] = Field(default_factory=list)
    context_snapshot_json: dict[str, Any] = Field(default_factory=dict)
    outcome_status: str
    review_note: str | None = None


class DecisionRecordListData(BaseModel):
    generated_at: datetime
    items: list[DecisionRecordItemData] = Field(default_factory=list)
    count: int


class DecisionRecordCaptureData(DecisionRecordListData):
    record_date: str
