from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.stock_analysis_thread import (
    create_stock_analysis_thread_router,
)


class FakeWorkspaceService:
    async def list_threads(self, *, user_id: str):
        return {
            "generated_at": "2026-04-18T10:00:00Z",
            "items": [
                {
                    "thread_id": 1,
                    "user_id": user_id,
                    "title": "AI 算力跟踪",
                    "focus_type": "ticker",
                    "ticker_refs_json": ["SZSE:300308"],
                    "theme_refs_json": [],
                    "conversation_id": "conv_test_1",
                    "context_count": 1,
                    "created_at": "2026-04-18T09:00:00Z",
                    "updated_at": "2026-04-18T09:30:00Z",
                    "archived_at": None,
                }
            ],
            "count": 1,
        }

    async def create_thread(self, **_: str):
        return {
            "thread_id": 2,
            "user_id": "default_user",
            "title": "新线程",
            "focus_type": "mixed",
            "ticker_refs_json": [],
            "theme_refs_json": [],
            "conversation_id": "conv_test_2",
            "context_count": 0,
            "created_at": "2026-04-18T10:00:00Z",
            "updated_at": "2026-04-18T10:00:00Z",
            "archived_at": None,
        }

    async def update_thread(self, **_: str):
        return {
            "thread_id": 2,
            "user_id": "default_user",
            "title": "已重命名",
            "focus_type": "mixed",
            "ticker_refs_json": [],
            "theme_refs_json": [],
            "conversation_id": "conv_test_2",
            "context_count": 0,
            "created_at": "2026-04-18T10:00:00Z",
            "updated_at": "2026-04-18T10:01:00Z",
            "archived_at": None,
        }

    async def delete_thread(self, **_: str):
        return {
            "thread_id": 2,
            "user_id": "default_user",
            "title": "已归档",
            "focus_type": "mixed",
            "ticker_refs_json": [],
            "theme_refs_json": [],
            "conversation_id": "conv_test_2",
            "context_count": 0,
            "created_at": "2026-04-18T10:00:00Z",
            "updated_at": "2026-04-18T10:01:00Z",
            "archived_at": "2026-04-18T10:05:00Z",
        }

    async def duplicate_thread(self, **_: str):
        return {
            "thread": {
                "thread_id": 3,
                "user_id": "default_user",
                "title": "副本",
                "focus_type": "mixed",
                "ticker_refs_json": [],
                "theme_refs_json": [],
                "conversation_id": "conv_test_3",
                "context_count": 1,
                "created_at": "2026-04-18T10:06:00Z",
                "updated_at": "2026-04-18T10:06:00Z",
                "archived_at": None,
            },
            "contexts": [],
        }

    async def get_workspace_overview(self, *, user_id: str, thread_id: int | None = None):
        return {
            "generated_at": "2026-04-18T10:00:00Z",
            "threads": [],
            "current_thread": None,
            "context_count": 0,
            "available": False,
            "empty_message": "empty",
        }

    async def import_context(self, **_: str):
        return {
            "thread": {
                "thread_id": 4,
                "user_id": "default_user",
                "title": "追问：SZSE:300308 TradingAgents 分析",
                "focus_type": "tradingagents_followup",
                "ticker_refs_json": ["SZSE:300308"],
                "theme_refs_json": [],
                "conversation_id": "conv_test_4",
                "context_count": 1,
                "created_at": "2026-04-18T10:00:00Z",
                "updated_at": "2026-04-18T10:00:00Z",
                "archived_at": None,
            },
            "context_card": {
                "context_id": 1,
                "thread_id": 4,
                "user_id": "default_user",
                "context_type": "tradingagents_run",
                "title": "摘要",
                "subtitle": None,
                "ticker_refs_json": ["SZSE:300308"],
                "theme_refs_json": [],
                "summary": "摘要",
                "snapshot_payload_json": {},
                "source_module": "tradingagents_run",
                "source_ref": "run_1",
                "staleness_hint": None,
                "is_pinned": True,
                "created_at": "2026-04-18T10:00:00Z",
                "updated_at": "2026-04-18T10:00:00Z",
            },
            "contexts": [],
        }


def test_stock_analysis_thread_router_crud_and_import(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.stock_analysis_thread.get_stock_analysis_workspace_service",
        lambda: FakeWorkspaceService(),
    )
    app = FastAPI()
    app.include_router(create_stock_analysis_thread_router(), prefix="/api/v1")
    client = TestClient(app)

    assert client.get("/api/v1/stock-analysis/threads").status_code == 200
    assert client.post(
        "/api/v1/stock-analysis/threads",
        json={"title": "新线程", "focus_type": "mixed"},
    ).status_code == 200
    assert client.post(
        "/api/v1/stock-analysis/context-import",
        json={
            "source_module": "tradingagents_run",
            "source_ref": "run_1",
            "create_new_thread": True,
            "mode": "append",
        },
    ).status_code == 200
