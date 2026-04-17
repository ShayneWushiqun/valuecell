from __future__ import annotations

from typing import Any, cast

import pytest

from valuecell.server.services.assets.stock_analysis_workspace_service import (
    StockAnalysisWorkspaceService,
)
from valuecell.server.services.tests.test_stock_analysis_thread_service import (
    FakeContextRepository,
    FakeConversationService,
    FakeThreadRepository,
)


class FakeRunData:
    def __init__(self, run_id: str, symbol: str, status: str = "succeeded") -> None:
        self.run_id = run_id
        self.symbol = symbol
        self.status = status

    def model_dump(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "symbol": self.symbol,
            "status": self.status,
            "decision_signal": "继续观察承接，不放大单次动作。",
            "summary": {
                "technical": "趋势仍在，但波动变大。",
                "fundamentals": "基本面无新增破坏。",
                "sentiment": "短线情绪分歧。",
                "capital_flow": "资金承接尚可。",
                "final_decision": "先保守跟踪，不把结论直接转成交易指令。",
            },
            "reports": [
                {
                    "key": "final_trade_decision",
                    "title": "Final Trade Decision",
                    "content": "建议继续保守跟踪，确认承接与量能。",
                }
            ],
            "completed_at": "2026-04-18T10:00:00Z",
            "updated_at": "2026-04-18T10:01:00Z",
            "created_at": "2026-04-18T09:50:00Z",
        }


class FakeTradingAgentsService:
    async def get_run(self, run_id: str):
        if run_id == "missing":
            return None
        symbol = "SZSE:300308" if run_id == "run_1" else "SZSE:688256"
        return FakeRunData(run_id=run_id, symbol=symbol)


@pytest.mark.asyncio
async def test_import_create_new_thread_returns_thread_and_context_card() -> None:
    service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        tradingagents_service=cast(Any, FakeTradingAgentsService()),
        conversation_service=cast(Any, FakeConversationService()),
    )

    result = await service.import_context(
        user_id="default_user",
        source_module="tradingagents_run",
        source_ref="run_1",
        create_new_thread=True,
        mode="append",
    )

    assert result["thread"]["focus_type"] == "tradingagents_followup"
    assert result["context_card"]["context_type"] == "tradingagents_run"
    assert result["context_card"]["source_ref"] == "run_1"


@pytest.mark.asyncio
async def test_import_replace_replaces_existing_tradingagents_cards() -> None:
    service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        tradingagents_service=cast(Any, FakeTradingAgentsService()),
        conversation_service=cast(Any, FakeConversationService()),
    )
    thread = await service.create_thread(
        user_id="default_user",
        title="替换测试",
        focus_type="tradingagents_followup",
        ticker_refs_json=["SZSE:300308"],
    )
    await service.import_context(
        user_id="default_user",
        source_module="tradingagents_run",
        source_ref="run_1",
        target_thread_id=thread["thread_id"],
        mode="append",
    )

    result = await service.import_context(
        user_id="default_user",
        source_module="tradingagents_run",
        source_ref="run_2",
        target_thread_id=thread["thread_id"],
        mode="replace",
    )

    assert len(result["contexts"]) == 1
    assert result["contexts"][0]["source_ref"] == "run_2"
