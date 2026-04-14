from __future__ import annotations

from typing import Any, cast

from valuecell.server.services.portfolio.holding_exit_signal_service import (
    HoldingExitSignalService,
)


class FakeHoldingService:
    def __init__(self, holding: dict[str, Any] | None = None) -> None:
        self.holding = holding

    def list_holdings(self, user_id: str = "default_user") -> list[dict[str, Any]]:
        return [self.holding] if self.holding else []

    def get_holding(self, user_id: str, holding_id: int) -> dict[str, Any] | None:
        if self.holding and int(self.holding["id"]) == holding_id:
            return self.holding
        return None


class FakeHoldingDiagnosisService:
    def __init__(self) -> None:
        self.refresh_calls = 0

    def refresh_latest_diagnosis(self, user_id: str, holding_id: int) -> dict[str, Any] | None:
        self.refresh_calls += 1
        return {"holding_id": holding_id}


class FakeDecisionContextService:
    def __init__(
        self,
        *,
        role_label: str = "龙头",
        trend_quality: str = "顺势",
        tradeability_state: str = "可观察",
        risk_items: list[str] | None = None,
        risk_style: str = "steady",
    ) -> None:
        self.role_label = role_label
        self.trend_quality = trend_quality
        self.tradeability_state = tradeability_state
        self.risk_items = risk_items or []
        self.risk_style = risk_style

    def get_decision_context(self, *, ticker: str, user_id: str = "default_user") -> dict[str, Any]:
        return {
            "ticker": ticker,
            "available": True,
            "theme_context": {
                "topic_name": "AI算力",
                "role_label": self.role_label,
                "trend_quality": self.trend_quality,
            },
            "candidate_context": {
                "candidate_state": "高优先级买点",
                "tradeability_state": self.tradeability_state,
            },
            "preference_context": {
                "risk_style": self.risk_style,
            },
            "portfolio_context": {
                "has_position": True,
                "summary": "已有仓位，先看承接。",
            },
            "risk_context": {
                "items": self.risk_items,
            },
        }


class FakeDecisionJudgeService:
    def __init__(self, *, action: str = "接近可参与窗口") -> None:
        self.action = action

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
            "action": self.action,
            "summary": "当前为规则版裁决摘要，仍需继续确认。",
            "invalid_conditions": [],
        }


def build_holding(
    *,
    profit_percent: float = 8.0,
    latest_change_percent: float = 1.5,
    diagnosis_action: str = "持有",
    diagnosis_risk: str = "中",
) -> dict[str, Any]:
    return {
        "id": 1,
        "ticker": "SZSE:300308",
        "asset_name": "中际旭创",
        "market_snapshot": {
            "current_price": 123.4,
            "latest_change_percent": latest_change_percent,
            "profit_percent": profit_percent,
        },
        "latest_diagnosis": {
            "action": diagnosis_action,
            "risk_level": diagnosis_risk,
            "invalid_conditions": [],
        },
    }


def test_holding_exit_signal_service_prefers_continue_hold_for_core_trend() -> None:
    service = HoldingExitSignalService(
        holding_service=cast(Any, FakeHoldingService(build_holding())),
        holding_diagnosis_service=cast(Any, FakeHoldingDiagnosisService()),
        decision_context_service=cast(
            Any,
                FakeDecisionContextService(
                    role_label="龙头",
                    trend_quality="顺势",
                    risk_style="balanced",
                ),
        ),
        decision_judge_service=cast(Any, FakeDecisionJudgeService(action="接近可参与窗口")),
    )

    result = service.get_exit_signal(user_id="default_user", holding_id=1)

    assert result is not None
    assert result["action"] == "继续持有"


def test_holding_exit_signal_service_prefers_profit_protection_when_profit_and_risk_show_up() -> None:
    service = HoldingExitSignalService(
        holding_service=cast(Any, FakeHoldingService(build_holding(profit_percent=16.0))),
        holding_diagnosis_service=cast(Any, FakeHoldingDiagnosisService()),
        decision_context_service=cast(
            Any,
            FakeDecisionContextService(
                tradeability_state="谨慎追高",
                risk_items=["当前处于谨慎追高区间，更适合等待回踩确认。"],
            ),
        ),
        decision_judge_service=cast(Any, FakeDecisionJudgeService(action="等待回踩确认")),
    )

    result = service.get_exit_signal(user_id="default_user", holding_id=1)

    assert result is not None
    assert result["action"] == "保护利润"
    assert "保护利润" in result["profit_protection_view"]


def test_holding_exit_signal_service_prefers_discipline_stop_for_weak_non_core_risk() -> None:
    diagnosis_service = FakeHoldingDiagnosisService()
    service = HoldingExitSignalService(
        holding_service=cast(
            Any,
            FakeHoldingService(
                build_holding(
                    profit_percent=-8.0,
                    latest_change_percent=-7.2,
                    diagnosis_action="减仓",
                    diagnosis_risk="高",
                )
            ),
        ),
        holding_diagnosis_service=cast(Any, diagnosis_service),
        decision_context_service=cast(
            Any,
            FakeDecisionContextService(
                role_label="跟风",
                trend_quality="走弱",
                risk_items=["存在流动性风险，需优先考虑退出条件。"],
            ),
        ),
        decision_judge_service=cast(Any, FakeDecisionJudgeService(action="暂不参与")),
    )

    result = service.get_exit_signal(user_id="default_user", holding_id=1, force_refresh=True)

    assert result is not None
    assert result["action"] == "纪律止损"
    assert diagnosis_service.refresh_calls == 1
