from __future__ import annotations

from typing import Any, cast

from valuecell.server.services.assets.ashare_decision_context_service import (
    AShareDecisionContextService,
)


class FakeHomepageContextService:
    def get_homepage_context(self, user_id: str = "default_user") -> dict[str, Any]:
        return {
            "market_overview": {
                "market_state": "震荡偏强",
                "score": 68,
                "summary": "指数震荡，主线保持活跃。",
            },
            "emotion_cycle": {
                "cycle_stage": "主升分歧",
            },
            "action_framework": {
                "summary": "优先看强趋势核心票，等待确认后处理。",
            },
        }


class FakeOpportunityPoolService:
    def get_opportunity_candidates(self, user_id: str = "default_user") -> dict[str, Any]:
        return {
            "items": [
                {
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "topic_name": "AI算力",
                    "priority_score": 89,
                    "candidate_state": "高优先级买点",
                    "tradeability_state": "可观察",
                    "expectation_gap_level": "高",
                    "matched_preferences": ["偏好龙头/核心", "偏好题材命中：AI算力"],
                    "preference_adjustments": [{"label": "偏好龙头", "delta": 8}],
                    "reasons": ["主线题材共振。"],
                    "time_horizon": "1-2周",
                    "source_tags": ["watchlist", "theme_resonance"],
                    "role_label": "龙头",
                    "trend_quality": "顺势",
                    "missing_confirmations": ["等待承接确认。"],
                    "invalid_conditions": [],
                }
            ]
        }


class FakeEntryTimingService:
    def get_entry_timing_signals(self, user_id: str = "default_user") -> dict[str, Any]:
        return {
            "items": [
                {
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "action": "接近可参与窗口",
                    "confidence": 76,
                    "summary": "处于较优观察阶段，但仍需等待进一步确认。",
                    "reasons": ["与主线题材共振。"],
                    "missing_confirmations": ["仍需等待更明确的承接或回踩确认。"],
                    "invalid_conditions": [],
                }
            ]
        }


class FakeDecisionAlertPersistenceService:
    def list_alerts(
        self,
        *,
        user_id: str,
        status: str = "active",
        alert_type: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        return {
            "items": [
                {
                    "id": 11,
                    "ticker": "SZSE:300308",
                    "alert_type": "买点接近",
                    "priority": "high",
                    "title": "中际旭创 接近可参与窗口",
                    "body": "当前更接近可参与窗口，但仍需确认。",
                    "next_action": "继续观察承接、量价与回踩确认。",
                    "action": "接近可参与窗口",
                    "confidence": 76,
                    "reasons": ["当前信号更接近可参与窗口，但仍需确认。"],
                    "read_at": None,
                    "dismissed_at": None,
                    "created_at": "2025-04-10T10:10:00Z",
                    "updated_at": "2025-04-10T10:10:00Z",
                }
            ]
        }


class FakeStrategyPreferenceService:
    def get_effective_profile(self, user_id: str = "default_user") -> dict[str, Any]:
        return {
            "template_id": "trend_continuation",
            "template_title": "趋势延续",
            "risk_style": "balanced",
            "buy_style": "right_side",
            "preferred_themes": ["AI算力"],
            "avoid_risks": ["ST", "流动性风险"],
            "accept_high_position": False,
            "prefer_expectation_gap": True,
            "prefer_leader_or_core": True,
            "note": "优先强趋势核心票。",
        }


class FakeHoldingService:
    def list_holdings(self, user_id: str = "default_user") -> list[dict[str, Any]]:
        return [
            {
                "ticker": "SZSE:300308",
                "market_snapshot": {"price": 123.4},
                "latest_diagnosis": {
                    "summary": "已有仓位，先观察强趋势是否延续。",
                    "action": "持有观察",
                    "risk_level": "medium",
                },
            }
        ]


def test_ashare_decision_context_service_builds_structured_context() -> None:
    service = AShareDecisionContextService(
        homepage_context_service=cast(Any, FakeHomepageContextService()),
        opportunity_pool_service=cast(Any, FakeOpportunityPoolService()),
        entry_timing_service=cast(Any, FakeEntryTimingService()),
        decision_alert_persistence_service=cast(Any, FakeDecisionAlertPersistenceService()),
        strategy_preference_service=cast(Any, FakeStrategyPreferenceService()),
        holding_service=cast(Any, FakeHoldingService()),
    )

    result = service.get_decision_context(ticker="SZSE:300308", user_id="default_user")

    assert result["available"] is True
    assert result["market_context"]["market_state"] == "震荡偏强"
    assert result["theme_context"]["role_label"] == "龙头"
    assert result["candidate_context"]["priority_score"] == 89
    assert result["entry_timing_context"]["action"] == "接近可参与窗口"
    assert result["alert_context"]["active_count"] == 1
    assert result["preference_context"]["template_id"] == "trend_continuation"
    assert result["portfolio_context"]["has_position"] is True
    assert result["rule_based_judgement"]["action"] == "接近可参与窗口"
    assert "不构成买入指令" in result["agent_prompt_preview"]


def test_ashare_decision_context_service_reports_missing_context_when_candidate_absent() -> None:
    service = AShareDecisionContextService(
        homepage_context_service=cast(Any, FakeHomepageContextService()),
        opportunity_pool_service=cast(Any, type("NoCandidatePool", (), {
            "get_opportunity_candidates": lambda self, user_id="default_user": {"items": []}
        })()),
        entry_timing_service=cast(Any, FakeEntryTimingService()),
        decision_alert_persistence_service=cast(Any, FakeDecisionAlertPersistenceService()),
        strategy_preference_service=cast(Any, FakeStrategyPreferenceService()),
        holding_service=cast(Any, type("NoHoldingService", (), {
            "list_holdings": lambda self, user_id="default_user": []
        })()),
    )

    result = service.get_decision_context(ticker="SZSE:000001", user_id="default_user")

    assert result["available"] is False
    assert result["empty_message"] == "当前 ticker 暂无可用裁决上下文"
    assert result["missing_context"]
