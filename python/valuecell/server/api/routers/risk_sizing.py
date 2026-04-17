from fastapi import APIRouter, HTTPException, Query

from ...services.assets.risk_sizing_service import get_risk_sizing_service
from ..schemas import SuccessResponse
from ..schemas.risk_sizing import RiskSizingSummaryData, RiskSizingTickerData

DEFAULT_USER_ID = "default_user"


def create_risk_sizing_router() -> APIRouter:
    router = APIRouter(prefix="/risk-sizing", tags=["risk-sizing"])

    @router.get("/summary", response_model=SuccessResponse[RiskSizingSummaryData])
    async def get_risk_sizing_summary() -> SuccessResponse[RiskSizingSummaryData]:
        try:
            data = get_risk_sizing_service().get_summary(user_id=DEFAULT_USER_ID)
            return SuccessResponse.create(
                data=RiskSizingSummaryData(**data),
                msg="Risk sizing summary retrieved successfully",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving risk sizing summary: {str(exc)}",
            ) from exc

    @router.get("/ticker", response_model=SuccessResponse[RiskSizingTickerData])
    async def get_risk_sizing_ticker(
        ticker: str = Query(..., min_length=1),
    ) -> SuccessResponse[RiskSizingTickerData]:
        try:
            data = get_risk_sizing_service().get_ticker_summary(
                user_id=DEFAULT_USER_ID,
                ticker=ticker,
            )
            return SuccessResponse.create(
                data=RiskSizingTickerData(**data),
                msg="Risk sizing ticker summary retrieved successfully",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving risk sizing ticker summary: {str(exc)}",
            ) from exc

    return router
