from __future__ import annotations

from typing import Any, cast

from valuecell.server.services.assets.risk_sizing_service import RiskSizingService


class FakeHomepageContextService:
    def get_homepage_context(self, user_id: str) -> dict[str, Any]:
        return {
            "market_overview": {"market_state": "修复"},
            "emotion_cycle": {"cycle_stage": "修复试错"},
            "risk_control": {"total_position_range": "3-5成"},
        }


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
                    "tradeability_state": "可低吸",
                },
                {
                    "holding_id": 2,
                    "ticker": "SZSE:688256",
                    "display_name": "寒武纪",
                    "lifecycle_stage": "退潮减仓期",
                    "action": "减仓观察",
                    "theme_name": "AI算力",
                    "role_label": "跟风",
                    "tradeability_state": "谨慎追高",
                },
            ],
            "count": 2,
        }


class FakeExitRiskCenterService:
    def get_overview(self, user_id: str) -> dict[str, Any]:
        risk_item = {
            "ticker": "SZSE:688256",
            "display_name": "寒武纪",
            "action": "保护利润",
            "risk_type": "节奏转弱",
            "liquidity_warning": "当前存在退出难度或流动性压力，处理时需要优先考虑成交与滑点风险。",
        }
        return {
            "high_priority_items": [risk_item],
            "profit_protection_items": [risk_item],
            "discipline_stop_items": [],
            "watch_items": [],
        }


class FakeOpportunityPoolService:
    def get_opportunity_candidates(self, user_id: str) -> dict[str, Any]:
        return {
            "items": [
                {
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "topic_name": "AI算力",
                    "candidate_state": "高优先级买点",
                    "tradeability_state": "可低吸",
                    "role_label": "龙头",
                },
                {
                    "ticker": "SZSE:000001",
                    "display_name": "平安银行",
                    "topic_name": "金融",
                    "candidate_state": "候选买点",
                    "tradeability_state": "可观察",
                    "role_label": "中军",
                },
            ]
        }


class FakeAShareDecisionJudgeService:
    def judge(
        self,
        *,
        ticker: str,
        user_id: str = "default_user",
        enable_agent: bool = False,
        force_refresh_context: bool = False,
        user_note: str | None = None,
    ) -> dict[str, Any]:
        return {
            "ticker": ticker,
            "summary": f"{ticker} 需要继续确认承接，不外推成交易指令。",
        }


class FakeStrategyPreferenceService:
    def get_effective_profile(self, user_id: str = "default_user") -> dict[str, Any]:
        return {
            "risk_style": "steady",
            "buy_style": "pullback",
            "accept_high_position": False,
        }


def test_risk_sizing_service_builds_summary_and_ticker_suggestions() -> None:
    service = RiskSizingService(
        homepage_context_service=cast(Any, FakeHomepageContextService()),
        holding_lifecycle_service=cast(Any, FakeHoldingLifecycleService()),
        exit_risk_center_service=cast(Any, FakeExitRiskCenterService()),
        opportunity_pool_service=cast(Any, FakeOpportunityPoolService()),
        ashare_decision_judge_service=cast(Any, FakeAShareDecisionJudgeService()),
        strategy_preference_service=cast(Any, FakeStrategyPreferenceService()),
    )

    result = service.get_summary(user_id="default_user")

    assert result["available"] is True
    assert result["market_risk_level"] == "中性"
    assert result["suggested_total_exposure_range"] == "30% - 50%"
    assert result["suggested_new_position_range"] == "4% - 7%"
    assert result["ticker_suggestions"]
    assert result["ticker_suggestions"][0]["ticker"] == "SZSE:688256"


def test_risk_sizing_service_builds_ticker_detail_with_conservative_ranges() -> None:
    service = RiskSizingService(
        homepage_context_service=cast(Any, FakeHomepageContextService()),
        holding_lifecycle_service=cast(Any, FakeHoldingLifecycleService()),
        exit_risk_center_service=cast(Any, FakeExitRiskCenterService()),
        opportunity_pool_service=cast(Any, FakeOpportunityPoolService()),
        ashare_decision_judge_service=cast(Any, FakeAShareDecisionJudgeService()),
        strategy_preference_service=cast(Any, FakeStrategyPreferenceService()),
    )

    result = service.get_ticker_summary(
        user_id="default_user",
        ticker="SZSE:300308",
    )

    assert result["available"] is True
    assert result["risk_level"] in {"低", "中", "高"}
    assert "%" in result["suggested_position_range"]
    assert "轻仓试错" in result["summary"]
    assert result["reasons"]
