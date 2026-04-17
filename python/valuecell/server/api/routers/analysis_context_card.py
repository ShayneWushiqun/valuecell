from fastapi import APIRouter, HTTPException

from ...services.assets.stock_analysis_workspace_service import (
    DEFAULT_USER_ID,
    get_stock_analysis_workspace_service,
)
from ..schemas import SuccessResponse
from ..schemas.analysis_context_card import (
    AnalysisContextCardCreateRequest,
    AnalysisContextCardItemData,
    AnalysisContextCardListData,
    AnalysisContextCardUpdateRequest,
)


def create_analysis_context_card_router() -> APIRouter:
    router = APIRouter(prefix="/stock-analysis", tags=["stock-analysis"])

    @router.get(
        "/threads/{thread_id}/contexts",
        response_model=SuccessResponse[AnalysisContextCardListData],
    )
    async def list_contexts(thread_id: int) -> SuccessResponse[AnalysisContextCardListData]:
        try:
            data = await get_stock_analysis_workspace_service().list_context_cards(
                user_id=DEFAULT_USER_ID,
                thread_id=thread_id,
            )
            if data is None:
                raise HTTPException(status_code=404, detail="Thread not found")
            return SuccessResponse.create(
                data=AnalysisContextCardListData(**data),
                msg="Analysis context cards retrieved successfully",
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving analysis context cards: {str(exc)}",
            ) from exc

    @router.post(
        "/threads/{thread_id}/contexts",
        response_model=SuccessResponse[AnalysisContextCardItemData],
    )
    async def create_context(
        thread_id: int,
        request: AnalysisContextCardCreateRequest,
    ) -> SuccessResponse[AnalysisContextCardItemData]:
        try:
            data = await get_stock_analysis_workspace_service().create_context_card(
                user_id=DEFAULT_USER_ID,
                thread_id=thread_id,
                context_type=request.context_type,
                title=request.title,
                subtitle=request.subtitle,
                ticker_refs_json=request.ticker_refs_json,
                theme_refs_json=request.theme_refs_json,
                summary=request.summary,
                snapshot_payload_json=request.snapshot_payload_json,
                source_module=request.source_module,
                source_ref=request.source_ref,
                staleness_hint=request.staleness_hint,
                is_pinned=request.is_pinned,
                mode=request.mode,
            )
            if data is None:
                raise HTTPException(status_code=404, detail="Thread not found")
            return SuccessResponse.create(
                data=AnalysisContextCardItemData(**data),
                msg="Analysis context card created successfully",
            )
        except HTTPException:
            raise
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error creating analysis context card: {str(exc)}",
            ) from exc

    @router.put(
        "/threads/{thread_id}/contexts/{context_id}",
        response_model=SuccessResponse[AnalysisContextCardItemData],
    )
    async def update_context(
        thread_id: int,
        context_id: int,
        request: AnalysisContextCardUpdateRequest,
    ) -> SuccessResponse[AnalysisContextCardItemData]:
        try:
            data = await get_stock_analysis_workspace_service().update_context_card(
                user_id=DEFAULT_USER_ID,
                thread_id=thread_id,
                context_id=context_id,
                title=request.title,
                subtitle=request.subtitle,
                summary=request.summary,
                staleness_hint=request.staleness_hint,
                is_pinned=request.is_pinned,
            )
            if data is None:
                raise HTTPException(status_code=404, detail="Context card not found")
            return SuccessResponse.create(
                data=AnalysisContextCardItemData(**data),
                msg="Analysis context card updated successfully",
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error updating analysis context card: {str(exc)}",
            ) from exc

    @router.delete(
        "/threads/{thread_id}/contexts/{context_id}",
        response_model=SuccessResponse[dict],
    )
    async def delete_context(
        thread_id: int,
        context_id: int,
    ) -> SuccessResponse[dict]:
        try:
            deleted = await get_stock_analysis_workspace_service().delete_context_card(
                user_id=DEFAULT_USER_ID,
                thread_id=thread_id,
                context_id=context_id,
            )
            if not deleted:
                raise HTTPException(status_code=404, detail="Context card not found")
            return SuccessResponse.create(
                data={"deleted": True},
                msg="Analysis context card deleted successfully",
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error deleting analysis context card: {str(exc)}",
            ) from exc

    return router
