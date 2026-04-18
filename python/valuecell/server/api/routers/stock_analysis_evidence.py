from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..schemas import SuccessResponse
from ..schemas.analysis_context_card import AnalysisContextCardItemData
from ..schemas.stock_analysis_evidence import (
    StockAnalysisEvidenceSaveData,
    StockAnalysisEvidenceSaveRequest,
)
from ...services.assets.stock_analysis_message_service import (
    DEFAULT_USER_ID,
    get_stock_analysis_message_service,
)


def create_stock_analysis_evidence_router() -> APIRouter:
    router = APIRouter(prefix="/stock-analysis", tags=["stock-analysis-evidence"])

    @router.post(
        "/threads/{thread_id}/messages/{message_id}/save-evidence",
        response_model=SuccessResponse[StockAnalysisEvidenceSaveData],
    )
    async def save_stock_analysis_evidence(
        thread_id: int,
        message_id: str,
        request: StockAnalysisEvidenceSaveRequest,
    ) -> SuccessResponse[StockAnalysisEvidenceSaveData]:
        context_card = await get_stock_analysis_message_service().save_temporary_evidence_as_context(
            user_id=DEFAULT_USER_ID,
            thread_id=thread_id,
            message_id=message_id,
            evidence_index=request.evidence_index,
            pin=request.pin,
            custom_title=request.title,
        )
        if context_card is None:
            raise HTTPException(status_code=404, detail="Evidence block not found")
        return SuccessResponse.create(
            data=StockAnalysisEvidenceSaveData(
                thread_id=thread_id,
                message_id=message_id,
                evidence_index=request.evidence_index,
                context_card=AnalysisContextCardItemData.model_validate(context_card),
            ),
            msg="Stock analysis evidence saved successfully",
        )

    return router
