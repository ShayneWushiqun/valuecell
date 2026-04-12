from __future__ import annotations

from fastapi import APIRouter

from ..schemas import SuccessResponse
from ..schemas.decision_alert import DecisionAlertSummaryData
from ...services.assets.decision_alert_service import get_decision_alert_service


def create_decision_alert_router() -> APIRouter:
    router = APIRouter(prefix="/decision-alerts", tags=["decision-alerts"])

    @router.get("/summary", response_model=SuccessResponse[DecisionAlertSummaryData])
    async def get_decision_alert_summary() -> SuccessResponse[DecisionAlertSummaryData]:
        data = get_decision_alert_service().get_decision_alert_summary(
            user_id="default_user"
        )
        return SuccessResponse(data=data)

    return router
