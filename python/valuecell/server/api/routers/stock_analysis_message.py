from fastapi import APIRouter, HTTPException

from ...services.assets.stock_analysis_message_service import (
    get_stock_analysis_message_service,
)
from ...services.assets.stock_analysis_workspace_service import DEFAULT_USER_ID
from ..schemas import SuccessResponse
from ..schemas.stock_analysis_message import (
    StockAnalysisMessageCreateData,
    StockAnalysisMessageCreateRequest,
    StockAnalysisMessageListData,
)


def create_stock_analysis_message_router() -> APIRouter:
    router = APIRouter(prefix="/stock-analysis", tags=["stock-analysis"])

    @router.get(
        "/threads/{thread_id}/messages",
        response_model=SuccessResponse[StockAnalysisMessageListData],
    )
    async def list_stock_analysis_messages(
        thread_id: int,
    ) -> SuccessResponse[StockAnalysisMessageListData]:
        try:
            data = await get_stock_analysis_message_service().list_messages(
                user_id=DEFAULT_USER_ID,
                thread_id=thread_id,
            )
            if data is None:
                raise HTTPException(status_code=404, detail="Thread not found")
            return SuccessResponse.create(
                data=StockAnalysisMessageListData(**data),
                msg="Stock analysis messages retrieved successfully",
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving stock analysis messages: {str(exc)}",
            ) from exc

    @router.post(
        "/threads/{thread_id}/messages",
        response_model=SuccessResponse[StockAnalysisMessageCreateData],
    )
    async def create_stock_analysis_message(
        thread_id: int,
        request: StockAnalysisMessageCreateRequest,
    ) -> SuccessResponse[StockAnalysisMessageCreateData]:
        try:
            data = await get_stock_analysis_message_service().send_message(
                user_id=DEFAULT_USER_ID,
                thread_id=thread_id,
                message=request.message,
                force_tooling=request.force_tooling,
            )
            if data is None:
                raise HTTPException(status_code=404, detail="Thread not found")
            return SuccessResponse.create(
                data=StockAnalysisMessageCreateData(**data.model_dump()),
                msg="Stock analysis message created successfully",
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error creating stock analysis message: {str(exc)}",
            ) from exc

    return router
