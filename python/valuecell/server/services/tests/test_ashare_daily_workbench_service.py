from __future__ import annotations

from typing import Any, cast

from valuecell.server.services.assets.ashare_daily_workbench_service import (
    AShareDailyWorkbenchService,
)


class FakeHomepageContextService:
    def get_homepage_context(self, user_id: str = "default_user") -> dict[str, Any]:
        return {
            "market_overview": {
                "market_state": "震荡偏强",
                "score": 68,
                "summary": "指数震荡，主线保持活跃。",
                "action_hint": "优先看风险和前排强势方向。",
            },
            "emotion_cycle": {
                "cycle_stage": "主升分歧",
            },
            "action_framework": {
                "summary": "先看风险，再看持仓，再看机会。",
            },
        }


class FakeOpportunityPoolService:
    def get_opportunity_candidates(self, user_id: str = "default_user") -> dict[str, Any]:
        return {
            "count": 2,
            "items": [
                {
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "topic_name": "AI算力",
                    "candidate_state": "高优先级买点",
                    "tradeability_state": "可观察",
                    "priority_score": 88,
                    "action_hint": "继续观察",
                },
                {
                    "ticker": "SZSE:000001",
                    "display_name": "平安银行",
                    "topic_name": "金融",
                    "candidate_state": "候选买点",
                    "tradeability_state": "可低吸",
                    "priority_score": 65,
                    "action_hint": "继续观察",
                },
            ],
        }


class FakeEntryTimingService:
    def get_entry_timing_signals(self, user_id: str = "default_user") -> dict[str, Any]:
        return {
            "items": [
                {
                    "ticker": "SZSE:300308",
                    "action": "接近可参与窗口",
                },
                {
                    "ticker": "SZSE:000001",
                    "action": "继续观察",
                },
            ]
        }


class FakeDecisionAlertPersistenceService:
    def __init__(self) -> None:
        self.refresh_calls = 0

    def list_alerts(self, *, user_id: str, status: str = "active", limit: int = 50) -> dict[str, Any]:
        if status == "unread":
            return {
                "unread_count": 3,
                "items": [
                    {
                        "id": 1,
                        "ticker": "SZSE:300308",
                        "display_name": "中际旭创",
                        "alert_type": "风险回避",
                        "priority": "high",
                        "title": "中际旭创 当前应风险回避",
                        "body": "先回避高波动。",
                        "next_action": "先观察。",
                    }
                ],
            }
        return {
            "unread_count": 3,
            "items": [
                {
                    "id": 1,
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "alert_type": "风险回避",
                    "priority": "high",
                    "title": "中际旭创 当前应风险回避",
                    "body": "先回避高波动。",
                    "next_action": "先观察。",
                },
                {
                    "id": 2,
                    "ticker": "SZSE:000001",
                    "display_name": "平安银行",
                    "alert_type": "买点接近",
                    "priority": "medium",
                    "title": "平安银行 接近可参与窗口",
                    "body": "继续等待确认。",
                    "next_action": "继续观察承接。",
                },
            ],
            "count": 2,
        }

    def refresh_alerts(self, user_id: str = "default_user") -> dict[str, Any]:
        self.refresh_calls += 1
        return {"count": 2}


class FakeHoldingExitSignalService:
    def __init__(self) -> None:
        self.refresh_calls = 0

    def list_exit_signals(self, user_id: str = "default_user") -> dict[str, Any]:
        return {
            "items": [
                {
                    "holding_id": 1,
                    "ticker": "SZSE:300308",
                    "asset_name": "中际旭创",
                    "action": "纪律止损",
                    "confidence": 70,
                    "summary": "优先收缩风险。",
                    "profit_protection_view": "先控制回撤。",
                },
                {
                    "holding_id": 2,
                    "ticker": "SZSE:000001",
                    "asset_name": "平安银行",
                    "action": "继续持有",
                    "confidence": 58,
                    "summary": "逻辑未坏。",
                    "profit_protection_view": "继续跟踪利润变化。",
                },
                {
                    "holding_id": 3,
                    "ticker": "SZSE:600036",
                    "asset_name": "招商银行",
                    "action": "保护利润",
                    "confidence": 66,
                    "summary": "浮盈回撤需防守。",
                    "profit_protection_view": "优先保护利润。",
                },
            ],
            "count": 3,
        }

    def get_exit_signal(self, *, user_id: str, holding_id: int, force_refresh: bool = False):
        if force_refresh:
            self.refresh_calls += 1
        return {
            "holding_id": holding_id,
            "action": "保护利润" if holding_id % 2 == 1 else "持有观察",
        }


class FakeHoldingService:
    def list_holdings(self, user_id: str = "default_user") -> list[dict[str, Any]]:
        return [
            {"id": 1},
            {"id": 2},
            {"id": 3},
        ]


def test_ashare_daily_workbench_service_builds_read_only_overview() -> None:
    alert_service = FakeDecisionAlertPersistenceService()
    service = AShareDailyWorkbenchService(
        homepage_context_service=cast(Any, FakeHomepageContextService()),
        opportunity_pool_service=cast(Any, FakeOpportunityPoolService()),
        entry_timing_service=cast(Any, FakeEntryTimingService()),
        decision_alert_persistence_service=cast(Any, alert_service),
        holding_exit_signal_service=cast(Any, FakeHoldingExitSignalService()),
        holding_service=cast(Any, FakeHoldingService()),
    )

    result = service.get_overview("default_user")

    assert result["available"] is True
    assert result["market_digest"]["market_state"] == "震荡偏强"
    assert result["attention_digest"]["unread_alert_count"] == 3
    assert result["attention_digest"]["holding_profit_protection_count"] == 1
    assert result["top_alerts"][0]["alert_type"] == "风险回避"
    assert result["top_opportunities"][0]["action"] == "接近可参与窗口"
    assert result["top_holdings_to_handle"][0]["action"] == "纪律止损"
    assert result["top_holdings_stable"][0]["action"] == "继续持有"
    assert result["today_action_queue"][0]["target_path"] == "/home/alerts"
    assert alert_service.refresh_calls == 0


def test_ashare_daily_workbench_service_refresh_runs_explicit_side_effects_only() -> None:
    alert_service = FakeDecisionAlertPersistenceService()
    holding_exit_service = FakeHoldingExitSignalService()
    service = AShareDailyWorkbenchService(
        homepage_context_service=cast(Any, FakeHomepageContextService()),
        opportunity_pool_service=cast(Any, FakeOpportunityPoolService()),
        entry_timing_service=cast(Any, FakeEntryTimingService()),
        decision_alert_persistence_service=cast(Any, alert_service),
        holding_exit_signal_service=cast(Any, holding_exit_service),
        holding_service=cast(Any, FakeHoldingService()),
    )

    result = service.refresh("default_user")

    assert result["success"] is True
    assert result["refreshed_alert_count"] == 2
    assert result["refreshed_holding_signal_count"] == 3
    assert result["near_entry_count"] == 1
    assert result["holding_action_count"] == 2
    assert alert_service.refresh_calls == 1
    assert holding_exit_service.refresh_calls == 3
