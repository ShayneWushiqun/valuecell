from __future__ import annotations

from typing import Any, Optional

from .stock_analysis_workspace_service import (
    DEFAULT_USER_ID,
    StockAnalysisWorkspaceService,
    _normalize_compare_targets,
    _refs_from_compare_targets,
)


class StockAnalysisCompareService:
    def __init__(
        self,
        stock_analysis_workspace_service: Optional[StockAnalysisWorkspaceService] = None,
    ) -> None:
        self.stock_analysis_workspace_service = (
            stock_analysis_workspace_service or StockAnalysisWorkspaceService()
        )

    async def list_compare_targets(
        self,
        *,
        user_id: str,
        thread_id: int,
    ) -> dict[str, Any] | None:
        thread = self.stock_analysis_workspace_service.stock_analysis_thread_repository.get_thread_by_id(
            user_id=user_id,
            thread_id=thread_id,
        )
        if thread is None:
            return None
        compare_targets = _normalize_compare_targets(
            list(getattr(thread, "compare_targets_json", []) or [])
        )
        compared_tickers, compared_themes = _refs_from_compare_targets(compare_targets)
        return {
            "thread_id": thread_id,
            "focus_type": thread.focus_type,
            "compare_targets": compare_targets,
            "compared_tickers": compared_tickers,
            "compared_themes": compared_themes,
            "comparison_mode": len(compare_targets) >= 2,
        }

    async def update_compare_targets(
        self,
        *,
        user_id: str,
        thread_id: int,
        compare_targets: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        normalized_targets = _normalize_compare_targets(compare_targets)
        thread = await self.stock_analysis_workspace_service.update_thread(
            user_id=user_id,
            thread_id=thread_id,
            compare_targets_json=normalized_targets,
            focus_type="comparison" if len(normalized_targets) >= 2 else None,
        )
        if thread is None:
            return None
        return await self.list_compare_targets(user_id=user_id, thread_id=thread_id)


_stock_analysis_compare_service: StockAnalysisCompareService | None = None


def get_stock_analysis_compare_service() -> StockAnalysisCompareService:
    global _stock_analysis_compare_service
    if _stock_analysis_compare_service is None:
        _stock_analysis_compare_service = StockAnalysisCompareService()
    return _stock_analysis_compare_service


def reset_stock_analysis_compare_service() -> None:
    global _stock_analysis_compare_service
    _stock_analysis_compare_service = None
