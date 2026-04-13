from __future__ import annotations

from fastapi import APIRouter

from ...services.assets.ashare_decision_judge_service import (
    get_ashare_decision_judge_service,
)
from ..schemas import SuccessResponse
from ..schemas.ashare_decision_judge import (
    AShareDecisionJudgeData,
    AShareDecisionJudgeRequest,
)

DEFAULT_USER_ID = "default_user"


def create_ashare_decision_judge_router() -> APIRouter:
    router = APIRouter(prefix="/ashare-decision", tags=["ashare-decision"])

    @router.post("/judge", response_model=SuccessResponse[AShareDecisionJudgeData])
    async def judge_ashare_decision(
        request: AShareDecisionJudgeRequest,
    ) -> SuccessResponse[AShareDecisionJudgeData]:
        data = get_ashare_decision_judge_service().judge(
            ticker=request.ticker,
            user_id=DEFAULT_USER_ID,
            enable_agent=request.enable_agent,
            force_refresh_context=request.force_refresh_context,
            user_note=request.user_note,
        )
        return SuccessResponse(data=data)

    return router
