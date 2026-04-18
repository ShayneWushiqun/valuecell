from fastapi import APIRouter, HTTPException

from ...services.assets.stock_analysis_compare_service import (
    get_stock_analysis_compare_service,
)
from ...services.assets.stock_analysis_workspace_service import (
    DEFAULT_USER_ID,
    get_stock_analysis_workspace_service,
)
from ..schemas import SuccessResponse
from ..schemas.stock_analysis_compare import (
    StockAnalysisCompareTargetListData,
    StockAnalysisCompareTargetUpdateRequest,
    StockAnalysisThreadForkData,
    StockAnalysisThreadForkRequest,
)


def create_stock_analysis_compare_router() -> APIRouter:
    router = APIRouter(prefix="/stock-analysis", tags=["stock-analysis-compare"])

    @router.get(
        "/threads/{thread_id}/compare-targets",
        response_model=SuccessResponse[StockAnalysisCompareTargetListData],
    )
    async def list_compare_targets(thread_id: int) -> SuccessResponse[StockAnalysisCompareTargetListData]:
        data = await get_stock_analysis_compare_service().list_compare_targets(
            user_id=DEFAULT_USER_ID,
            thread_id=thread_id,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Thread not found")
        return SuccessResponse.create(
            data=StockAnalysisCompareTargetListData(**data),
            msg="Stock analysis compare targets retrieved successfully",
        )

    @router.put(
        "/threads/{thread_id}/compare-targets",
        response_model=SuccessResponse[StockAnalysisCompareTargetListData],
    )
    async def update_compare_targets(
        thread_id: int,
        request: StockAnalysisCompareTargetUpdateRequest,
    ) -> SuccessResponse[StockAnalysisCompareTargetListData]:
        data = await get_stock_analysis_compare_service().update_compare_targets(
            user_id=DEFAULT_USER_ID,
            thread_id=thread_id,
            compare_targets=request.compare_targets,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Thread not found")
        return SuccessResponse.create(
            data=StockAnalysisCompareTargetListData(**data),
            msg="Stock analysis compare targets updated successfully",
        )

    @router.post(
        "/threads/{thread_id}/fork",
        response_model=SuccessResponse[StockAnalysisThreadForkData],
    )
    async def fork_thread(
        thread_id: int,
        request: StockAnalysisThreadForkRequest,
    ) -> SuccessResponse[StockAnalysisThreadForkData]:
        try:
            data = await get_stock_analysis_workspace_service().fork_thread(
                user_id=DEFAULT_USER_ID,
                thread_id=thread_id,
                title=request.title,
                selected_context_ids=request.selected_context_ids,
                include_compare_targets=request.include_compare_targets,
                pin_imported_contexts=request.pin_imported_contexts,
                seed_from_active_memory=request.seed_from_active_memory,
                focus_type_override=request.focus_type_override,
            )
            if data is None:
                raise HTTPException(status_code=404, detail="Thread not found")
            return SuccessResponse.create(
                data=StockAnalysisThreadForkData(**data),
                msg="Stock analysis thread forked successfully",
            )
        except HTTPException:
            raise
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router
