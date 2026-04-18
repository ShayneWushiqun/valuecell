from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.stock_analysis_message import (
    create_stock_analysis_message_router,
)


class FakeMessageService:
    async def list_messages(self, *, user_id: str, thread_id: int, limit: int = 100):
        return {
            "conversation_id": "conv_test_1",
            "thread_id": thread_id,
            "items": [
                {
                    "item_id": "item_1",
                    "role": "user",
                    "event": "message",
                    "conversation_id": "conv_test_1",
                    "content": "问题",
                    "answer_basis": "context_only",
                    "used_context_ids": [],
                    "missing_context_hints": [],
                }
            ],
            "count": 1,
        }

    async def send_message(self, *, user_id: str, thread_id: int, message: str):
        from valuecell.server.services.assets.stock_analysis_message_service import (
            StockAnalysisMessageResult,
        )

        return StockAnalysisMessageResult(
            conversation_id="conv_test_1",
            thread_id=thread_id,
            answer_basis="context_only",
            used_context_ids=[1],
            missing_context_hints=[],
            user_message={
                "item_id": "item_1",
                "role": "user",
                "event": "message",
                "conversation_id": "conv_test_1",
                "content": message,
                "answer_basis": "context_only",
                "used_context_ids": [],
                "missing_context_hints": [],
            },
            assistant_message={
                "item_id": "item_2",
                "role": "agent",
                "event": "message",
                "conversation_id": "conv_test_1",
                "content": "回答依据：当前上下文。",
                "answer_basis": "context_only",
                "used_context_ids": [1],
                "missing_context_hints": [],
            },
        )


def test_stock_analysis_message_router_list_and_create(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.stock_analysis_message.get_stock_analysis_message_service",
        lambda: FakeMessageService(),
    )
    app = FastAPI()
    app.include_router(create_stock_analysis_message_router(), prefix="/api/v1")
    client = TestClient(app)

    list_response = client.get("/api/v1/stock-analysis/threads/1/messages")
    create_response = client.post(
        "/api/v1/stock-analysis/threads/1/messages",
        json={"message": "请比较当前上下文里的标的。"},
    )

    assert list_response.status_code == 200
    assert list_response.json()["data"]["count"] == 1
    assert create_response.status_code == 200
    assert create_response.json()["data"]["answer_basis"] == "context_only"
