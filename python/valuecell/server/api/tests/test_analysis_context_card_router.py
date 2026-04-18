from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.analysis_context_card import (
    create_analysis_context_card_router,
)


class FakeWorkspaceService:
    async def list_context_cards(self, *, user_id: str, thread_id: int):
        return {
            "generated_at": "2026-04-18T10:00:00Z",
            "items": [],
            "count": 0,
        }

    async def create_context_card(self, **_: str):
        return {
            "context_id": 1,
            "thread_id": 1,
            "user_id": "default_user",
            "context_type": "tradingagents_run",
            "title": "上下文摘要",
            "subtitle": None,
            "ticker_refs_json": ["SZSE:300308"],
            "theme_refs_json": [],
            "summary": "摘要",
            "snapshot_payload_json": {},
            "source_module": "tradingagents_run",
            "source_ref": "run_1",
            "staleness_hint": None,
            "generated_at": "2026-04-18T10:00:00Z",
            "data_time": "2026-04-18T10:00:00Z",
            "freshness_label": "较新",
            "refresh_recommended": False,
            "is_stale": False,
            "refresh_supported": True,
            "is_pinned": False,
            "created_at": "2026-04-18T10:00:00Z",
            "updated_at": "2026-04-18T10:00:00Z",
        }

    async def update_context_card(self, **_: str):
        return {
            "context_id": 1,
            "thread_id": 1,
            "user_id": "default_user",
            "context_type": "tradingagents_run",
            "title": "已置顶",
            "subtitle": None,
            "ticker_refs_json": ["SZSE:300308"],
            "theme_refs_json": [],
            "summary": "摘要",
            "snapshot_payload_json": {},
            "source_module": "tradingagents_run",
            "source_ref": "run_1",
            "staleness_hint": None,
            "generated_at": "2026-04-18T10:00:00Z",
            "data_time": "2026-04-18T10:00:00Z",
            "freshness_label": "较新",
            "refresh_recommended": False,
            "is_stale": False,
            "refresh_supported": True,
            "is_pinned": True,
            "created_at": "2026-04-18T10:00:00Z",
            "updated_at": "2026-04-18T10:02:00Z",
        }

    async def delete_context_card(self, **_: str):
        return True

    async def refresh_context_card(self, **_: str):
        return {
            "context_id": 1,
            "thread_id": 1,
            "user_id": "default_user",
            "context_type": "tradingagents_run",
            "title": "刷新后的上下文摘要",
            "subtitle": None,
            "ticker_refs_json": ["SZSE:300308"],
            "theme_refs_json": [],
            "summary": "刷新后的摘要",
            "snapshot_payload_json": {},
            "source_module": "tradingagents_run",
            "source_ref": "run_1",
            "staleness_hint": "建议以最新 run 为准。",
            "generated_at": "2026-04-18T10:05:00Z",
            "data_time": "2026-04-18T10:05:00Z",
            "freshness_label": "较新",
            "refresh_recommended": False,
            "is_stale": False,
            "refresh_supported": True,
            "is_pinned": True,
            "created_at": "2026-04-18T10:00:00Z",
            "updated_at": "2026-04-18T10:05:00Z",
        }

    async def refresh_stale_contexts(self, **_: str):
        return {
            "thread_id": 1,
            "refreshed_count": 1,
            "skipped_count": 1,
            "failed_count": 0,
            "items": [
                {
                    "context_id": 1,
                    "title": "刷新后的上下文摘要",
                    "source_module": "tradingagents_run",
                    "refresh_supported": True,
                    "status": "refreshed",
                    "reason": "刷新成功",
                    "before_freshness_label": "建议刷新",
                    "after_freshness_label": "较新",
                    "changed_fields": ["freshness_label", "summary"],
                    "new_generated_at": "2026-04-18T10:05:00Z",
                    "new_data_time": "2026-04-18T10:05:00Z",
                }
            ],
            "summary": "建议更新的上下文共 2 张，已刷新 1 张，其中 1 张有变化，跳过 1 张，失败 0 张。",
            "generated_at": "2026-04-18T10:05:00Z",
            "refreshed_context_ids": [1],
            "skipped_context_ids": [2],
            "failed_context_ids": [],
            "changed_contexts": [
                {
                    "context_id": 1,
                    "title": "刷新后的上下文摘要",
                    "changed_fields": ["freshness_label", "summary"],
                    "after_freshness_label": "较新",
                }
            ],
        }


def test_analysis_context_card_router_crud(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.analysis_context_card.get_stock_analysis_workspace_service",
        lambda: FakeWorkspaceService(),
    )
    monkeypatch.setattr(
        "valuecell.server.api.routers.analysis_context_card.get_stock_analysis_refresh_service",
        lambda: FakeWorkspaceService(),
    )
    app = FastAPI()
    app.include_router(create_analysis_context_card_router(), prefix="/api/v1")
    client = TestClient(app)

    assert client.get("/api/v1/stock-analysis/threads/1/contexts").status_code == 200
    assert client.post(
        "/api/v1/stock-analysis/threads/1/contexts",
        json={
            "context_type": "tradingagents_run",
            "title": "上下文摘要",
            "summary": "摘要",
            "source_module": "tradingagents_run",
            "source_ref": "run_1",
            "mode": "append",
        },
    ).status_code == 200
    assert client.put(
        "/api/v1/stock-analysis/threads/1/contexts/1",
        json={"is_pinned": True, "title": "已置顶"},
    ).status_code == 200
    assert (
        client.post("/api/v1/stock-analysis/threads/1/contexts/1/refresh").status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/stock-analysis/threads/1/contexts/refresh-stale",
            json={"include_supported_only": True, "pin_refreshed_cards": False},
        ).status_code
        == 200
    )
    assert client.delete("/api/v1/stock-analysis/threads/1/contexts/1").status_code == 200
