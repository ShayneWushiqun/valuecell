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


class FakeHoldingLifecycleService:
    def get_overview(self, user_id: str) -> dict[str, Any]:
        return {
            "items": [
                {
                    "holding_id": 1,
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "lifecycle_stage": "主升持有期",
                    "action": "继续持有",
                    "theme_name": "AI算力",
                    "role_label": "龙头",
                }
            ]
        }


class FakeExitRiskCenterService:
    def get_overview(self, user_id: str) -> dict[str, Any]:
        return {
            "high_priority_items": [
                {
                    "ticker": "SZSE:300308",
                    "action": "保护利润",
                    "risk_type": "高位分歧",
                    "liquidity_warning": "成交放大后需防止回撤。",
                }
            ],
            "profit_protection_items": [],
            "discipline_stop_items": [],
            "watch_items": [],
        }


class FakeOpportunityPoolService:
    def get_opportunity_candidates(self, user_id: str) -> dict[str, Any]:
        return {
            "items": [
                {
                    "ticker": "SZSE:000001",
                    "display_name": "平安银行",
                    "topic_name": "金融",
                    "candidate_state": "候选买点",
                    "action_hint": "等待确认后分批参与",
                    "tradeability_state": "可观察",
                    "role_label": "中军",
                }
            ]
        }


class FakeWatchlistCenterService:
    def get_overview(self, user_id: str) -> dict[str, Any]:
        return {
            "items": [
                {
                    "ticker": "SZSE:002594",
                    "display_name": "比亚迪",
                    "status": "重点观察",
                    "reason": "等待新一轮承接确认。",
                    "tradeability_state": "可低吸",
                    "expectation_gap_level": "中",
                    "theme_name": "新能源车",
                    "quick_note": "不追高。",
                }
            ]
        }


class FakeThemeRadarService:
    def get_overview(self, user_id: str) -> dict[str, Any]:
        return {
            "items": [
                {
                    "theme_code": "ai_compute",
                    "theme_name": "AI算力",
                    "theme_state": "主升",
                    "observation_summary": "主线仍然清晰，但分歧加大。",
                    "representative_tickers": ["SZSE:300308", "SHSE:603019"],
                    "participation_hint": "优先核心票",
                    "risk_tags": ["高位分歧", "轮动加快"],
                }
            ]
        }


class FakeDecisionAlertService:
    def get_decision_alert_summary(self, user_id: str) -> dict[str, Any]:
        return {
            "items": [
                {
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "alert_type": "holding_risk",
                    "body": "短线波动放大，注意利润保护。",
                    "next_action": "先确认承接再决定是否减仓。",
                    "reasons": ["量能波动放大"],
                    "priority": "high",
                    "topic_name": "AI算力",
                }
            ]
        }


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("source_module", "source_ref", "expected_type"),
    [
        ("holding", "1", "holding"),
        ("opportunity", "SZSE:000001", "opportunity"),
        ("watchlist", "SZSE:002594", "watchlist"),
        ("theme", "ai_compute", "theme"),
        ("alert", "SZSE:300308|holding_risk", "alert"),
        ("ticker", "SZSE:600519", "ticker"),
    ],
)
async def test_import_multi_module_contexts(
    source_module: str,
    source_ref: str,
    expected_type: str,
) -> None:
    service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        tradingagents_service=cast(Any, FakeTradingAgentsService()),
        conversation_service=cast(Any, FakeConversationService()),
        holding_lifecycle_service=cast(Any, FakeHoldingLifecycleService()),
        exit_risk_center_service=cast(Any, FakeExitRiskCenterService()),
        opportunity_pool_service=cast(Any, FakeOpportunityPoolService()),
        watchlist_center_service=cast(Any, FakeWatchlistCenterService()),
        theme_radar_service=cast(Any, FakeThemeRadarService()),
        decision_alert_service=cast(Any, FakeDecisionAlertService()),
    )

    result = await service.import_context(
        user_id="default_user",
        source_module=source_module,
        source_ref=source_ref,
        create_new_thread=True,
        mode="append",
    )

    assert result["context_card"]["context_type"] == expected_type
    assert result["context_card"]["summary"]


@pytest.mark.asyncio
async def test_import_replace_keeps_unrelated_context_cards() -> None:
    service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        tradingagents_service=cast(Any, FakeTradingAgentsService()),
        conversation_service=cast(Any, FakeConversationService()),
        opportunity_pool_service=cast(Any, FakeOpportunityPoolService()),
        theme_radar_service=cast(Any, FakeThemeRadarService()),
    )
    thread = await service.create_thread(
        user_id="default_user",
        title="多模块替换测试",
        focus_type="mixed",
    )
    await service.import_context(
        user_id="default_user",
        source_module="theme",
        source_ref="ai_compute",
        target_thread_id=thread["thread_id"],
        mode="append",
    )
    await service.import_context(
        user_id="default_user",
        source_module="opportunity",
        source_ref="SZSE:000001",
        target_thread_id=thread["thread_id"],
        mode="append",
    )

    result = await service.import_context(
        user_id="default_user",
        source_module="opportunity",
        source_ref="SZSE:000001",
        target_thread_id=thread["thread_id"],
        mode="replace",
    )

    assert len(result["contexts"]) == 2
    assert {item["context_type"] for item in result["contexts"]} == {"theme", "opportunity"}
