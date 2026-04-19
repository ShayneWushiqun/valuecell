from fastapi import APIRouter, HTTPException

from ...services.assets.stock_analysis_thread_compression_service import (
    get_stock_analysis_thread_compression_service,
)
from ...services.assets.stock_analysis_workspace_service import DEFAULT_USER_ID
from ..schemas import SuccessResponse
from ..schemas.stock_analysis_thread_compression import (
    StockAnalysisThreadCompressionActivateData,
    StockAnalysisThreadCompressionCaptureData,
    StockAnalysisThreadCompressionCaptureRequest,
    StockAnalysisThreadCompressionItemData,
    StockAnalysisThreadCompressionListData,
)


def create_stock_analysis_thread_compression_router() -> APIRouter:
    router = APIRouter(
        prefix="/stock-analysis",
        tags=["stock-analysis-thread-compression"],
    )

    @router.get(
        "/threads/{thread_id}/compressions",
        response_model=SuccessResponse[StockAnalysisThreadCompressionListData],
    )
    async def list_thread_compressions(
        thread_id: int,
    ) -> SuccessResponse[StockAnalysisThreadCompressionListData]:
        data = await get_stock_analysis_thread_compression_service().list_compressions(
            user_id=DEFAULT_USER_ID,
            thread_id=thread_id,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Thread not found")
        return SuccessResponse.create(
            data=StockAnalysisThreadCompressionListData(**data),
            msg="Stock analysis thread compressions retrieved successfully",
        )

    @router.get(
        "/threads/{thread_id}/compressions/{compression_id}",
        response_model=SuccessResponse[StockAnalysisThreadCompressionItemData],
    )
    async def get_thread_compression(
        thread_id: int,
        compression_id: int,
    ) -> SuccessResponse[StockAnalysisThreadCompressionItemData]:
        data = await get_stock_analysis_thread_compression_service().get_compression(
            user_id=DEFAULT_USER_ID,
            thread_id=thread_id,
            compression_id=compression_id,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Thread compression not found")
        return SuccessResponse.create(
            data=StockAnalysisThreadCompressionItemData(**data),
            msg="Stock analysis thread compression retrieved successfully",
        )

    @router.post(
        "/threads/{thread_id}/compressions/capture",
        response_model=SuccessResponse[StockAnalysisThreadCompressionCaptureData],
    )
    async def capture_thread_compression(
        thread_id: int,
        request: StockAnalysisThreadCompressionCaptureRequest,
    ) -> SuccessResponse[StockAnalysisThreadCompressionCaptureData]:
        data = await get_stock_analysis_thread_compression_service().capture_compression(
            user_id=DEFAULT_USER_ID,
            thread_id=thread_id,
            title=request.title,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Thread not found")
        return SuccessResponse.create(
            data=StockAnalysisThreadCompressionCaptureData(
                compression=StockAnalysisThreadCompressionItemData(**data)
            ),
            msg="Stock analysis thread compression captured successfully",
        )

    @router.post(
        "/threads/{thread_id}/compressions/{compression_id}/activate",
        response_model=SuccessResponse[StockAnalysisThreadCompressionActivateData],
    )
    async def activate_thread_compression(
        thread_id: int,
        compression_id: int,
    ) -> SuccessResponse[StockAnalysisThreadCompressionActivateData]:
        data = await get_stock_analysis_thread_compression_service().activate_compression(
            user_id=DEFAULT_USER_ID,
            thread_id=thread_id,
            compression_id=compression_id,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Thread compression not found")
        return SuccessResponse.create(
            data=StockAnalysisThreadCompressionActivateData(
                thread_id=thread_id,
                compression=StockAnalysisThreadCompressionItemData(**data),
            ),
            msg="Stock analysis thread compression activated successfully",
        )

    @router.post(
        "/threads/{thread_id}/compressions/{compression_id}/refresh",
        response_model=SuccessResponse[StockAnalysisThreadCompressionCaptureData],
    )
    async def refresh_thread_compression(
        thread_id: int,
        compression_id: int,
        request: StockAnalysisThreadCompressionCaptureRequest,
    ) -> SuccessResponse[StockAnalysisThreadCompressionCaptureData]:
        data = await get_stock_analysis_thread_compression_service().refresh_compression(
            user_id=DEFAULT_USER_ID,
            thread_id=thread_id,
            compression_id=compression_id,
            title=request.title,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Thread compression not found")
        return SuccessResponse.create(
            data=StockAnalysisThreadCompressionCaptureData(
                compression=StockAnalysisThreadCompressionItemData(**data)
            ),
            msg="Stock analysis thread compression refreshed successfully",
        )

    return router
