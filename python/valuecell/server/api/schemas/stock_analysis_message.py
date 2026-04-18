from __future__ import annotations

from pydantic import BaseModel, Field


class StockAnalysisMessageItemData(BaseModel):
    item_id: str
    role: str
    event: str | None = None
    conversation_id: str | None = None
    content: str
    answer_basis: str = "context_only"
    used_context_ids: list[int] = Field(default_factory=list)
    missing_context_hints: list[str] = Field(default_factory=list)


class StockAnalysisMessageListData(BaseModel):
    conversation_id: str
    thread_id: int
    items: list[StockAnalysisMessageItemData] = Field(default_factory=list)
    count: int


class StockAnalysisMessageCreateRequest(BaseModel):
    message: str


class StockAnalysisMessageCreateData(BaseModel):
    conversation_id: str
    thread_id: int
    answer_basis: str = "context_only"
    used_context_ids: list[int] = Field(default_factory=list)
    missing_context_hints: list[str] = Field(default_factory=list)
    user_message: StockAnalysisMessageItemData
    assistant_message: StockAnalysisMessageItemData
