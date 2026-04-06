from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from valuecell.server.api.schemas.base import SuccessResponse
from valuecell.server.api.schemas.tradingagents import (
    TradingAgentsRunListResponse,
    TradingAgentsRunRequest,
    TradingAgentsRunResponse,
)
from valuecell.server.services.tradingagents_service import TradingAgentsService


def create_tradingagents_router() -> APIRouter:
    router = APIRouter(prefix="/tradingagents", tags=["tradingagents"])
    service = TradingAgentsService()

    @router.post("/runs", response_model=TradingAgentsRunResponse)
    async def create_run(request: TradingAgentsRunRequest):
        try:
            data = await service.create_run(request)
            return SuccessResponse.create(data=data)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            logger.exception("TradingAgents run failed unexpectedly")
            raise HTTPException(
                status_code=500,
                detail="TradingAgents run failed",
            ) from exc

    @router.get("/runs", response_model=TradingAgentsRunListResponse)
    async def list_runs(limit: int = Query(default=20, ge=1, le=100)):
        try:
            data = await service.list_runs(limit=limit)
            return SuccessResponse.create(data=data)
        except Exception as exc:
            logger.exception("TradingAgents runs query failed unexpectedly")
            raise HTTPException(
                status_code=500,
                detail="TradingAgents runs query failed",
            ) from exc

    @router.get("/runs/{run_id}", response_model=TradingAgentsRunResponse)
    async def get_run(run_id: str):
        try:
            data = await service.get_run(run_id)
            if data is None:
                raise HTTPException(status_code=404, detail="TradingAgents run not found")
            return SuccessResponse.create(data=data)
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("TradingAgents run detail query failed unexpectedly")
            raise HTTPException(
                status_code=500,
                detail="TradingAgents run detail query failed",
            ) from exc

    return router
