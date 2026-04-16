from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AShareDailySnapshotListItem(BaseModel):
    snapshot_date: str
    generated_at: datetime | None = None
    market_digest: dict[str, Any] = Field(default_factory=dict)
    attention_digest: dict[str, Any] = Field(default_factory=dict)
    brief_action_queue: list[str] = Field(default_factory=list)
    top_opportunity_count: int
    top_holding_action_count: int


class AShareDailySnapshotListData(BaseModel):
    generated_at: datetime
    count: int
    items: list[AShareDailySnapshotListItem] = Field(default_factory=list)


class AShareDailySnapshotDetailData(BaseModel):
    snapshot_date: str
    generated_at: datetime | None = None
    market_digest: dict[str, Any] = Field(default_factory=dict)
    attention_digest: dict[str, Any] = Field(default_factory=dict)
    top_alerts: list[dict[str, Any]] = Field(default_factory=list)
    top_opportunities: list[dict[str, Any]] = Field(default_factory=list)
    top_holdings_to_handle: list[dict[str, Any]] = Field(default_factory=list)
    top_holdings_stable: list[dict[str, Any]] = Field(default_factory=list)
    today_action_queue: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AShareDailySnapshotRefreshData(BaseModel):
    generated_at: datetime
    snapshot_date: str
    created_or_updated: str
    summary: str
    snapshot: AShareDailySnapshotDetailData
