from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..schemas import SuccessResponse
from ..schemas.decision_alert import (
    DecisionAlertItem,
    DecisionAlertListData,
    DecisionAlertReadAllData,
    DecisionAlertSummaryData,
)
from ...services.assets.decision_alert_persistence_service import (
    get_decision_alert_persistence_service,
)

DEFAULT_USER_ID = "default_user"


def create_decision_alert_router() -> APIRouter:
    router = APIRouter(prefix="/decision-alerts", tags=["decision-alerts"])

    @router.get("/summary", response_model=SuccessResponse[DecisionAlertSummaryData])
    async def get_decision_alert_summary() -> SuccessResponse[DecisionAlertSummaryData]:
        data = get_decision_alert_persistence_service().get_decision_alert_summary(
            user_id=DEFAULT_USER_ID
        )
        return SuccessResponse(data=data)

    @router.get("", response_model=SuccessResponse[DecisionAlertListData])
    async def list_decision_alerts(
        status: str = Query("all"),
        alert_type: str | None = Query(None),
        limit: int = Query(50, ge=1, le=200),
    ) -> SuccessResponse[DecisionAlertListData]:
        data = get_decision_alert_persistence_service().list_alerts(
            user_id=DEFAULT_USER_ID,
            status=status,
            alert_type=alert_type,
            limit=limit,
        )
        return SuccessResponse(data=data)

    @router.post("/refresh", response_model=SuccessResponse[DecisionAlertListData])
    async def refresh_decision_alerts() -> SuccessResponse[DecisionAlertListData]:
        data = get_decision_alert_persistence_service().refresh_alerts(user_id=DEFAULT_USER_ID)
        return SuccessResponse(data=data)

    @router.put("/{alert_id}/read", response_model=SuccessResponse[DecisionAlertItem])
    async def mark_decision_alert_read(alert_id: int) -> SuccessResponse[DecisionAlertItem]:
        data = get_decision_alert_persistence_service().mark_alert_read(
            user_id=DEFAULT_USER_ID,
            alert_id=alert_id,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Alert not found")
        return SuccessResponse(data=data)

    @router.put("/read-all", response_model=SuccessResponse[DecisionAlertReadAllData])
    async def mark_all_decision_alerts_read() -> SuccessResponse[DecisionAlertReadAllData]:
        data = get_decision_alert_persistence_service().mark_all_read(user_id=DEFAULT_USER_ID)
        return SuccessResponse(data=data)

    @router.put("/{alert_id}/dismiss", response_model=SuccessResponse[DecisionAlertItem])
    async def dismiss_decision_alert(alert_id: int) -> SuccessResponse[DecisionAlertItem]:
        data = get_decision_alert_persistence_service().dismiss_alert(
            user_id=DEFAULT_USER_ID,
            alert_id=alert_id,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Alert not found")
        return SuccessResponse(data=data)

    return router
