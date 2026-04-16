from fastapi import APIRouter, HTTPException
from loguru import logger

from ...services.assets.watchlist_center_service import get_watchlist_center_service
from ..schemas import SuccessResponse
from ..schemas.watchlist_center import WatchlistCenterOverviewData

DEFAULT_USER_ID = 'default_user'


def create_watchlist_center_router() -> APIRouter:
    router = APIRouter(prefix='/watchlist-center', tags=['watchlist-center'])
    watchlist_center_service = get_watchlist_center_service()

    @router.get('/overview', response_model=SuccessResponse[WatchlistCenterOverviewData])
    async def get_watchlist_center_overview() -> SuccessResponse[WatchlistCenterOverviewData]:
        try:
            data = watchlist_center_service.get_overview(DEFAULT_USER_ID)
            return SuccessResponse.create(
                data=WatchlistCenterOverviewData(**data),
                msg='Watchlist center overview retrieved successfully',
            )
        except Exception as exc:
            logger.exception('Watchlist center overview query failed')
            raise HTTPException(
                status_code=500,
                detail=f'Error retrieving watchlist center overview: {str(exc)}',
            ) from exc

    return router
