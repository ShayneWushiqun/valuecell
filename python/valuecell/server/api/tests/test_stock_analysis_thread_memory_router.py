from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.stock_analysis_thread_memory import (
    create_stock_analysis_thread_memory_router,
)


class FakeThreadMemoryService:
    async def list_memories(self, *, user_id: str, thread_id: int):
        del user_id
        return {
            "thread_id": thread_id,
            "active_memory": {
                "memory_id": 2,
                "thread_id": thread_id,
                "user_id": "default_user",
                "title": "当前研究记忆",
                "summary": "当前主要看上下文刷新状态。",
                "stance": "继续观察",
                "confidence": 0.55,
                "time_horizon": "短线到波段",
                "focus_tickers_json": ["SZSE:300308"],
                "focus_themes_json": ["AI算力"],
                "compared_tickers_json": [],
                "support_points_json": ["中军上下文仍在。"],
                "opposing_points_json": [],
                "risk_points_json": ["仍需等待刷新。"],
                "key_uncertainties_json": ["最新价格动作尚未确认。"],
                "invalidation_conditions_json": ["刷新后摘要若变化则失效。"],
                "next_questions_json": ["刷新后是否仍能保持优先级？"],
                "next_data_to_check_json": ["最新价格动作"],
                "linked_context_ids_json": [1],
                "linked_message_ids_json": ["item_2"],
                "linked_compare_targets_json": [],
                "source_snapshot_json": {"context_count": 1},
                "is_active": True,
                "version": 2,
                "linked_context_count": 1,
                "linked_message_count": 1,
                "compare_target_count": 0,
                "created_at": "2026-04-19T10:00:00Z",
                "updated_at": "2026-04-19T10:00:00Z",
            },
            "items": [],
            "count": 1,
            "generated_at": "2026-04-19T10:00:00Z",
        }

    async def get_memory(self, *, user_id: str, thread_id: int, memory_id: int):
        del user_id
        return {
            "memory_id": memory_id,
            "thread_id": thread_id,
            "user_id": "default_user",
            "title": "历史研究记忆",
            "summary": "历史摘要",
            "stance": "继续观察",
            "confidence": 0.45,
            "time_horizon": "短线",
            "focus_tickers_json": [],
            "focus_themes_json": [],
            "compared_tickers_json": [],
            "support_points_json": [],
            "opposing_points_json": [],
            "risk_points_json": [],
            "key_uncertainties_json": [],
            "invalidation_conditions_json": [],
            "next_questions_json": [],
            "next_data_to_check_json": [],
            "linked_context_ids_json": [],
            "linked_message_ids_json": [],
            "linked_compare_targets_json": [],
            "source_snapshot_json": {},
            "is_active": False,
            "version": 1,
            "linked_context_count": 0,
            "linked_message_count": 0,
            "compare_target_count": 0,
            "created_at": "2026-04-18T10:00:00Z",
            "updated_at": "2026-04-18T10:00:00Z",
        }

    async def capture_memory(self, *, user_id: str, thread_id: int, title: str | None = None):
        del user_id
        return await self.get_memory(user_id="default_user", thread_id=thread_id, memory_id=3)

    async def activate_memory(self, *, user_id: str, thread_id: int, memory_id: int):
        del user_id
        data = await self.get_memory(user_id="default_user", thread_id=thread_id, memory_id=memory_id)
        data["is_active"] = True
        return data

    async def refresh_memory(
        self,
        *,
        user_id: str,
        thread_id: int,
        memory_id: int,
        title: str | None = None,
    ):
        del user_id, memory_id, title
        return await self.get_memory(user_id="default_user", thread_id=thread_id, memory_id=4)


def test_stock_analysis_thread_memory_router_handles_crud_actions(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.stock_analysis_thread_memory.get_stock_analysis_thread_memory_service",
        lambda: FakeThreadMemoryService(),
    )
    app = FastAPI()
    app.include_router(create_stock_analysis_thread_memory_router(), prefix="/api/v1")
    client = TestClient(app)

    assert client.get("/api/v1/stock-analysis/threads/1/memories").status_code == 200
    assert client.get("/api/v1/stock-analysis/threads/1/memories/2").status_code == 200
    assert client.post(
        "/api/v1/stock-analysis/threads/1/memories/capture",
        json={},
    ).status_code == 200
    assert client.post(
        "/api/v1/stock-analysis/threads/1/memories/2/activate",
        json={},
    ).status_code == 200
    assert client.post(
        "/api/v1/stock-analysis/threads/1/memories/2/refresh",
        json={},
    ).status_code == 200
