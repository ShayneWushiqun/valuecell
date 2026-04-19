from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.stock_analysis_overview import (
    create_stock_analysis_overview_router,
)


class FakeOverviewService:
    async def get_overview(self, *, user_id: str):
        del user_id
        return {
            "generated_at": "2026-04-19T10:00:00Z",
            "available": True,
            "summary": "当前有 2 条研究线程。",
            "thread_overview_items": [
                {
                    "thread_id": 1,
                    "title": "AI算力主线",
                    "focus_type": "comparison",
                    "updated_at": "2026-04-19T10:00:00Z",
                    "context_count": 2,
                    "compare_target_count": 2,
                    "open_task_count": 1,
                    "high_priority_task_count": 1,
                    "active_memory_available": True,
                    "active_compression_available": True,
                    "refresh_recommended_count": 1,
                    "stale_context_count": 1,
                    "latest_planning_profile": "refresh_first",
                    "latest_conflict_level": "high",
                    "latest_validation_status": "thesis_recheck_needed",
                    "latest_feedback_alignment_status": "unclear",
                    "latest_process_quality_status": "under_evidenced",
                    "thread_health_status": "high_conflict",
                    "thread_health_score": 48,
                    "thread_health_reason": "存在 stale context 且冲突高。",
                    "headline_summary": "当前线程需要优先处理冲突。",
                    "next_best_action": "review_high_conflict",
                    "next_best_action_reason": "先回看冲突摘要。",
                }
            ],
            "high_priority_tasks": [
                {
                    "task_id": 11,
                    "thread_id": 1,
                    "thread_title": "AI算力主线",
                    "title": "先 refresh 再确认",
                    "summary": "当前需要先刷新上下文。",
                    "priority": "high",
                    "status": "open",
                    "task_type": "refresh_needed",
                    "suggested_action": "refresh_thread",
                    "reason": "先 refresh 再强化结论。",
                }
            ],
            "high_conflict_threads": [],
            "refresh_needed_threads": [],
            "research_quality_summary": {
                "effective_count": 0,
                "mixed_count": 0,
                "under_evidenced_count": 1,
                "over_researched_count": 0,
                "confirmed_count": 0,
                "partially_confirmed_count": 0,
                "unclear_count": 1,
                "contradicted_count": 0,
            },
            "planning_profile_summary": {
                "balanced_count": 0,
                "refresh_first_count": 1,
                "compare_first_count": 0,
                "internal_first_count": 0,
                "external_confirm_first_count": 0,
                "lightweight_research_count": 0,
            },
            "recent_feedback_summary": {
                "total_feedback_count": 1,
                "effective_thread_count": 0,
                "high_conflict_thread_count": 1,
                "needs_refresh_thread_count": 1,
                "follow_up_required_thread_count": 0,
                "latest_alignment_statuses": ["unclear"],
            },
            "action_queue": [
                {
                    "kind": "review_high_conflict",
                    "thread_id": 1,
                    "title": "AI算力主线",
                    "summary": "先看 conflict",
                    "priority": "high",
                    "reason": "当前冲突高。",
                    "suggested_action": "review_high_conflict",
                    "target_ref": "thread:1",
                }
            ],
            "empty_message": None,
        }


def test_stock_analysis_overview_router_returns_overview(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.stock_analysis_overview.get_stock_analysis_overview_service",
        lambda: FakeOverviewService(),
    )
    app = FastAPI()
    app.include_router(create_stock_analysis_overview_router(), prefix="/api/v1")
    client = TestClient(app)

    response = client.get("/api/v1/stock-analysis/overview")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["available"] is True
    assert data["thread_overview_items"][0]["thread_health_status"] == "high_conflict"
    assert data["action_queue"][0]["kind"] == "review_high_conflict"
