from __future__ import annotations

from fastapi import APIRouter, Query

from ...services.assets.ashare_decision_context_service import (
    get_ashare_decision_context_service,
)
from ..schemas import SuccessResponse
from ..schemas.ashare_decision_context import AShareDecisionContextData

DEFAULT_USER_ID = "default_user"


def create_ashare_decision_context_router() -> APIRouter:
    router = APIRouter(prefix="/ashare-decision", tags=["ashare-decision"])

    @router.get("/context", response_model=SuccessResponse[AShareDecisionContextData])
    async def get_ashare_decision_context(
        ticker: str = Query(..., min_length=1),
    ) -> SuccessResponse[AShareDecisionContextData]:
        data = get_ashare_decision_context_service().get_decision_context(
            ticker=ticker,
            user_id=DEFAULT_USER_ID,
        )
        return SuccessResponse(data=data)

    return router
