from __future__ import annotations

from fastapi import APIRouter

from ..schemas import SuccessResponse
from ..schemas.opportunity_pool import OpportunityPoolData
from ...services.assets.opportunity_pool_service import get_opportunity_pool_service


def create_opportunity_pool_router() -> APIRouter:
    router = APIRouter(prefix="/opportunities", tags=["opportunities"])

    @router.get("/candidates", response_model=SuccessResponse[OpportunityPoolData])
    async def get_opportunity_candidates() -> SuccessResponse[OpportunityPoolData]:
        data = get_opportunity_pool_service().get_opportunity_candidates(
            user_id="default_user"
        )
        return SuccessResponse(data=data)

    return router
