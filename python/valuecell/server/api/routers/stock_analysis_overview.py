from fastapi import APIRouter

from ...services.assets.stock_analysis_overview_service import (
    get_stock_analysis_overview_service,
)
from ...services.assets.stock_analysis_workspace_service import DEFAULT_USER_ID
from ..schemas import SuccessResponse
from ..schemas.stock_analysis_overview import StockAnalysisOverviewData


def create_stock_analysis_overview_router() -> APIRouter:
    router = APIRouter(prefix="/stock-analysis", tags=["stock-analysis-overview"])

    @router.get(
        "/overview",
        response_model=SuccessResponse[StockAnalysisOverviewData],
    )
    async def get_stock_analysis_overview() -> SuccessResponse[StockAnalysisOverviewData]:
        data = await get_stock_analysis_overview_service().get_overview(
            user_id=DEFAULT_USER_ID
        )
        return SuccessResponse.create(
            data=StockAnalysisOverviewData(**data),
            msg="Stock analysis overview retrieved successfully",
        )

    return router
