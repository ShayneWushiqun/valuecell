from __future__ import annotations

from typing import Any, cast

import pytest

from valuecell.server.services.assets.stock_analysis_workspace_service import (
    TEMPORARY_EVIDENCE_SAVED_CONTEXT_TYPE,
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


class FakeDecisionContextWindowService:
    def list_windows(self, *, user_id: str, limit: int = 100) -> dict[str, Any]:
        del user_id, limit
        return {
            "items": [
                {
                    "window_id": 11,
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "theme_name": "AI算力",
                    "action": "继续持有",
                    "window_date": "2026-04-18",
                    "support_points": ["趋势仍在"],
                    "opposing_points": ["高位分歧"],
                    "risk_points": ["波动放大"],
                }
            ]
        }


class FakeDecisionOutcomeReviewService:
    def list_reviews(self, *, user_id: str, limit: int = 100) -> dict[str, Any]:
        del user_id, limit
        return {
            "items": [
                {
                    "review_id": 21,
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "outcome_status": "有效",
                    "outcome_score": 88,
                    "review_horizon_days": 10,
                    "summary": "继续持有判断在窗口内有效。",
                    "what_happened": "趋势延续。",
                    "what_was_right": "识别主升。",
                    "what_was_wrong": "分歧时点偏乐观。",
                }
            ]
        }


class FakeRiskSizingService:
    def get_summary(self, *, user_id: str) -> dict[str, Any]:
        del user_id
        return {
            "available": True,
            "market_risk_level": "中",
            "suggested_total_exposure_range": "30% - 50%",
            "suggested_single_position_range": "6% - 10%",
            "position_guidance": "先控制节奏。",
            "ticker_suggestions": [
                {
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "risk_level": "中",
                    "suggested_position_range": "6% - 10%",
                    "guidance": "优先分批。",
                }
            ],
        }

    def get_ticker_summary(self, *, user_id: str, ticker: str) -> dict[str, Any]:
        del user_id
        return {
            "available": True,
            "ticker": ticker,
            "display_name": "中际旭创",
            "risk_level": "中",
            "suggested_position_range": "6% - 10%",
            "guidance": "优先分批。",
        }


class FakeDecisionEffectivenessService:
    def get_summary(self, *, user_id: str) -> dict[str, Any]:
        del user_id
        return {
            "available": True,
            "overall_summary": "近期继续持有类判断整体更稳。",
            "overall_score": 76,
            "review_count": 8,
            "effective_count": 5,
            "failed_count": 1,
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
        ("decision_context_window", "11", "decision_context_window"),
        ("decision_outcome_review", "21", "decision_outcome_review"),
        ("risk_sizing", "__portfolio__", "risk_sizing"),
        ("decision_effectiveness", "__summary__", "decision_effectiveness"),
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
        decision_context_window_service=cast(Any, FakeDecisionContextWindowService()),
        decision_outcome_review_service=cast(Any, FakeDecisionOutcomeReviewService()),
        risk_sizing_service=cast(Any, FakeRiskSizingService()),
        decision_effectiveness_service=cast(Any, FakeDecisionEffectivenessService()),
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


@pytest.mark.asyncio
async def test_fork_thread_copies_selected_contexts_without_copying_message_history() -> None:
    conversation_service = FakeConversationService()
    context_repository = FakeContextRepository()
    service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        analysis_context_card_repository=cast(Any, context_repository),
        conversation_service=cast(Any, conversation_service),
    )
    source_thread = await service.create_thread(
        user_id="default_user",
        title="半导体主线",
        focus_type="comparison",
        compare_targets_json=[
            {
                "target_type": "ticker",
                "ref": "SHSE:603986",
                "label": "中军",
                "source_module": "holding",
                "source_ref": "11",
                "role": "primary",
                "order": 0,
            },
            {
                "target_type": "ticker",
                "ref": "SZSE:300474",
                "label": "跟风",
                "source_module": "opportunity",
                "source_ref": "SZSE:300474",
                "role": "secondary",
                "order": 1,
            },
        ],
    )
    first = await service.create_context_card(
        user_id="default_user",
        thread_id=source_thread["thread_id"],
        context_type="holding",
        title="中军持仓卡",
        summary="中军票持仓观察。",
        ticker_refs_json=["SHSE:603986"],
        source_module="holding",
        source_ref="11",
    )
    second = await service.create_context_card(
        user_id="default_user",
        thread_id=source_thread["thread_id"],
        context_type="opportunity",
        title="跟风机会卡",
        summary="跟风候选观察。",
        ticker_refs_json=["SZSE:300474"],
        source_module="opportunity",
        source_ref="SZSE:300474",
    )

    result = await service.fork_thread(
        user_id="default_user",
        thread_id=source_thread["thread_id"],
        selected_context_ids=[int(first["context_id"])],
        include_compare_targets=True,
        pin_imported_contexts=True,
    )

    assert result is not None
    assert result["thread"]["thread_id"] != source_thread["thread_id"]
    assert result["thread"]["conversation_id"] != source_thread["conversation_id"]
    assert result["thread"]["compare_targets_json"]
    assert result["context_count"] == 1
    assert result["contexts"][0]["context_id"] != second["context_id"]
    assert result["contexts"][0]["title"] == "中军持仓卡"
    assert result["contexts"][0]["is_pinned"] is True


@pytest.mark.asyncio
async def test_refresh_context_card_reuses_existing_builder() -> None:
    service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        tradingagents_service=cast(Any, FakeTradingAgentsService()),
        conversation_service=cast(Any, FakeConversationService()),
        opportunity_pool_service=cast(Any, FakeOpportunityPoolService()),
    )
    thread = await service.create_thread(
        user_id="default_user",
        title="刷新测试",
        focus_type="ticker",
    )
    card = await service.import_context(
        user_id="default_user",
        source_module="opportunity",
        source_ref="SZSE:000001",
        target_thread_id=thread["thread_id"],
        mode="append",
    )

    refreshed = await service.refresh_context_card(
        user_id="default_user",
        thread_id=thread["thread_id"],
        context_id=int(card["context_card"]["context_id"]),
    )

    assert refreshed is not None
    assert refreshed["context_id"] == card["context_card"]["context_id"]
    assert refreshed["context_type"] == "opportunity"
    assert refreshed["source_ref"] == "SZSE:000001"
    assert refreshed["summary"]


