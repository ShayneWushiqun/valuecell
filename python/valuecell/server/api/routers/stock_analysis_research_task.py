from fastapi import APIRouter, HTTPException

from ...services.assets.stock_analysis_research_task_service import (
    get_stock_analysis_research_task_service,
)
from ...services.assets.stock_analysis_workspace_service import DEFAULT_USER_ID
from ..schemas import SuccessResponse
from ..schemas.stock_analysis_research_task import (
    StockAnalysisResearchTaskCreateRequest,
    StockAnalysisResearchTaskGenerateData,
    StockAnalysisResearchTaskGenerateRequest,
    StockAnalysisResearchTaskItemData,
    StockAnalysisResearchTaskListData,
    StockAnalysisResearchTaskMutationData,
    StockAnalysisResearchTaskStateRequest,
)


def create_stock_analysis_research_task_router() -> APIRouter:
    router = APIRouter(prefix="/stock-analysis", tags=["stock-analysis-research-task"])

    @router.get(
        "/threads/{thread_id}/research-tasks",
        response_model=SuccessResponse[StockAnalysisResearchTaskListData],
    )
    async def list_thread_research_tasks(
        thread_id: int,
    ) -> SuccessResponse[StockAnalysisResearchTaskListData]:
        data = await get_stock_analysis_research_task_service().list_tasks(
            user_id=DEFAULT_USER_ID,
            thread_id=thread_id,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Thread not found")
        return SuccessResponse.create(
            data=StockAnalysisResearchTaskListData(**data),
            msg="Stock analysis research tasks retrieved successfully",
        )

    @router.get(
        "/threads/{thread_id}/research-tasks/{task_id}",
        response_model=SuccessResponse[StockAnalysisResearchTaskItemData],
    )
    async def get_thread_research_task(
        thread_id: int,
        task_id: int,
    ) -> SuccessResponse[StockAnalysisResearchTaskItemData]:
        data = await get_stock_analysis_research_task_service().get_task(
            user_id=DEFAULT_USER_ID,
            thread_id=thread_id,
            task_id=task_id,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Research task not found")
        return SuccessResponse.create(
            data=StockAnalysisResearchTaskItemData(**data),
            msg="Stock analysis research task retrieved successfully",
        )

    @router.post(
        "/threads/{thread_id}/research-tasks",
        response_model=SuccessResponse[StockAnalysisResearchTaskMutationData],
    )
    async def create_thread_research_task(
        thread_id: int,
        request: StockAnalysisResearchTaskCreateRequest,
    ) -> SuccessResponse[StockAnalysisResearchTaskMutationData]:
        data = await get_stock_analysis_research_task_service().create_task(
            user_id=DEFAULT_USER_ID,
            thread_id=thread_id,
            title=request.title,
            summary=request.summary,
            task_type=request.task_type,
            priority=request.priority,
            source_kind=request.source_kind,
            source_ref=request.source_ref,
            related_tickers_json=request.related_tickers_json,
            related_themes_json=request.related_themes_json,
            related_context_ids_json=request.related_context_ids_json,
            related_memory_id=request.related_memory_id,
            related_compression_id=request.related_compression_id,
            related_message_id=request.related_message_id,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Thread not found")
        return SuccessResponse.create(
            data=StockAnalysisResearchTaskMutationData(
                thread_id=thread_id,
                task=StockAnalysisResearchTaskItemData(**data),
            ),
            msg="Stock analysis research task created successfully",
        )

    @router.post(
        "/threads/{thread_id}/research-tasks/generate",
        response_model=SuccessResponse[StockAnalysisResearchTaskGenerateData],
    )
    async def generate_thread_research_tasks(
        thread_id: int,
        request: StockAnalysisResearchTaskGenerateRequest,
    ) -> SuccessResponse[StockAnalysisResearchTaskGenerateData]:
        del request
        data = await get_stock_analysis_research_task_service().generate_tasks(
            user_id=DEFAULT_USER_ID,
            thread_id=thread_id,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Thread not found")
        return SuccessResponse.create(
            data=StockAnalysisResearchTaskGenerateData(**data),
            msg="Stock analysis research tasks generated successfully",
        )

    @router.post(
        "/threads/{thread_id}/research-tasks/{task_id}/complete",
        response_model=SuccessResponse[StockAnalysisResearchTaskMutationData],
    )
    async def complete_thread_research_task(
        thread_id: int,
        task_id: int,
        request: StockAnalysisResearchTaskStateRequest,
    ) -> SuccessResponse[StockAnalysisResearchTaskMutationData]:
        data = await get_stock_analysis_research_task_service().complete_task(
            user_id=DEFAULT_USER_ID,
            thread_id=thread_id,
            task_id=task_id,
            note=request.note,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Research task not found")
        return SuccessResponse.create(
            data=StockAnalysisResearchTaskMutationData(
                thread_id=thread_id,
                task=StockAnalysisResearchTaskItemData(**data),
            ),
            msg="Stock analysis research task completed successfully",
        )

    @router.post(
        "/threads/{thread_id}/research-tasks/{task_id}/reopen",
        response_model=SuccessResponse[StockAnalysisResearchTaskMutationData],
    )
    async def reopen_thread_research_task(
        thread_id: int,
        task_id: int,
    ) -> SuccessResponse[StockAnalysisResearchTaskMutationData]:
        data = await get_stock_analysis_research_task_service().reopen_task(
            user_id=DEFAULT_USER_ID,
            thread_id=thread_id,
            task_id=task_id,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Research task not found")
        return SuccessResponse.create(
            data=StockAnalysisResearchTaskMutationData(
                thread_id=thread_id,
                task=StockAnalysisResearchTaskItemData(**data),
            ),
            msg="Stock analysis research task reopened successfully",
        )

    @router.post(
        "/threads/{thread_id}/research-tasks/{task_id}/dismiss",
        response_model=SuccessResponse[StockAnalysisResearchTaskMutationData],
    )
    async def dismiss_thread_research_task(
        thread_id: int,
        task_id: int,
        request: StockAnalysisResearchTaskStateRequest,
    ) -> SuccessResponse[StockAnalysisResearchTaskMutationData]:
        data = await get_stock_analysis_research_task_service().dismiss_task(
            user_id=DEFAULT_USER_ID,
            thread_id=thread_id,
            task_id=task_id,
            note=request.note,
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Research task not found")
        return SuccessResponse.create(
            data=StockAnalysisResearchTaskMutationData(
                thread_id=thread_id,
                task=StockAnalysisResearchTaskItemData(**data),
            ),
            msg="Stock analysis research task dismissed successfully",
        )

    return router
