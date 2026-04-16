from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ...services.assets.ashare_daily_snapshot_service import (
    get_ashare_daily_snapshot_service,
)
from ..schemas import SuccessResponse
from ..schemas.ashare_daily_snapshot import (
    AShareDailySnapshotDetailData,
    AShareDailySnapshotListData,
    AShareDailySnapshotRefreshData,
)

DEFAULT_USER_ID = "default_user"


def create_ashare_daily_snapshot_router() -> APIRouter:
    router = APIRouter(prefix="/ashare-workbench", tags=["ashare-workbench"])

    @router.get("/snapshots", response_model=SuccessResponse[AShareDailySnapshotListData])
    async def list_ashare_workbench_snapshots(
        limit: int = Query(20, ge=1, le=50),
        include_today: bool = Query(True),
    ) -> SuccessResponse[AShareDailySnapshotListData]:
        data = get_ashare_daily_snapshot_service().list_snapshots(
            user_id=DEFAULT_USER_ID,
            limit=limit,
            include_today=include_today,
        )
        return SuccessResponse(data=data)

    @router.get(
        "/snapshots/{snapshot_date}",
        response_model=SuccessResponse[AShareDailySnapshotDetailData],
    )
    async def get_ashare_workbench_snapshot_detail(
        snapshot_date: str,
    ) -> SuccessResponse[AShareDailySnapshotDetailData]:
        data = get_ashare_daily_snapshot_service().get_snapshot_detail(
            user_id=DEFAULT_USER_ID,
            snapshot_date=snapshot_date,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Snapshot not found")
        return SuccessResponse(data=data)

    @router.post(
        "/snapshots/refresh",
        response_model=SuccessResponse[AShareDailySnapshotRefreshData],
    )
    async def refresh_ashare_workbench_snapshot() -> SuccessResponse[AShareDailySnapshotRefreshData]:
        data = get_ashare_daily_snapshot_service().refresh_today_snapshot(
            user_id=DEFAULT_USER_ID
        )
        return SuccessResponse(data=data)

    return router
