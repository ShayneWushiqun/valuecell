from fastapi import APIRouter, HTTPException, Path, Query

from ...services.assets.decision_record_service import get_decision_record_service
from ..schemas import SuccessResponse
from ..schemas.decision_record import (
    DecisionRecordCaptureData,
    DecisionRecordItemData,
    DecisionRecordListData,
)

DEFAULT_USER_ID = "default_user"


def create_decision_record_router() -> APIRouter:
    router = APIRouter(prefix="/decision-records", tags=["decision-records"])
    decision_record_service = get_decision_record_service()

    @router.get("", response_model=SuccessResponse[DecisionRecordListData])
    async def list_decision_records(
        limit: int = Query(20, ge=1, le=100),
        action: str | None = Query(None),
    ) -> SuccessResponse[DecisionRecordListData]:
        try:
            data = decision_record_service.list_records(
                user_id=DEFAULT_USER_ID,
                limit=limit,
                action=action,
            )
            return SuccessResponse.create(
                data=DecisionRecordListData(**data),
                msg="Decision records retrieved successfully",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving decision records: {str(exc)}",
            ) from exc

    @router.get("/{record_id}", response_model=SuccessResponse[DecisionRecordItemData])
    async def get_decision_record_detail(
        record_id: int = Path(..., ge=1, description="Decision record ID"),
    ) -> SuccessResponse[DecisionRecordItemData]:
        try:
            data = decision_record_service.get_record_detail(
                user_id=DEFAULT_USER_ID,
                record_id=record_id,
            )
            if data is None:
                raise HTTPException(status_code=404, detail="Decision record not found")
            return SuccessResponse.create(
                data=DecisionRecordItemData(**data),
                msg="Decision record retrieved successfully",
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving decision record: {str(exc)}",
            ) from exc

    @router.post("/capture", response_model=SuccessResponse[DecisionRecordCaptureData])
    async def capture_decision_records() -> SuccessResponse[DecisionRecordCaptureData]:
        try:
            data = decision_record_service.capture_records(user_id=DEFAULT_USER_ID)
            return SuccessResponse.create(
                data=DecisionRecordCaptureData(**data),
                msg="Decision records captured successfully",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error capturing decision records: {str(exc)}",
            ) from exc

    @router.post("/refresh", response_model=SuccessResponse[DecisionRecordCaptureData])
    async def refresh_decision_records() -> SuccessResponse[DecisionRecordCaptureData]:
        try:
            data = decision_record_service.refresh_records(user_id=DEFAULT_USER_ID)
            return SuccessResponse.create(
                data=DecisionRecordCaptureData(**data),
                msg="Decision records refreshed successfully",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Error refreshing decision records: {str(exc)}",
            ) from exc

    return router
