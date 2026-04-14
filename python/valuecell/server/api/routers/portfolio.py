"""Portfolio API routes for phase one holdings and daily briefing workflows."""

from fastapi import APIRouter, HTTPException, Path
from loguru import logger

from ...services.portfolio.daily_briefing_service import get_daily_briefing_service
from ...services.portfolio.diagnosis_service import get_holding_diagnosis_service
from ...services.portfolio.holding_exit_signal_service import (
    get_holding_exit_signal_service,
)
from ...services.portfolio.holding_service import get_holding_service
from ..schemas import SuccessResponse
from ..schemas.holding_exit_signal import HoldingExitSignalData, HoldingExitSignalListData
from ..schemas.portfolio import (
    CreateHoldingRequest,
    DailyBriefingData,
    HoldingDiagnosisData,
    HoldingListData,
    PortfolioOverviewData,
    UpdateHoldingRequest,
    UserHoldingData,
)

DEFAULT_USER_ID = "default_user"


def create_portfolio_router() -> APIRouter:
    """Create portfolio router."""
    router = APIRouter(prefix="/portfolio", tags=["Portfolio"])
    holding_service = get_holding_service()
    diagnosis_service = get_holding_diagnosis_service()
    exit_signal_service = get_holding_exit_signal_service()
    briefing_service = get_daily_briefing_service()

    @router.get(
        "/overview",
        response_model=SuccessResponse[PortfolioOverviewData],
    )
    async def get_portfolio_overview():
        """Get overview for the portfolio-focused home page."""
        try:
            briefing = briefing_service.get_latest_briefing(DEFAULT_USER_ID)
            if briefing is None:
                briefing = briefing_service.refresh_daily_briefing(DEFAULT_USER_ID)
            if briefing is None:
                raise HTTPException(status_code=500, detail="Failed to generate briefing")
            holdings = holding_service.list_holdings(DEFAULT_USER_ID)
            return SuccessResponse.create(
                data=PortfolioOverviewData(
                    briefing=DailyBriefingData(**briefing),
                    holdings=[UserHoldingData(**item) for item in holdings],
                    holding_count=len(holdings),
                ),
                msg="Portfolio overview retrieved successfully",
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Portfolio overview query failed")
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving portfolio overview: {str(exc)}",
            ) from exc

    @router.get(
        "/exit-signals",
        response_model=SuccessResponse[HoldingExitSignalListData],
    )
    async def list_holding_exit_signals():
        """List exit/reduce-position signals for all holdings."""
        try:
            result = exit_signal_service.list_exit_signals(DEFAULT_USER_ID)
            return SuccessResponse.create(
                data=HoldingExitSignalListData(
                    generated_at=result["generated_at"],
                    items=[HoldingExitSignalData(**item) for item in result["items"]],
                    count=result["count"],
                ),
                msg="Holding exit signals retrieved successfully",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving holding exit signals: {str(exc)}",
            ) from exc

    @router.get(
        "/holdings",
        response_model=SuccessResponse[HoldingListData],
    )
    async def list_holdings():
        """List all user holdings with latest diagnosis."""
        try:
            holdings = holding_service.list_holdings(DEFAULT_USER_ID)
            return SuccessResponse.create(
                data=HoldingListData(
                    items=[UserHoldingData(**item) for item in holdings],
                    count=len(holdings),
                ),
                msg="Holdings retrieved successfully",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving holdings: {str(exc)}",
            ) from exc

    @router.post(
        "/holdings",
        response_model=SuccessResponse[UserHoldingData],
    )
    async def create_holding(request: CreateHoldingRequest):
        """Create a holding and immediately generate its first diagnosis."""
        try:
            holding = holding_service.create_holding(
                user_id=DEFAULT_USER_ID,
                ticker=request.ticker,
                asset_name=request.asset_name,
                quantity=request.quantity,
                cost_price=request.cost_price,
                position_weight=request.position_weight,
                buy_date=request.buy_date,
                thesis_note=request.thesis_note,
                notes=request.notes,
            )
            if holding is None:
                raise HTTPException(status_code=500, detail="Failed to create holding")
            diagnosis_service.refresh_latest_diagnosis(DEFAULT_USER_ID, holding["id"])
            detail = holding_service.get_holding(DEFAULT_USER_ID, holding["id"])
            if detail is None:
                raise HTTPException(status_code=500, detail="Failed to load holding")
            return SuccessResponse.create(
                data=UserHoldingData(**detail),
                msg="Holding created successfully",
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error creating holding: {str(exc)}",
            ) from exc

    @router.get(
        "/holdings/{holding_id}",
        response_model=SuccessResponse[UserHoldingData],
    )
    async def get_holding(
        holding_id: int = Path(..., ge=1, description="Holding ID"),
    ):
        """Get one holding with latest diagnosis."""
        try:
            holding = holding_service.get_holding(DEFAULT_USER_ID, holding_id)
            if holding is None:
                raise HTTPException(status_code=404, detail="Holding not found")
            return SuccessResponse.create(
                data=UserHoldingData(**holding),
                msg="Holding retrieved successfully",
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving holding: {str(exc)}",
            ) from exc

    @router.put(
        "/holdings/{holding_id}",
        response_model=SuccessResponse[UserHoldingData],
    )
    async def update_holding(
        request: UpdateHoldingRequest,
        holding_id: int = Path(..., ge=1, description="Holding ID"),
    ):
        """Update a holding and refresh latest diagnosis."""
        try:
            holding = holding_service.update_holding(
                user_id=DEFAULT_USER_ID,
                holding_id=holding_id,
                ticker=request.ticker,
                asset_name=request.asset_name,
                quantity=request.quantity,
                cost_price=request.cost_price,
                position_weight=request.position_weight,
                buy_date=request.buy_date,
                thesis_note=request.thesis_note,
                notes=request.notes,
            )
            if holding is None:
                raise HTTPException(status_code=404, detail="Holding not found")
            diagnosis_service.refresh_latest_diagnosis(DEFAULT_USER_ID, holding_id)
            detail = holding_service.get_holding(DEFAULT_USER_ID, holding_id)
            if detail is None:
                raise HTTPException(status_code=500, detail="Failed to load holding")
            return SuccessResponse.create(
                data=UserHoldingData(**detail),
                msg="Holding updated successfully",
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error updating holding: {str(exc)}",
            ) from exc

    @router.delete(
        "/holdings/{holding_id}",
        response_model=SuccessResponse[dict],
    )
    async def delete_holding(
        holding_id: int = Path(..., ge=1, description="Holding ID"),
    ):
        """Delete a holding."""
        try:
            deleted = holding_service.delete_holding(DEFAULT_USER_ID, holding_id)
            if not deleted:
                raise HTTPException(status_code=404, detail="Holding not found")
            return SuccessResponse.create(
                data={"holding_id": holding_id, "deleted": True},
                msg="Holding deleted successfully",
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error deleting holding: {str(exc)}",
            ) from exc

    @router.post(
        "/holdings/{holding_id}/exit-signal/refresh",
        response_model=SuccessResponse[HoldingExitSignalData],
    )
    async def refresh_holding_exit_signal(
        holding_id: int = Path(..., ge=1, description="Holding ID"),
    ):
        """Refresh and return one holding exit/reduce-position signal."""
        try:
            result = exit_signal_service.get_exit_signal(
                user_id=DEFAULT_USER_ID,
                holding_id=holding_id,
                force_refresh=True,
            )
            if result is None:
                raise HTTPException(status_code=404, detail="Holding not found")
            return SuccessResponse.create(
                data=HoldingExitSignalData(**result),
                msg="Holding exit signal refreshed successfully",
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error refreshing holding exit signal: {str(exc)}",
            ) from exc

    @router.get(
        "/holdings/{holding_id}/exit-signal",
        response_model=SuccessResponse[HoldingExitSignalData],
    )
    async def get_holding_exit_signal(
        holding_id: int = Path(..., ge=1, description="Holding ID"),
    ):
        """Get one holding exit/reduce-position signal."""
        try:
            result = exit_signal_service.get_exit_signal(
                user_id=DEFAULT_USER_ID,
                holding_id=holding_id,
                force_refresh=False,
            )
            if result is None:
                raise HTTPException(status_code=404, detail="Holding not found")
            return SuccessResponse.create(
                data=HoldingExitSignalData(**result),
                msg="Holding exit signal retrieved successfully",
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving holding exit signal: {str(exc)}",
            ) from exc

    @router.post(
        "/holdings/{holding_id}/diagnosis",
        response_model=SuccessResponse[HoldingDiagnosisData],
    )
    async def refresh_holding_diagnosis(
        holding_id: int = Path(..., ge=1, description="Holding ID"),
    ):
        """Refresh and return the latest diagnosis for one holding."""
        try:
            diagnosis = diagnosis_service.refresh_latest_diagnosis(
                DEFAULT_USER_ID,
                holding_id,
            )
            if diagnosis is None:
                raise HTTPException(
                    status_code=404,
                    detail="Holding not found or diagnosis refresh failed",
                )
            return SuccessResponse.create(
                data=HoldingDiagnosisData(**diagnosis),
                msg="Holding diagnosis refreshed successfully",
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error refreshing diagnosis: {str(exc)}",
            ) from exc

    @router.get(
        "/holdings/{holding_id}/diagnosis/latest",
        response_model=SuccessResponse[HoldingDiagnosisData],
    )
    async def get_latest_holding_diagnosis(
        holding_id: int = Path(..., ge=1, description="Holding ID"),
    ):
        """Get latest diagnosis for one holding."""
        diagnosis = diagnosis_service.get_latest_diagnosis(DEFAULT_USER_ID, holding_id)
        if diagnosis is None:
            raise HTTPException(status_code=404, detail="Diagnosis not found")
        return SuccessResponse.create(
            data=HoldingDiagnosisData(**diagnosis),
            msg="Holding diagnosis retrieved successfully",
        )

    @router.post(
        "/briefings/daily",
        response_model=SuccessResponse[DailyBriefingData],
    )
    async def refresh_daily_briefing():
        """Generate or update today's daily briefing."""
        briefing = briefing_service.refresh_daily_briefing(DEFAULT_USER_ID)
        if briefing is None:
            raise HTTPException(status_code=500, detail="Failed to refresh briefing")
        return SuccessResponse.create(
            data=DailyBriefingData(**briefing),
            msg="Daily briefing refreshed successfully",
        )

    @router.get(
        "/briefings/daily/latest",
        response_model=SuccessResponse[DailyBriefingData],
    )
    async def get_latest_daily_briefing():
        """Get the latest saved daily briefing."""
        briefing = briefing_service.get_latest_briefing(DEFAULT_USER_ID)
        if briefing is None:
            briefing = briefing_service.refresh_daily_briefing(DEFAULT_USER_ID)
        if briefing is None:
            raise HTTPException(status_code=500, detail="Failed to load briefing")
        return SuccessResponse.create(
            data=DailyBriefingData(**briefing),
            msg="Daily briefing retrieved successfully",
        )

    return router
