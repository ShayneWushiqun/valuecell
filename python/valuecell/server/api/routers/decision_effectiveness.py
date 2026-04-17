from fastapi import APIRouter, HTTPException

from ...services.assets.decision_effectiveness_service import (
    get_decision_effectiveness_service,
)
from ..schemas import SuccessResponse
from ..schemas.decision_effectiveness import DecisionEffectivenessSummaryData

DEFAULT_USER_ID = "default_user"


def create_decision_effectiveness_router() -> APIRouter:
    router = APIRouter(
        prefix="/decision-effectiveness",
        tags=["decision-effectiveness"],
    )

    @router.get("/summary", response_model=SuccessResponse[DecisionEffectivenessSummaryData])
    async def get_decision_effectiveness_summary() -> SuccessResponse[
        DecisionEffectivenessSummaryData
    ]:
        try:
            data = get_decision_effectiveness_service().get_summary(
                user_id=DEFAULT_USER_ID
            )
            return SuccessResponse.create(
                data=DecisionEffectivenessSummaryData(**data),
                msg="Decision effectiveness summary retrieved successfully",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving decision effectiveness summary: {str(exc)}",
            ) from exc

    return router
