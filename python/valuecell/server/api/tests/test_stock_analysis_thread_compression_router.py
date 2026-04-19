from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.stock_analysis_thread_compression import (
    create_stock_analysis_thread_compression_router,
)


class FakeThreadCompressionService:
    async def list_compressions(self, *, user_id: str, thread_id: int):
        del user_id
        return {
            "thread_id": thread_id,
            "active_compression": {
                "compression_id": 2,
                "thread_id": thread_id,
                "user_id": "default_user",
                "conversation_id": "conv_1",
                "title": "当前对话压缩",
                "summary": "较早历史已压缩。",
                "current_focus": "继续沿着主线判断。",
                "covered_until_message_id": "item_12",
                "covered_message_count": 12,
                "source_message_ids_json": ["item_9", "item_10"],
                "resolved_topics_json": ["早期问题已回答。"],
                "open_questions_json": ["最新承接谁更强？"],
                "recent_compare_notes_json": ["最近比较了两只票。"],
                "recent_refresh_notes_json": ["已刷新 1 张上下文卡片。"],
                "recent_tooling_notes_json": ["补了价格动作。"],
                "recent_evidence_notes_json": ["行情补充：补最近 5 日日线。"],
                "active_memory_id": 3,
                "focus_tickers_json": ["SZSE:300308"],
                "focus_themes_json": ["AI算力"],
                "compared_tickers_json": ["SZSE:300308"],
                "next_questions_json": ["刷新后是否仍优先？"],
                "compression_reason": "manual_capture",
                "is_active": True,
                "version": 2,
                "source_message_count": 2,
                "covered_message_range_text": "已覆盖 12 条消息，截止 item_12",
                "created_at": "2026-04-20T10:00:00Z",
                "updated_at": "2026-04-20T10:00:00Z",
            },
            "items": [],
            "count": 1,
            "compression_recommended": True,
            "compression_reason": "消息数已达 24 条",
            "uncompressed_message_count": 8,
            "estimated_history_size": 12000,
            "active_compression_stale": True,
            "generated_at": "2026-04-20T10:00:00Z",
        }

    async def get_compression(self, *, user_id: str, thread_id: int, compression_id: int):
        del user_id
        return {
            "compression_id": compression_id,
            "thread_id": thread_id,
            "user_id": "default_user",
            "conversation_id": "conv_1",
            "title": "历史对话压缩",
            "summary": "历史摘要",
            "current_focus": "历史焦点",
            "covered_until_message_id": "item_8",
            "covered_message_count": 8,
            "source_message_ids_json": ["item_7", "item_8"],
            "resolved_topics_json": [],
            "open_questions_json": [],
            "recent_compare_notes_json": [],
            "recent_refresh_notes_json": [],
            "recent_tooling_notes_json": [],
            "recent_evidence_notes_json": [],
            "active_memory_id": None,
            "focus_tickers_json": [],
            "focus_themes_json": [],
            "compared_tickers_json": [],
            "next_questions_json": [],
            "compression_reason": "manual_capture",
            "is_active": False,
            "version": 1,
            "source_message_count": 2,
            "covered_message_range_text": "已覆盖 8 条消息，截止 item_8",
            "created_at": "2026-04-19T10:00:00Z",
            "updated_at": "2026-04-19T10:00:00Z",
        }

    async def capture_compression(self, *, user_id: str, thread_id: int, title: str | None = None):
        del user_id, title
        return await self.get_compression(
            user_id="default_user",
            thread_id=thread_id,
            compression_id=3,
        )

    async def activate_compression(self, *, user_id: str, thread_id: int, compression_id: int):
        del user_id
        data = await self.get_compression(
            user_id="default_user",
            thread_id=thread_id,
            compression_id=compression_id,
        )
        data["is_active"] = True
        return data

    async def refresh_compression(
        self,
        *,
        user_id: str,
        thread_id: int,
        compression_id: int,
        title: str | None = None,
    ):
        del user_id, compression_id, title
        return await self.get_compression(
            user_id="default_user",
            thread_id=thread_id,
            compression_id=4,
        )


def test_stock_analysis_thread_compression_router_handles_crud_actions(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.stock_analysis_thread_compression.get_stock_analysis_thread_compression_service",
        lambda: FakeThreadCompressionService(),
    )
    app = FastAPI()
    app.include_router(create_stock_analysis_thread_compression_router(), prefix="/api/v1")
    client = TestClient(app)

    assert client.get("/api/v1/stock-analysis/threads/1/compressions").status_code == 200
    assert client.get("/api/v1/stock-analysis/threads/1/compressions/2").status_code == 200
    assert client.post(
        "/api/v1/stock-analysis/threads/1/compressions/capture",
        json={},
    ).status_code == 200
    assert client.post(
        "/api/v1/stock-analysis/threads/1/compressions/2/activate",
        json={},
    ).status_code == 200
    assert client.post(
        "/api/v1/stock-analysis/threads/1/compressions/2/refresh",
        json={},
    ).status_code == 200
