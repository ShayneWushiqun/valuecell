from __future__ import annotations

from fastapi import APIRouter

from ...services.assets.strategy_preference_service import get_strategy_preference_service
from ..schemas import SuccessResponse
from ..schemas.strategy_preference import (
    StrategyPreferenceProfileData,
    StrategyPreferenceTemplateListData,
    UpdateStrategyPreferenceRequest,
)

DEFAULT_USER_ID = "default_user"


def create_strategy_preference_router() -> APIRouter:
    router = APIRouter(prefix="/strategy-preferences", tags=["strategy-preferences"])

    @router.get("/templates", response_model=SuccessResponse[StrategyPreferenceTemplateListData])
    async def get_strategy_preference_templates() -> SuccessResponse[StrategyPreferenceTemplateListData]:
        data = get_strategy_preference_service().get_templates()
        return SuccessResponse(data=data)

    @router.get("/profile", response_model=SuccessResponse[StrategyPreferenceProfileData])
    async def get_strategy_preference_profile() -> SuccessResponse[StrategyPreferenceProfileData]:
        data = get_strategy_preference_service().get_effective_profile(user_id=DEFAULT_USER_ID)
        return SuccessResponse(data=data)

    @router.put("/profile", response_model=SuccessResponse[StrategyPreferenceProfileData])
    async def update_strategy_preference_profile(
        request: UpdateStrategyPreferenceRequest,
    ) -> SuccessResponse[StrategyPreferenceProfileData]:
        data = get_strategy_preference_service().save_profile(
            user_id=DEFAULT_USER_ID,
            payload=request.model_dump(),
        )
        return SuccessResponse(data=data)

    return router
