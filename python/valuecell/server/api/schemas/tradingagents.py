from datetime import date, datetime
from typing import List, Literal

from pydantic import BaseModel, Field, field_validator

from .base import SuccessResponse

TRADING_AGENTS_ANALYSTS = Literal["market", "social", "news", "fundamentals"]


class TradingAgentsRunRequest(BaseModel):
    symbol: str = Field(..., description="Ticker or exchange-qualified symbol")
    trade_date: date = Field(..., description="Analysis date")
    provider: str = Field(..., description="Configured model provider")
    deep_model: str = Field(..., description="Model used for deep reasoning")
    quick_model: str = Field(..., description="Model used for quick reasoning")
    output_language: str = Field(default="Chinese", description="Report language")
    analysts: List[TRADING_AGENTS_ANALYSTS] = Field(
        default_factory=lambda: ["market", "social", "news", "fundamentals"],
        description="Enabled analyst modules",
    )
    debug: bool = Field(default=False, description="Whether to enable debug mode")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("symbol is required")
        return normalized

    @field_validator("provider", "deep_model", "quick_model", "output_language")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("field is required")
        return normalized

    @field_validator("analysts")
    @classmethod
    def validate_analysts(cls, value: List[TRADING_AGENTS_ANALYSTS]) -> List[str]:
        if not value:
            raise ValueError("at least one analyst is required")
        deduped = list(dict.fromkeys(value))
        return deduped


class TradingAgentsSummaryData(BaseModel):
    technical: str = Field(..., description="Technical summary")
    fundamentals: str = Field(..., description="Fundamentals summary")
    sentiment: str = Field(..., description="Sentiment summary")
    capital_flow: str = Field(..., description="Capital flow or execution summary")
    final_decision: str = Field(..., description="Final decision summary")


class TradingAgentsReportData(BaseModel):
    key: str = Field(..., description="Stable report key")
    title: str = Field(..., description="Display title")
    content: str = Field(..., description="Markdown report content")


class TradingAgentsStepLogData(BaseModel):
    stage: str = Field(..., description="Stable stage identifier")
    title: str = Field(..., description="Display title")
    message: str = Field(..., description="User-facing progress message")
    level: Literal["info", "running", "completed", "warning", "error"] = Field(
        ...,
        description="Progress severity level",
    )
    progress_percent: int | None = Field(
        default=None,
        description="Approximate completion percentage",
    )
    created_at: datetime = Field(..., description="Progress event timestamp")


class TradingAgentsRunData(BaseModel):
    run_id: str = Field(..., description="Generated run identifier")
    status: Literal["queued", "running", "succeeded", "failed"] = Field(
        ...,
        description="Run lifecycle status",
    )
    symbol: str = Field(..., description="Ticker or exchange-qualified symbol")
    trade_date: date = Field(..., description="Analysis date")
    provider: str = Field(..., description="Configured provider")
    deep_model: str = Field(..., description="Configured deep model")
    quick_model: str = Field(..., description="Configured quick model")
    output_language: str = Field(..., description="Output language")
    analysts: List[str] = Field(..., description="Enabled analysts")
    debug: bool = Field(..., description="Debug flag")
    progress_stage: str | None = Field(None, description="Current progress stage")
    progress_message: str | None = Field(None, description="Current progress message")
    progress_percent: int | None = Field(
        None,
        description="Approximate completion percentage",
    )
    decision_signal: str | None = Field(None, description="Normalized decision signal")
    summary: TradingAgentsSummaryData | None = Field(
        None,
        description="Workspace summary",
    )
    reports: List[TradingAgentsReportData] = Field(
        default_factory=list,
        description="Detailed markdown reports",
    )
    step_logs: List[TradingAgentsStepLogData] = Field(
        default_factory=list,
        description="Progress timeline entries",
    )
    error_message: str | None = Field(None, description="Run error message")
    started_at: datetime | None = Field(None, description="Actual start timestamp")
    completed_at: datetime | None = Field(None, description="Completion timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class TradingAgentsRunListData(BaseModel):
    runs: List[TradingAgentsRunData] = Field(..., description="Recent run records")
    total: int = Field(..., description="Total run count")
    running_count: int = Field(..., description="Number of active runs")


TradingAgentsRunResponse = SuccessResponse[TradingAgentsRunData]
TradingAgentsRunListResponse = SuccessResponse[TradingAgentsRunListData]
