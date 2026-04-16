from fastapi import APIRouter, HTTPException, Path

from ...services.assets.holding_lifecycle_service import get_holding_lifecycle_service
from ..schemas import SuccessResponse
from ..schemas.holding_lifecycle import (
    HoldingLifecycleDetailData,
    HoldingLifecycleOverviewData,
)

DEFAULT_USER_ID = "default_user"


def create_holding_lifecycle_router() -> APIRouter:
    router = APIRouter(prefix="/holding-lifecycle", tags=["holding-lifecycle"])
    holding_lifecycle_service = get_holding_lifecycle_service()

    @router.get(
        "/overview",
        response_model=SuccessResponse[HoldingLifecycleOverviewData],
    )
    async def get_holding_lifecycle_overview() -> SuccessResponse[HoldingLifecycleOverviewData]:
        try:
            data = holding_lifecycle_service.get_overview(DEFAULT_USER_ID)
            return SuccessResponse.create(
                data=HoldingLifecycleOverviewData(**data),
                msg="Holding lifecycle overview retrieved successfully",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving holding lifecycle overview: {str(exc)}",
            ) from exc

    @router.get(
        "/holdings/{holding_id}",
        response_model=SuccessResponse[HoldingLifecycleDetailData],
    )
    async def get_holding_lifecycle_detail(
        holding_id: int = Path(..., ge=1, description="Holding ID"),
    ) -> SuccessResponse[HoldingLifecycleDetailData]:
        try:
            data = holding_lifecycle_service.get_holding_lifecycle(
                user_id=DEFAULT_USER_ID,
                holding_id=holding_id,
            )
            if data is None:
                raise HTTPException(status_code=404, detail="Holding lifecycle not found")
            return SuccessResponse.create(
                data=HoldingLifecycleDetailData(**data),
                msg="Holding lifecycle detail retrieved successfully",
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving holding lifecycle detail: {str(exc)}",
            ) from exc

    return router
