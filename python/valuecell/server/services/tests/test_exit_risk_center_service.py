from __future__ import annotations

from typing import Any, cast

from valuecell.server.services.assets.exit_risk_center_service import ExitRiskCenterService


class FakeHoldingService:
    def list_holdings(self, user_id: str = "default_user") -> list[dict[str, Any]]:
        return [
            {"id": 1, "ticker": "SZSE:300308", "asset_name": "中际旭创"},
            {"id": 2, "ticker": "SZSE:000001", "asset_name": "平安银行"},
        ]


class FakeHoldingExitSignalService:
    def __init__(self) -> None:
        self.refresh_calls = 0

    def list_exit_signals(self, user_id: str = "default_user") -> dict[str, Any]:
        return {
            "generated_at": "2025-04-11T10:00:00Z",
            "items": [
                {
                    "holding_id": 1,
                    "ticker": "SZSE:300308",
                    "asset_name": "中际旭创",
                    "action": "保护利润",
                    "confidence": 65,
                    "summary": "优先保护利润。",
                    "thesis": "高位分歧加大。",
                    "evidence": ["已有浮盈"],
                    "disagreement": ["题材未完全走坏"],
                    "invalid_conditions": ["跌破承接位"],
                    "risk_controls": ["先收缩风险"],
                    "context_snapshot": {
                        "decision_context": {
                            "theme_context": {
                                "topic_name": "AI算力",
                                "role_label": "龙头",
                                "trend_quality": "顺势",
                            },
                            "risk_context": {"items": ["谨慎追高"]},
                        }
                    },
                },
                {
                    "holding_id": 2,
                    "ticker": "SZSE:000001",
                    "asset_name": "平安银行",
                    "action": "纪律止损",
                    "confidence": 56,
                    "summary": "逻辑失效。",
                    "thesis": "非核心票掉队。",
                    "evidence": ["走弱明显"],
                    "disagreement": ["有反抽预期"],
                    "invalid_conditions": ["量能持续缩减"],
                    "risk_controls": ["注意退出难度"],
                    "context_snapshot": {
                        "decision_context": {
                            "theme_context": {
                                "topic_name": "银行",
                                "role_label": "跟风",
                                "trend_quality": "走弱",
                            },
                            "risk_context": {"items": ["存在流动性风险，需优先考虑退出条件。"]},
                        }
                    },
                },
            ],
            "count": 2,
        }

    def get_exit_signal(
        self,
        *,
        user_id: str,
        holding_id: int,
        force_refresh: bool = False,
    ) -> dict[str, Any] | None:
        if force_refresh:
            self.refresh_calls += 1
        return None


class FakeDecisionAlertPersistenceService:
    def list_alerts(
        self,
        *,
        user_id: str,
        status: str = "all",
        alert_type: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        return {"items": [{"ticker": "SZSE:300308"}], "count": 1}


def test_exit_risk_center_service_builds_risk_groups_and_refresh() -> None:
    exit_signal_service = FakeHoldingExitSignalService()
    service = ExitRiskCenterService(
        holding_service=cast(Any, FakeHoldingService()),
        holding_exit_signal_service=cast(Any, exit_signal_service),
        decision_alert_persistence_service=cast(Any, FakeDecisionAlertPersistenceService()),
    )

    overview = service.get_overview("default_user")
    refreshed = service.refresh("default_user")

    assert overview["available"] is True
    assert len(overview["high_priority_items"]) == 2
    assert len(overview["profit_protection_items"]) == 1
    assert len(overview["discipline_stop_items"]) == 1
    assert overview["risk_buckets"]["保护利润"] == 1
    assert refreshed["refreshed_count"] == 2
    assert exit_signal_service.refresh_calls == 2
