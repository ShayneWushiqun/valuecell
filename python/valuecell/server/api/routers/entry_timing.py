from __future__ import annotations

from fastapi import APIRouter

from ..schemas import SuccessResponse
from ..schemas.entry_timing import EntryTimingData
from ...services.assets.entry_timing_service import get_entry_timing_service


def create_entry_timing_router() -> APIRouter:
    router = APIRouter(prefix="/entry-timing", tags=["entry-timing"])

    @router.get("/signals", response_model=SuccessResponse[EntryTimingData])
    async def get_entry_timing_signals() -> SuccessResponse[EntryTimingData]:
        data = get_entry_timing_service().get_entry_timing_signals(user_id="default_user")
        return SuccessResponse(data=data)

    return router
