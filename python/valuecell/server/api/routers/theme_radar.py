from fastapi import APIRouter, HTTPException
from loguru import logger

from ...services.assets.theme_radar_service import get_theme_radar_service
from ..schemas import SuccessResponse
from ..schemas.theme_radar import ThemeRadarOverviewData

DEFAULT_USER_ID = 'default_user'


def create_theme_radar_router() -> APIRouter:
    router = APIRouter(prefix='/theme-radar', tags=['theme-radar'])
    theme_radar_service = get_theme_radar_service()

    @router.get('/overview', response_model=SuccessResponse[ThemeRadarOverviewData])
    async def get_theme_radar_overview() -> SuccessResponse[ThemeRadarOverviewData]:
        try:
            data = theme_radar_service.get_overview(DEFAULT_USER_ID)
            return SuccessResponse.create(
                data=ThemeRadarOverviewData(**data),
                msg='Theme radar overview retrieved successfully',
            )
        except Exception as exc:
            logger.exception('Theme radar overview query failed')
            raise HTTPException(
                status_code=500,
                detail=f'Error retrieving theme radar overview: {str(exc)}',
            ) from exc

    return router
