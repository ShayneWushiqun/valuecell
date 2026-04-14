from __future__ import annotations

from fastapi import APIRouter

from ...services.assets.ashare_daily_workbench_service import (
    get_ashare_daily_workbench_service,
)
from ..schemas import SuccessResponse
from ..schemas.ashare_daily_workbench import (
    AShareDailyWorkbenchOverviewData,
    AShareDailyWorkbenchRefreshData,
)

DEFAULT_USER_ID = "default_user"


def create_ashare_daily_workbench_router() -> APIRouter:
    router = APIRouter(prefix="/ashare-workbench", tags=["ashare-workbench"])

    @router.get("/overview", response_model=SuccessResponse[AShareDailyWorkbenchOverviewData])
    async def get_ashare_workbench_overview() -> SuccessResponse[AShareDailyWorkbenchOverviewData]:
        data = get_ashare_daily_workbench_service().get_overview(user_id=DEFAULT_USER_ID)
        return SuccessResponse(data=data)

    @router.post("/refresh", response_model=SuccessResponse[AShareDailyWorkbenchRefreshData])
    async def refresh_ashare_workbench() -> SuccessResponse[AShareDailyWorkbenchRefreshData]:
        data = get_ashare_daily_workbench_service().refresh(user_id=DEFAULT_USER_ID)
        return SuccessResponse(data=data)

    return router
