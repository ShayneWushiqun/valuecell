from fastapi import APIRouter, HTTPException, Path, Query

from ...services.assets.short_cycle_context_event_service import (
    get_short_cycle_context_event_service,
)
from ..schemas import SuccessResponse
from ..schemas.short_cycle_context_event import (
    ShortCycleContextEventItemData,
    ShortCycleContextEventListData,
    ShortCycleContextEventRefreshRequest,
)

DEFAULT_USER_ID = "default_user"


def create_short_cycle_context_event_router() -> APIRouter:
    router = APIRouter(prefix="/short-cycle-context-events", tags=["short-cycle-context-events"])
    short_cycle_context_event_service = get_short_cycle_context_event_service()

    @router.get("", response_model=SuccessResponse[ShortCycleContextEventListData])
    async def list_short_cycle_context_events(
        ticker: str | None = Query(None),
        limit: int = Query(200, ge=1, le=500),
    ) -> SuccessResponse[ShortCycleContextEventListData]:
        try:
            data = short_cycle_context_event_service.list_events(
                user_id=DEFAULT_USER_ID,
                ticker=ticker,
                limit=limit,
            )
            return SuccessResponse.create(
                data=ShortCycleContextEventListData(**data),
                msg="Short cycle context events retrieved successfully",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving short cycle context events: {str(exc)}",
            ) from exc

    @router.get("/{event_id}", response_model=SuccessResponse[ShortCycleContextEventItemData])
    async def get_short_cycle_context_event_detail(
        event_id: int = Path(..., ge=1, description="Event ID"),
    ) -> SuccessResponse[ShortCycleContextEventItemData]:
        try:
            data = short_cycle_context_event_service.get_event_detail(
                user_id=DEFAULT_USER_ID,
                event_id=event_id,
            )
            if data is None:
                raise HTTPException(status_code=404, detail="Short cycle context event not found")
            return SuccessResponse.create(
                data=ShortCycleContextEventItemData(**data),
                msg="Short cycle context event retrieved successfully",
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving short cycle context event: {str(exc)}",
            ) from exc

    @router.post("/refresh", response_model=SuccessResponse[ShortCycleContextEventListData])
    async def refresh_short_cycle_context_events(
        request: ShortCycleContextEventRefreshRequest,
    ) -> SuccessResponse[ShortCycleContextEventListData]:
        try:
            data = short_cycle_context_event_service.refresh_events(
                user_id=DEFAULT_USER_ID,
                ticker=request.ticker,
            )
            return SuccessResponse.create(
                data=ShortCycleContextEventListData(**data),
                msg="Short cycle context events refreshed successfully",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error refreshing short cycle context events: {str(exc)}",
            ) from exc

    return router
