from fastapi import APIRouter, HTTPException, Path, Query

from ...services.assets.decision_context_window_service import (
    get_decision_context_window_service,
)
from ..schemas import SuccessResponse
from ..schemas.decision_context_window import (
    DecisionContextWindowItemData,
    DecisionContextWindowListData,
    DecisionContextWindowRefreshRequest,
)

DEFAULT_USER_ID = "default_user"


def create_decision_context_window_router() -> APIRouter:
    router = APIRouter(prefix="/decision-context-windows", tags=["decision-context-windows"])
    decision_context_window_service = get_decision_context_window_service()

    @router.get("", response_model=SuccessResponse[DecisionContextWindowListData])
    async def list_decision_context_windows(
        ticker: str | None = Query(None),
        window_size: int | None = Query(None, ge=1),
        limit: int = Query(100, ge=1, le=500),
    ) -> SuccessResponse[DecisionContextWindowListData]:
        try:
            data = decision_context_window_service.list_windows(
                user_id=DEFAULT_USER_ID,
                ticker=ticker,
                window_size=window_size,
                limit=limit,
            )
            return SuccessResponse.create(
                data=DecisionContextWindowListData(**data),
                msg="Decision context windows retrieved successfully",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving decision context windows: {str(exc)}",
            ) from exc

    @router.get("/{window_id}", response_model=SuccessResponse[DecisionContextWindowItemData])
    async def get_decision_context_window_detail(
        window_id: int = Path(..., ge=1, description="Window ID"),
    ) -> SuccessResponse[DecisionContextWindowItemData]:
        try:
            data = decision_context_window_service.get_window_detail(
                user_id=DEFAULT_USER_ID,
                window_id=window_id,
            )
            if data is None:
                raise HTTPException(status_code=404, detail="Decision context window not found")
            return SuccessResponse.create(
                data=DecisionContextWindowItemData(**data),
                msg="Decision context window retrieved successfully",
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving decision context window: {str(exc)}",
            ) from exc

    @router.post("/refresh", response_model=SuccessResponse[DecisionContextWindowListData])
    async def refresh_decision_context_windows(
        request: DecisionContextWindowRefreshRequest,
    ) -> SuccessResponse[DecisionContextWindowListData]:
        try:
            data = decision_context_window_service.refresh_windows(
                user_id=DEFAULT_USER_ID,
                ticker=request.ticker,
            )
            return SuccessResponse.create(
                data=DecisionContextWindowListData(**data),
                msg="Decision context windows refreshed successfully",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error refreshing decision context windows: {str(exc)}",
            ) from exc

    return router
