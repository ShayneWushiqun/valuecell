from fastapi import APIRouter, HTTPException, Query

from ...services.assets.stock_analysis_workspace_service import (
    DEFAULT_USER_ID,
    get_stock_analysis_workspace_service,
)
from ..schemas import SuccessResponse
from ..schemas.analysis_context_card import StockAnalysisContextImportData
from ..schemas.stock_analysis_thread import (
    StockAnalysisContextImportRequest,
    StockAnalysisThreadCreateRequest,
    StockAnalysisThreadDuplicateData,
    StockAnalysisThreadItemData,
    StockAnalysisThreadListData,
    StockAnalysisThreadUpdateRequest,
    StockAnalysisWorkspaceOverviewData,
)


def create_stock_analysis_thread_router() -> APIRouter:
    router = APIRouter(prefix="/stock-analysis", tags=["stock-analysis"])

    @router.get("/threads", response_model=SuccessResponse[StockAnalysisThreadListData])
    async def list_threads() -> SuccessResponse[StockAnalysisThreadListData]:
        try:
            data = await get_stock_analysis_workspace_service().list_threads(
                user_id=DEFAULT_USER_ID
            )
            return SuccessResponse.create(
                data=StockAnalysisThreadListData(**data),
                msg="Stock analysis threads retrieved successfully",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving stock analysis threads: {str(exc)}",
            ) from exc

    @router.post("/threads", response_model=SuccessResponse[StockAnalysisThreadItemData])
    async def create_thread(
        request: StockAnalysisThreadCreateRequest,
    ) -> SuccessResponse[StockAnalysisThreadItemData]:
        try:
            data = await get_stock_analysis_workspace_service().create_thread(
                user_id=DEFAULT_USER_ID,
                title=request.title,
                focus_type=request.focus_type,
                ticker_refs_json=request.ticker_refs_json,
                theme_refs_json=request.theme_refs_json,
                compare_targets_json=request.compare_targets_json,
            )
            return SuccessResponse.create(
                data=StockAnalysisThreadItemData(**data),
                msg="Stock analysis thread created successfully",
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error creating stock analysis thread: {str(exc)}",
            ) from exc

    @router.put(
        "/threads/{thread_id}", response_model=SuccessResponse[StockAnalysisThreadItemData]
    )
    async def update_thread(
        thread_id: int,
        request: StockAnalysisThreadUpdateRequest,
    ) -> SuccessResponse[StockAnalysisThreadItemData]:
        try:
            data = await get_stock_analysis_workspace_service().update_thread(
                user_id=DEFAULT_USER_ID,
                thread_id=thread_id,
                title=request.title,
                focus_type=request.focus_type,
                ticker_refs_json=request.ticker_refs_json,
                theme_refs_json=request.theme_refs_json,
                compare_targets_json=request.compare_targets_json,
            )
            if data is None:
                raise HTTPException(status_code=404, detail="Thread not found")
            return SuccessResponse.create(
                data=StockAnalysisThreadItemData(**data),
                msg="Stock analysis thread updated successfully",
            )
        except HTTPException:
            raise
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error updating stock analysis thread: {str(exc)}",
            ) from exc

    @router.delete(
        "/threads/{thread_id}", response_model=SuccessResponse[StockAnalysisThreadItemData]
    )
    async def delete_thread(thread_id: int) -> SuccessResponse[StockAnalysisThreadItemData]:
        try:
            data = await get_stock_analysis_workspace_service().delete_thread(
                user_id=DEFAULT_USER_ID,
                thread_id=thread_id,
            )
            if data is None:
                raise HTTPException(status_code=404, detail="Thread not found")
            return SuccessResponse.create(
                data=StockAnalysisThreadItemData(**data),
                msg="Stock analysis thread archived successfully",
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error deleting stock analysis thread: {str(exc)}",
            ) from exc

    @router.post(
        "/threads/{thread_id}/duplicate",
        response_model=SuccessResponse[StockAnalysisThreadDuplicateData],
    )
    async def duplicate_thread(
        thread_id: int,
    ) -> SuccessResponse[StockAnalysisThreadDuplicateData]:
        try:
            data = await get_stock_analysis_workspace_service().duplicate_thread(
                user_id=DEFAULT_USER_ID,
                thread_id=thread_id,
            )
            if data is None:
                raise HTTPException(status_code=404, detail="Thread not found")
            return SuccessResponse.create(
                data=StockAnalysisThreadDuplicateData(**data),
                msg="Stock analysis thread duplicated successfully",
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error duplicating stock analysis thread: {str(exc)}",
            ) from exc

    @router.get(
        "/workspace/overview",
        response_model=SuccessResponse[StockAnalysisWorkspaceOverviewData],
    )
    async def get_workspace_overview(
        thread_id: int | None = Query(default=None),
    ) -> SuccessResponse[StockAnalysisWorkspaceOverviewData]:
        try:
            data = await get_stock_analysis_workspace_service().get_workspace_overview(
                user_id=DEFAULT_USER_ID,
                thread_id=thread_id,
            )
            return SuccessResponse.create(
                data=StockAnalysisWorkspaceOverviewData(**data),
                msg="Stock analysis workspace overview retrieved successfully",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving stock analysis workspace overview: {str(exc)}",
            ) from exc

    @router.post(
        "/context-import",
        response_model=SuccessResponse[StockAnalysisContextImportData],
    )
    async def import_context(
        request: StockAnalysisContextImportRequest,
    ) -> SuccessResponse[StockAnalysisContextImportData]:
        try:
            data = await get_stock_analysis_workspace_service().import_context(
                user_id=DEFAULT_USER_ID,
                source_module=request.source_module,
                source_ref=request.source_ref,
                target_thread_id=request.target_thread_id,
                create_new_thread=request.create_new_thread,
                mode=request.mode,
            )
            return SuccessResponse.create(
                data=StockAnalysisContextImportData(**data),
                msg="Stock analysis context imported successfully",
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error importing stock analysis context: {str(exc)}",
            ) from exc

    return router
