from fastapi import APIRouter, HTTPException
from loguru import logger

from ...services.assets.homepage_context_service import get_homepage_context_service
from ..schemas import SuccessResponse
from ..schemas.homepage_context import HomepageContextData

DEFAULT_USER_ID = "default_user"


def create_homepage_context_router() -> APIRouter:
    router = APIRouter(prefix="/homepage", tags=["Homepage"])
    homepage_context_service = get_homepage_context_service()

    @router.get(
        "/context",
        response_model=SuccessResponse[HomepageContextData],
    )
    async def get_homepage_context():
        try:
            context = homepage_context_service.get_homepage_context(DEFAULT_USER_ID)
            return SuccessResponse.create(
                data=HomepageContextData(**context),
                msg="Homepage context retrieved successfully",
            )
        except Exception as exc:
            logger.exception("Homepage context query failed")
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving homepage context: {str(exc)}",
            ) from exc

    return router
