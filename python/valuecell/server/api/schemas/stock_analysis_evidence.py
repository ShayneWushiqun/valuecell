from __future__ import annotations

from pydantic import BaseModel, Field

from .analysis_context_card import AnalysisContextCardItemData


class StockAnalysisEvidenceSaveRequest(BaseModel):
    evidence_index: int = Field(ge=0)
    pin: bool = False
    title: str | None = None


class StockAnalysisEvidenceSaveData(BaseModel):
    thread_id: int
    message_id: str
    evidence_index: int
    context_card: AnalysisContextCardItemData
