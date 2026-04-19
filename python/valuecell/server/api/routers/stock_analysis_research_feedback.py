from fastapi import APIRouter, HTTPException

from ...services.assets.stock_analysis_research_feedback_service import (
    get_stock_analysis_research_feedback_service,
)
from ...services.assets.stock_analysis_workspace_service import DEFAULT_USER_ID
from ..schemas import SuccessResponse
from ..schemas.stock_analysis_research_feedback import (
    StockAnalysisResearchFeedbackCaptureRequest,
    StockAnalysisResearchFeedbackItemData,
    StockAnalysisResearchFeedbackListData,
    StockAnalysisResearchFeedbackMutationData,
    StockAnalysisResearchFeedbackRefreshRequest,
)


def create_stock_analysis_research_feedback_router() -> APIRouter:
    router = APIRouter(
        prefix="/stock-analysis",
        tags=["stock-analysis-research-feedback"],
    )

    @router.get(
        "/threads/{thread_id}/research-feedback",
        response_model=SuccessResponse[StockAnalysisResearchFeedbackListData],
    )
    async def list_thread_research_feedback(
        thread_id: int,
    ) -> SuccessResponse[StockAnalysisResearchFeedbackListData]:
        data = await get_stock_analysis_research_feedback_service().list_feedbacks(
            user_id=DEFAULT_USER_ID,
            thread_id=thread_id,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Thread not found")
        return SuccessResponse.create(
            data=StockAnalysisResearchFeedbackListData(**data),
            msg="Stock analysis research feedback retrieved successfully",
        )

    @router.get(
        "/threads/{thread_id}/research-feedback/{feedback_id}",
        response_model=SuccessResponse[StockAnalysisResearchFeedbackItemData],
    )
    async def get_thread_research_feedback(
        thread_id: int,
        feedback_id: int,
    ) -> SuccessResponse[StockAnalysisResearchFeedbackItemData]:
        data = await get_stock_analysis_research_feedback_service().get_feedback(
            user_id=DEFAULT_USER_ID,
            thread_id=thread_id,
            feedback_id=feedback_id,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Research feedback not found")
        return SuccessResponse.create(
            data=StockAnalysisResearchFeedbackItemData(**data),
            msg="Stock analysis research feedback retrieved successfully",
        )

    @router.post(
        "/threads/{thread_id}/research-feedback/capture",
        response_model=SuccessResponse[StockAnalysisResearchFeedbackMutationData],
    )
    async def capture_thread_research_feedback(
        thread_id: int,
        request: StockAnalysisResearchFeedbackCaptureRequest,
    ) -> SuccessResponse[StockAnalysisResearchFeedbackMutationData]:
        try:
            data = await get_stock_analysis_research_feedback_service().capture_feedback(
                user_id=DEFAULT_USER_ID,
                thread_id=thread_id,
                anchor_message_id=request.anchor_message_id,
                related_task_ids=request.related_task_ids,
                related_tickers=request.related_tickers,
                title=request.title,
                note=request.note,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if data is None:
            raise HTTPException(status_code=404, detail="Thread not found")
        return SuccessResponse.create(
            data=StockAnalysisResearchFeedbackMutationData(
                thread_id=thread_id,
                feedback=StockAnalysisResearchFeedbackItemData(**data),
            ),
            msg="Stock analysis research feedback captured successfully",
        )

    @router.post(
        "/threads/{thread_id}/research-feedback/{feedback_id}/refresh",
        response_model=SuccessResponse[StockAnalysisResearchFeedbackMutationData],
    )
    async def refresh_thread_research_feedback(
        thread_id: int,
        feedback_id: int,
        request: StockAnalysisResearchFeedbackRefreshRequest,
    ) -> SuccessResponse[StockAnalysisResearchFeedbackMutationData]:
        data = await get_stock_analysis_research_feedback_service().refresh_feedback(
            user_id=DEFAULT_USER_ID,
            thread_id=thread_id,
            feedback_id=feedback_id,
            title=request.title,
            note=request.note,
            related_task_ids=request.related_task_ids,
            related_tickers=request.related_tickers,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Research feedback not found")
        return SuccessResponse.create(
            data=StockAnalysisResearchFeedbackMutationData(
                thread_id=thread_id,
                feedback=StockAnalysisResearchFeedbackItemData(**data),
            ),
            msg="Stock analysis research feedback refreshed successfully",
        )

    return router
