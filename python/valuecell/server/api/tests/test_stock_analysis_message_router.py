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
                    "answer_basis": "当前上下文",
                    "mode": "context_only",
                    "used_context_ids": [],
                    "missing_context_hints": [],
                    "tool_reason": None,
                    "tool_calls_summary": [],
                    "temporary_evidence_blocks": [],
                    "unavailable_tools": [],
                }
            ],
            "count": 1,
        }

    async def send_message(
        self,
        *,
        user_id: str,
        thread_id: int,
        message: str,
        force_tooling: bool = False,
    ):
        del user_id, force_tooling
        from valuecell.server.services.assets.stock_analysis_message_service import (
            StockAnalysisMessageResult,
        )

        return StockAnalysisMessageResult(
            conversation_id="conv_test_1",
            thread_id=thread_id,
            answer_basis="当前上下文 + 行情补充",
            mode="user_forced_tooling",
            used_context_ids=[1],
            missing_context_hints=["latest_price_action"],
            tool_reason="用户显式要求补数据。",
            tool_calls_summary=["AssetService.get_historical_prices: 补最近 5 日日线价格"],
            temporary_evidence_blocks=[
                {
                    "type": "latest_price_action",
                    "title": "行情补充",
                    "summary": "补最近 5 日日线价格",
                    "temporary": True,
                }
            ],
            unavailable_tools=[],
            user_message={
                "item_id": "item_1",
                "role": "user",
                "event": "message",
                "conversation_id": "conv_test_1",
                "content": message,
                "answer_basis": "当前上下文",
                "mode": "user_forced_tooling",
                "used_context_ids": [],
                "missing_context_hints": [],
                "tool_reason": None,
                "tool_calls_summary": [],
                "temporary_evidence_blocks": [],
                "unavailable_tools": [],
            },
            assistant_message={
                "item_id": "item_2",
                "role": "agent",
                "event": "message",
                "conversation_id": "conv_test_1",
                "content": "回答依据：当前上下文。",
                "answer_basis": "当前上下文 + 行情补充",
                "mode": "user_forced_tooling",
                "used_context_ids": [1],
                "missing_context_hints": ["latest_price_action"],
                "tool_reason": "用户显式要求补数据。",
                "tool_calls_summary": ["AssetService.get_historical_prices: 补最近 5 日日线价格"],
                "temporary_evidence_blocks": [
                    {
                        "type": "latest_price_action",
                        "title": "行情补充",
                        "summary": "补最近 5 日日线价格",
                        "temporary": True,
                    }
                ],
                "unavailable_tools": [],
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
        json={"message": "请比较当前上下文里的标的。", "force_tooling": True},
    )

    assert list_response.status_code == 200
    assert list_response.json()["data"]["count"] == 1
    assert create_response.status_code == 200
    assert create_response.json()["data"]["answer_basis"] == "当前上下文 + 行情补充"
    assert create_response.json()["data"]["mode"] == "user_forced_tooling"
