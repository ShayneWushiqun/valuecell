from fastapi import APIRouter, HTTPException

from ...services.assets.exit_risk_center_service import get_exit_risk_center_service
from ..schemas import SuccessResponse
from ..schemas.exit_risk_center import (
    ExitRiskCenterOverviewData,
    ExitRiskCenterRefreshData,
)

DEFAULT_USER_ID = "default_user"


def create_exit_risk_center_router() -> APIRouter:
    router = APIRouter(prefix="/exit-risk-center", tags=["exit-risk-center"])
    exit_risk_center_service = get_exit_risk_center_service()

    @router.get(
        "/overview",
        response_model=SuccessResponse[ExitRiskCenterOverviewData],
    )
    async def get_exit_risk_center_overview() -> SuccessResponse[ExitRiskCenterOverviewData]:
        try:
            data = exit_risk_center_service.get_overview(DEFAULT_USER_ID)
            return SuccessResponse.create(
                data=ExitRiskCenterOverviewData(**data),
                msg="Exit risk center overview retrieved successfully",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving exit risk center overview: {str(exc)}",
            ) from exc

    @router.post(
        "/refresh",
        response_model=SuccessResponse[ExitRiskCenterRefreshData],
    )
    async def refresh_exit_risk_center() -> SuccessResponse[ExitRiskCenterRefreshData]:
        try:
            data = exit_risk_center_service.refresh(DEFAULT_USER_ID)
            return SuccessResponse.create(
                data=ExitRiskCenterRefreshData(**data),
                msg="Exit risk center refreshed successfully",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error refreshing exit risk center: {str(exc)}",
            ) from exc

    return router
