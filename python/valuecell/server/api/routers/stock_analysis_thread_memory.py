from fastapi import APIRouter, HTTPException

from ...services.assets.stock_analysis_thread_memory_service import (
    get_stock_analysis_thread_memory_service,
)
from ...services.assets.stock_analysis_workspace_service import DEFAULT_USER_ID
from ..schemas import SuccessResponse
from ..schemas.stock_analysis_thread_memory import (
    StockAnalysisThreadMemoryActivateData,
    StockAnalysisThreadMemoryCaptureData,
    StockAnalysisThreadMemoryCaptureRequest,
    StockAnalysisThreadMemoryItemData,
    StockAnalysisThreadMemoryListData,
)


def create_stock_analysis_thread_memory_router() -> APIRouter:
    router = APIRouter(prefix="/stock-analysis", tags=["stock-analysis-thread-memory"])

    @router.get(
        "/threads/{thread_id}/memories",
        response_model=SuccessResponse[StockAnalysisThreadMemoryListData],
    )
    async def list_thread_memories(
        thread_id: int,
    ) -> SuccessResponse[StockAnalysisThreadMemoryListData]:
        data = await get_stock_analysis_thread_memory_service().list_memories(
            user_id=DEFAULT_USER_ID,
            thread_id=thread_id,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Thread not found")
        return SuccessResponse.create(
            data=StockAnalysisThreadMemoryListData(**data),
            msg="Stock analysis thread memories retrieved successfully",
        )

    @router.get(
        "/threads/{thread_id}/memories/{memory_id}",
        response_model=SuccessResponse[StockAnalysisThreadMemoryItemData],
    )
    async def get_thread_memory(
        thread_id: int,
        memory_id: int,
    ) -> SuccessResponse[StockAnalysisThreadMemoryItemData]:
        data = await get_stock_analysis_thread_memory_service().get_memory(
            user_id=DEFAULT_USER_ID,
            thread_id=thread_id,
            memory_id=memory_id,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Thread memory not found")
        return SuccessResponse.create(
            data=StockAnalysisThreadMemoryItemData(**data),
            msg="Stock analysis thread memory retrieved successfully",
        )

    @router.post(
        "/threads/{thread_id}/memories/capture",
        response_model=SuccessResponse[StockAnalysisThreadMemoryCaptureData],
    )
    async def capture_thread_memory(
        thread_id: int,
        request: StockAnalysisThreadMemoryCaptureRequest,
    ) -> SuccessResponse[StockAnalysisThreadMemoryCaptureData]:
        data = await get_stock_analysis_thread_memory_service().capture_memory(
            user_id=DEFAULT_USER_ID,
            thread_id=thread_id,
            title=request.title,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Thread not found")
        return SuccessResponse.create(
            data=StockAnalysisThreadMemoryCaptureData(
                memory=StockAnalysisThreadMemoryItemData(**data)
            ),
            msg="Stock analysis thread memory captured successfully",
        )

    @router.post(
        "/threads/{thread_id}/memories/{memory_id}/activate",
        response_model=SuccessResponse[StockAnalysisThreadMemoryActivateData],
    )
    async def activate_thread_memory(
        thread_id: int,
        memory_id: int,
    ) -> SuccessResponse[StockAnalysisThreadMemoryActivateData]:
        data = await get_stock_analysis_thread_memory_service().activate_memory(
            user_id=DEFAULT_USER_ID,
            thread_id=thread_id,
            memory_id=memory_id,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Thread memory not found")
        return SuccessResponse.create(
            data=StockAnalysisThreadMemoryActivateData(
                thread_id=thread_id,
                memory=StockAnalysisThreadMemoryItemData(**data),
            ),
            msg="Stock analysis thread memory activated successfully",
        )

    @router.post(
        "/threads/{thread_id}/memories/{memory_id}/refresh",
        response_model=SuccessResponse[StockAnalysisThreadMemoryCaptureData],
    )
    async def refresh_thread_memory(
        thread_id: int,
        memory_id: int,
        request: StockAnalysisThreadMemoryCaptureRequest,
    ) -> SuccessResponse[StockAnalysisThreadMemoryCaptureData]:
        data = await get_stock_analysis_thread_memory_service().refresh_memory(
            user_id=DEFAULT_USER_ID,
            thread_id=thread_id,
            memory_id=memory_id,
            title=request.title,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Thread memory not found")
        return SuccessResponse.create(
            data=StockAnalysisThreadMemoryCaptureData(
                memory=StockAnalysisThreadMemoryItemData(**data)
            ),
            msg="Stock analysis thread memory refreshed successfully",
        )

    return router
