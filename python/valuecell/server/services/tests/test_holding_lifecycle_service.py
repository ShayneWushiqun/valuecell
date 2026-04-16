from __future__ import annotations

from typing import Any, cast

from valuecell.server.services.assets.holding_lifecycle_service import HoldingLifecycleService


class FakeHoldingService:
    def list_holdings(self, user_id: str = "default_user") -> list[dict[str, Any]]:
        return [
            {"id": 1, "ticker": "SZSE:300308", "asset_name": "中际旭创"},
            {"id": 2, "ticker": "SZSE:000001", "asset_name": "平安银行"},
        ]


class FakeHoldingExitSignalService:
    def list_exit_signals(self, user_id: str = "default_user") -> dict[str, Any]:
        return {
            "generated_at": "2025-04-11T10:00:00Z",
            "items": [
                {
                    "holding_id": 1,
                    "ticker": "SZSE:300308",
                    "action": "继续持有",
                    "confidence": 66,
                    "summary": "趋势未坏，继续跟踪。",
                    "invalid_conditions": ["跌破关键承接位。"],
                    "risk_controls": ["不追高。"],
                    "profit_protection_view": "当前以继续跟踪为主。",
                    "context_snapshot": {
                        "decision_context": {
                            "available": True,
                            "theme_context": {
                                "topic_name": "AI算力",
                                "role_label": "龙头",
                                "trend_quality": "顺势",
                            },
                            "candidate_context": {
                                "tradeability_state": "可观察",
                                "expectation_gap_level": "中",
                            },
                            "risk_context": {"items": []},
                            "market_context": {"market_state": "震荡偏强"},
                        }
                    },
                },
                {
                    "holding_id": 2,
                    "ticker": "SZSE:000001",
                    "action": "纪律止损",
                    "confidence": 58,
                    "summary": "逻辑明显走弱。",
                    "invalid_conditions": ["量价继续失衡。"],
                    "risk_controls": ["优先考虑退出难度。"],
                    "profit_protection_view": "先收缩风险。",
                    "context_snapshot": {
                        "decision_context": {
                            "available": True,
                            "theme_context": {
                                "topic_name": "银行",
                                "role_label": "跟风",
                                "trend_quality": "走弱",
                            },
                            "candidate_context": {
                                "tradeability_state": "流动性风险",
                                "expectation_gap_level": "低",
                            },
                            "risk_context": {"items": ["存在流动性风险"]},
                            "market_context": {"market_state": "偏弱震荡"},
                        }
                    },
                },
            ],
            "count": 2,
        }


class FakeDecisionAlertPersistenceService:
    def list_alerts(
        self,
        *,
        user_id: str,
        status: str = "all",
        alert_type: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        return {"items": [{"ticker": "SZSE:000001"}], "count": 1}


class FakeHomepageContextService:
    def get_homepage_context(self, user_id: str = "default_user") -> dict[str, Any]:
        return {"market_overview": {"market_state": "偏弱震荡"}, "emotion_cycle": {}}


def test_holding_lifecycle_service_builds_stage_view() -> None:
    service = HoldingLifecycleService(
        holding_service=cast(Any, FakeHoldingService()),
        holding_exit_signal_service=cast(Any, FakeHoldingExitSignalService()),
        decision_alert_persistence_service=cast(Any, FakeDecisionAlertPersistenceService()),
        homepage_context_service=cast(Any, FakeHomepageContextService()),
    )

    result = service.get_overview("default_user")

    assert result["available"] is True
    assert result["count"] == 2
    assert result["items"][0]["lifecycle_stage"] == "破逻辑退出期"
    assert result["items"][1]["lifecycle_stage"] == "主升持有期"
    assert result["summary"]["high_risk_count"] == 1
