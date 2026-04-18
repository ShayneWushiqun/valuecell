from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.stock_analysis_compare import (
    create_stock_analysis_compare_router,
)


class FakeCompareService:
    async def list_compare_targets(self, *, user_id: str, thread_id: int):
        return {
            "thread_id": thread_id,
            "focus_type": "comparison",
            "compare_targets": [
                {
                    "target_type": "ticker",
                    "ref": "SZSE:000001",
                    "label": "持仓票",
                    "source_module": "holding",
                    "source_ref": "1",
                    "role": "primary",
                    "order": 0,
                }
            ],
            "compared_tickers": ["SZSE:000001"],
            "compared_themes": [],
            "comparison_mode": False,
        }

    async def update_compare_targets(
        self,
        *,
        user_id: str,
        thread_id: int,
        compare_targets,
    ):
        return {
            "thread_id": thread_id,
            "focus_type": "comparison",
            "compare_targets": compare_targets,
            "compared_tickers": ["SZSE:000001", "SHSE:600519"],
            "compared_themes": [],
            "comparison_mode": True,
        }


class FakeWorkspaceService:
    async def fork_thread(self, **_: object):
        return {
            "thread": {
                "thread_id": 2,
                "user_id": "default_user",
                "title": "半导体对比线程",
                "focus_type": "comparison",
                "ticker_refs_json": ["SZSE:000001", "SHSE:600519"],
                "theme_refs_json": [],
                "compare_targets_json": [
                    {
                        "target_type": "ticker",
                        "ref": "SZSE:000001",
                        "label": "持仓票",
                        "source_module": "holding",
                        "source_ref": "1",
                        "role": "primary",
                        "order": 0,
                    }
                ],
                "conversation_id": "conv_test_2",
                "context_count": 1,
                "created_at": "2026-04-18T10:00:00Z",
                "updated_at": "2026-04-18T10:00:00Z",
                "archived_at": None,
            },
            "contexts": [],
            "context_count": 0,
        }


def test_stock_analysis_compare_router_handles_compare_and_fork(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.stock_analysis_compare.get_stock_analysis_compare_service",
        lambda: FakeCompareService(),
    )
    monkeypatch.setattr(
        "valuecell.server.api.routers.stock_analysis_compare.get_stock_analysis_workspace_service",
        lambda: FakeWorkspaceService(),
    )
    app = FastAPI()
    app.include_router(create_stock_analysis_compare_router(), prefix="/api/v1")
    client = TestClient(app)

    assert client.get("/api/v1/stock-analysis/threads/1/compare-targets").status_code == 200
    assert client.put(
        "/api/v1/stock-analysis/threads/1/compare-targets",
        json={
            "compare_targets": [
                {
                    "target_type": "ticker",
                    "ref": "SZSE:000001",
                    "label": "持仓票",
                    "source_module": "holding",
                    "source_ref": "1",
                    "role": "primary",
                    "order": 0,
                },
                {
                    "target_type": "ticker",
                    "ref": "SHSE:600519",
                    "label": "机会票",
                    "source_module": "opportunity",
                    "source_ref": "SHSE:600519",
                    "role": "secondary",
                    "order": 1,
                },
            ]
        },
    ).status_code == 200
    assert client.post(
        "/api/v1/stock-analysis/threads/1/fork",
        json={
            "title": "半导体对比线程",
            "selected_context_ids": [1, 2],
            "include_compare_targets": True,
            "pin_imported_contexts": True,
        },
    ).status_code == 200
