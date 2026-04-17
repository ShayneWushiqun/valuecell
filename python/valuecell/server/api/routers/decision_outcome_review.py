from fastapi import APIRouter, HTTPException, Path, Query

from ...services.assets.decision_outcome_review_service import (
    get_decision_outcome_review_service,
)
from ..schemas import SuccessResponse
from ..schemas.decision_outcome_review import (
    DecisionOutcomeReviewCaptureRequest,
    DecisionOutcomeReviewItemData,
    DecisionOutcomeReviewListData,
    DecisionOutcomeReviewRefreshRequest,
)

DEFAULT_USER_ID = "default_user"


def create_decision_outcome_review_router() -> APIRouter:
    router = APIRouter(
        prefix="/decision-outcome-reviews",
        tags=["decision-outcome-reviews"],
    )
    decision_outcome_review_service = get_decision_outcome_review_service()

    @router.get("", response_model=SuccessResponse[DecisionOutcomeReviewListData])
    async def list_decision_outcome_reviews(
        record_id: int | None = Query(None, ge=1),
        outcome_status: str | None = Query(None),
        action: str | None = Query(None),
        review_horizon_days: int | None = Query(None, ge=1),
        limit: int = Query(50, ge=1, le=200),
    ) -> SuccessResponse[DecisionOutcomeReviewListData]:
        try:
            data = decision_outcome_review_service.list_reviews(
                user_id=DEFAULT_USER_ID,
                record_id=record_id,
                outcome_status=outcome_status,
                action=action,
                review_horizon_days=review_horizon_days,
                limit=limit,
            )
            return SuccessResponse.create(
                data=DecisionOutcomeReviewListData(**data),
                msg="Decision outcome reviews retrieved successfully",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving decision outcome reviews: {str(exc)}",
            ) from exc

    @router.get("/{review_id}", response_model=SuccessResponse[DecisionOutcomeReviewItemData])
    async def get_decision_outcome_review_detail(
        review_id: int = Path(..., ge=1, description="Decision outcome review ID"),
    ) -> SuccessResponse[DecisionOutcomeReviewItemData]:
        try:
            data = decision_outcome_review_service.get_review_detail(
                user_id=DEFAULT_USER_ID,
                review_id=review_id,
            )
            if data is None:
                raise HTTPException(status_code=404, detail="Decision outcome review not found")
            return SuccessResponse.create(
                data=DecisionOutcomeReviewItemData(**data),
                msg="Decision outcome review retrieved successfully",
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving decision outcome review: {str(exc)}",
            ) from exc

    @router.post("/capture", response_model=SuccessResponse[DecisionOutcomeReviewItemData])
    async def capture_decision_outcome_review(
        request: DecisionOutcomeReviewCaptureRequest,
    ) -> SuccessResponse[DecisionOutcomeReviewItemData]:
        try:
            data = decision_outcome_review_service.capture_review(
                user_id=DEFAULT_USER_ID,
                record_id=request.record_id,
                review_horizon_days=request.review_horizon_days,
                review_date=request.review_date,
            )
            if data is None:
                raise HTTPException(status_code=404, detail="Decision record not found")
            return SuccessResponse.create(
                data=DecisionOutcomeReviewItemData(**data),
                msg="Decision outcome review captured successfully",
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error capturing decision outcome review: {str(exc)}",
            ) from exc

    @router.post("/refresh", response_model=SuccessResponse[DecisionOutcomeReviewListData])
    async def refresh_decision_outcome_reviews(
        request: DecisionOutcomeReviewRefreshRequest,
    ) -> SuccessResponse[DecisionOutcomeReviewListData]:
        try:
            data = decision_outcome_review_service.refresh_reviews(
                user_id=DEFAULT_USER_ID,
                review_horizon_days_list=request.review_horizon_days_list,
                lookback_days=request.lookback_days,
                limit_records=request.limit_records,
                review_date=request.review_date,
            )
            return SuccessResponse.create(
                data=DecisionOutcomeReviewListData(**data),
                msg="Decision outcome reviews refreshed successfully",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error refreshing decision outcome reviews: {str(exc)}",
            ) from exc

    return router