@pytest.mark.asyncio
async def test_refresh_context_card_rejects_saved_temporary_evidence() -> None:
    service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        conversation_service=cast(Any, FakeConversationService()),
    )
    thread = await service.create_thread(
        user_id="default_user",
        title="证据刷新测试",
        focus_type="mixed",
    )
    created = await service.create_context_card(
        user_id="default_user",
        thread_id=thread["thread_id"],
        context_type=TEMPORARY_EVIDENCE_SAVED_CONTEXT_TYPE,
        title="历史证据",
        summary="某轮补数证据",
        source_module="tooling_evidence",
        source_ref="message:0",
    )

    assert created is not None
    with pytest.raises(ValueError, match="不支持直接刷新"):
        await service.refresh_context_card(
            user_id="default_user",
            thread_id=thread["thread_id"],
            context_id=int(created["context_id"]),
        )


@pytest.mark.asyncio
async def test_list_context_cards_returns_staleness_fields() -> None:
    service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        conversation_service=cast(Any, FakeConversationService()),
    )
    thread = await service.create_thread(
        user_id="default_user",
        title="时效测试",
        focus_type="ticker",
        ticker_refs_json=["SZSE:300308"],
    )
    created = await service.create_context_card(
        user_id="default_user",
        thread_id=thread["thread_id"],
        context_type="ticker",
        title="老卡片",
        summary="需要刷新。",
        ticker_refs_json=["SZSE:300308"],
        snapshot_payload_json={"generated_at": "2026-04-10T10:00:00+00:00"},
        source_module="ticker",
        source_ref="SZSE:300308",
    )

    assert created is not None
    result = await service.list_context_cards(
        user_id="default_user",
        thread_id=thread["thread_id"],
    )

    assert result is not None
    assert result["items"][0]["freshness_label"] == "建议刷新"
    assert result["items"][0]["refresh_recommended"] is True
    assert result["items"][0]["is_stale"] is True
