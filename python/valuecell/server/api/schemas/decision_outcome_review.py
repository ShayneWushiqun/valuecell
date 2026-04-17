from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


ALLOWED_OUTCOME_STATUS = {"有效", "部分有效", "失效", "仍在观察", "数据不足"}
ALLOWED_REVIEW_HORIZONS = {5, 10, 20}


class DecisionOutcomeReviewItemData(BaseModel):
    review_id: int
    record_id: int
    ticker: str
    display_name: str
    action: str
    lifecycle_stage: str | None = None
    record_date: str
    review_date: str
    review_horizon_days: int
    available: bool
    outcome_status: str
    outcome_score: int
    price_change_pct: float | None = None
    max_favorable_excursion_pct: float | None = None
    max_adverse_excursion_pct: float | None = None
    entry_reference_price: float | None = None
    exit_reference_price: float | None = None
    summary: str
    what_happened: str
    what_was_right: str
    what_was_wrong: str
    followup_view: str
    risk_after_signal: str
    context_consistency: str
    linked_context_window_id: int | None = None
    linked_event_ids_json: list[int] = Field(default_factory=list)
    empty_message: str | None = None

    @field_validator("outcome_status")
    @classmethod
    def validate_outcome_status(cls, value: str) -> str:
        if value not in ALLOWED_OUTCOME_STATUS:
            raise ValueError("Unsupported outcome status")
        return value

    @field_validator("review_horizon_days")
    @classmethod
    def validate_review_horizon_days(cls, value: int) -> int:
        if value not in ALLOWED_REVIEW_HORIZONS:
            raise ValueError("Unsupported review horizon")
        return value


class DecisionOutcomeReviewListData(BaseModel):
    generated_at: datetime
    items: list[DecisionOutcomeReviewItemData] = Field(default_factory=list)
    count: int


class DecisionOutcomeReviewCaptureRequest(BaseModel):
    record_id: int
    review_horizon_days: int = 10
    review_date: str | None = None

    @field_validator("review_horizon_days")
    @classmethod
    def validate_review_horizon_days(cls, value: int) -> int:
        if value not in ALLOWED_REVIEW_HORIZONS:
            raise ValueError("Unsupported review horizon")
        return value


class DecisionOutcomeReviewRefreshRequest(BaseModel):
    review_horizon_days_list: list[int] = Field(default_factory=lambda: [5, 10, 20])
    lookback_days: int = 60
    limit_records: int = 30
    review_date: str | None = None

    @field_validator("review_horizon_days_list")
    @classmethod
    def validate_review_horizon_days_list(cls, value: list[int]) -> list[int]:
        normalized: list[int] = []
        for item in value:
            if item not in ALLOWED_REVIEW_HORIZONS:
                raise ValueError("Unsupported review horizon")
            if item not in normalized:
                normalized.append(item)
        return normalized
