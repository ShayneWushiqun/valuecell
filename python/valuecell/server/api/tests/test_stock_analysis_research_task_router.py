from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.stock_analysis_research_task import (
    create_stock_analysis_research_task_router,
)


class FakeResearchTaskService:
    async def list_tasks(self, *, user_id: str, thread_id: int):
        del user_id
        return {
            "thread_id": thread_id,
            "items": [
                {
                    "task_id": 1,
                    "thread_id": thread_id,
                    "user_id": "default_user",
                    "title": "刷新后重看结论",
                    "summary": "存在 stale 上下文",
                    "task_type": "refresh_needed",
                    "status": "open",
                    "priority": "high",
                    "source_kind": "refresh",
                    "source_ref": "stale_contexts",
                    "related_tickers_json": ["SZSE:300308"],
                    "related_themes_json": [],
                    "related_context_ids_json": [2],
                    "related_memory_id": None,
                    "related_compression_id": None,
                    "related_message_id": None,
                    "resolution_note": None,
                    "dismiss_reason": None,
                    "created_at": "2026-04-19T10:00:00Z",
                    "updated_at": "2026-04-19T10:00:00Z",
                    "completed_at": None,
                    "dismissed_at": None,
                }
            ],
            "count": 1,
            "open_count": 1,
            "high_priority_open_count": 1,
            "last_generated_at": "2026-04-19T10:00:00Z",
            "has_actionable_gap": True,
            "actionable_gap_summary": "存在 stale / 建议刷新上下文",
            "generated_at": "2026-04-19T10:00:00Z",
        }

    async def get_task(self, *, user_id: str, thread_id: int, task_id: int):
        del user_id
        return {
            "task_id": task_id,
            "thread_id": thread_id,
            "user_id": "default_user",
            "title": "手动任务",
            "summary": "详情",
            "task_type": "next_question",
            "status": "open",
            "priority": "medium",
            "source_kind": "manual",
            "source_ref": None,
            "related_tickers_json": [],
            "related_themes_json": [],
            "related_context_ids_json": [],
            "related_memory_id": None,
            "related_compression_id": None,
            "related_message_id": None,
            "resolution_note": None,
            "dismiss_reason": None,
            "created_at": "2026-04-19T10:00:00Z",
            "updated_at": "2026-04-19T10:00:00Z",
            "completed_at": None,
            "dismissed_at": None,
        }

    async def create_task(self, *, user_id: str, thread_id: int, **kwargs):
        del user_id, kwargs
        return await self.get_task(user_id="default_user", thread_id=thread_id, task_id=2)

    async def generate_tasks(self, *, user_id: str, thread_id: int):
        del user_id
        return {
            "thread_id": thread_id,
            "created_count": 2,
            "updated_count": 1,
            "items": [
                await self.get_task(
                    user_id="default_user",
                    thread_id=thread_id,
                    task_id=3,
                )
            ],
            "last_generated_at": "2026-04-19T10:00:00Z",
            "summary": "已生成/更新 3 条研究任务。",
        }

    async def complete_task(self, *, user_id: str, thread_id: int, task_id: int, note: str | None = None):
        del user_id, note
        data = await self.get_task(user_id="default_user", thread_id=thread_id, task_id=task_id)
        data["status"] = "completed"
        return data

    async def reopen_task(self, *, user_id: str, thread_id: int, task_id: int):
        del user_id
        return await self.get_task(user_id="default_user", thread_id=thread_id, task_id=task_id)

    async def dismiss_task(self, *, user_id: str, thread_id: int, task_id: int, note: str | None = None):
        del user_id
        data = await self.get_task(user_id="default_user", thread_id=thread_id, task_id=task_id)
        data["status"] = "dismissed"
        data["dismiss_reason"] = note
        return data


def test_stock_analysis_research_task_router_handles_crud_actions(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.stock_analysis_research_task.get_stock_analysis_research_task_service",
        lambda: FakeResearchTaskService(),
    )
    app = FastAPI()
    app.include_router(create_stock_analysis_research_task_router(), prefix="/api/v1")
    client = TestClient(app)

    assert client.get("/api/v1/stock-analysis/threads/1/research-tasks").status_code == 200
    assert client.get("/api/v1/stock-analysis/threads/1/research-tasks/1").status_code == 200
    assert (
        client.post(
            "/api/v1/stock-analysis/threads/1/research-tasks",
            json={"title": "手动创建任务"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/stock-analysis/threads/1/research-tasks/generate",
            json={},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/stock-analysis/threads/1/research-tasks/1/complete",
            json={"note": "done"},
        ).status_code
        == 200
    )
    assert (
        client.post("/api/v1/stock-analysis/threads/1/research-tasks/1/reopen", json={}).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/stock-analysis/threads/1/research-tasks/1/dismiss",
            json={"note": "skip"},
        ).status_code
        == 200
    )
