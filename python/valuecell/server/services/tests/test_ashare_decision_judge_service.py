from __future__ import annotations

from typing import Any, cast

from valuecell.server.services.assets.ashare_decision_judge_service import (
    AShareDecisionJudgeService,
)


class FakeContextService:
    def __init__(self, *, available: bool = True, has_position: bool = False) -> None:
        self.available = available
        self.has_position = has_position

    def get_decision_context(
        self,
        *,
        ticker: str,
        user_id: str = "default_user",
    ) -> dict[str, Any]:
        if not self.available:
            return {
                "generated_at": "2025-04-10T10:20:00Z",
                "ticker": ticker,
                "available": False,
                "empty_message": "当前 ticker 暂无可用裁决上下文",
                "market_context": {},
                "theme_context": {},
                "candidate_context": {},
                "entry_timing_context": {},
                "alert_context": {"active_count": 0, "items": []},
                "preference_context": {},
                "portfolio_context": {
                    "has_position": False,
                    "summary": None,
                    "latest_action": None,
                    "risk_level": None,
                    "market_snapshot": None,
                },
                "risk_context": {"items": []},
                "missing_context": ["缺少机会池候选", "缺少买点信号"],
                "rule_based_judgement": {
                    "action": "继续观察",
                    "summary": "当前缺少足够上下文，先观察。",
                    "reasons": [],
                    "missing_confirmations": ["缺少候选"],
                    "invalid_conditions": [],
                },
                "agent_prompt_preview": "prompt",
            }

        return {
            "generated_at": "2025-04-10T10:20:00Z",
            "ticker": ticker,
            "available": True,
            "empty_message": None,
            "market_context": {
                "market_state": "震荡偏强",
                "emotion_stage": "主升分歧",
                "temperature_score": 68,
                "action_rhythm": "优先看强趋势核心票，等待确认后处理。",
                "summary": "指数震荡，主线保持活跃。",
            },
            "theme_context": {
                "topic_name": "AI算力",
                "source_tags": ["watchlist", "theme_resonance"],
                "role_label": "龙头",
                "trend_quality": "顺势",
            },
            "candidate_context": {
                "priority_score": 84,
                "candidate_state": "高优先级买点",
                "tradeability_state": "谨慎追高",
                "expectation_gap_level": "高",
                "matched_preferences": ["偏好龙头/核心"],
                "preference_adjustments": [{"label": "偏好龙头", "delta": 8}],
                "reasons": ["主线题材共振。"],
                "time_horizon": "1-2周",
            },
            "entry_timing_context": {
                "action": "接近可参与窗口",
                "confidence": 76,
                "summary": "处于较优观察阶段，但仍需等待进一步确认。",
                "reasons": ["与主线题材共振。"],
                "missing_confirmations": ["等待承接确认。"],
                "invalid_conditions": [],
            },
            "alert_context": {
                "active_count": 1,
                "items": [
                    {
                        "title": "中际旭创 接近可参与窗口",
                        "body": "当前更接近可参与窗口，但仍需确认。",
                    }
                ],
            },
            "preference_context": {
                "template_id": "trend_continuation",
                "template_title": "趋势延续",
                "risk_style": "balanced",
                "buy_style": "right_side",
                "preferred_themes": ["AI算力"],
                "avoid_risks": ["ST", "流动性风险"],
            },
            "portfolio_context": {
                "has_position": self.has_position,
                "summary": "已有仓位，先观察强趋势是否延续。" if self.has_position else None,
                "latest_action": "持有观察" if self.has_position else None,
                "risk_level": "medium" if self.has_position else None,
                "market_snapshot": {"price": 123.4} if self.has_position else None,
            },
            "risk_context": {
                "items": [
                    "当前处于谨慎追高区间，更适合等待回踩确认。",
                    "存在流动性风险，需优先考虑退出条件。",
                ]
            },
            "missing_context": ["当前持仓系统没有该 ticker 的持仓摘要。"] if not self.has_position else [],
            "rule_based_judgement": {
                "action": "接近可参与窗口",
                "summary": "当前为规则版裁决摘要，仍需继续确认。",
                "reasons": ["主线题材共振。"],
                "missing_confirmations": ["等待承接确认。"],
                "invalid_conditions": [],
            },
            "agent_prompt_preview": "请输出 JSON。",
        }


class FakeDecisionAlertPersistenceService:
    def __init__(self) -> None:
        self.refresh_calls = 0

    def refresh_alerts(self, user_id: str = "default_user") -> dict[str, Any]:
        self.refresh_calls += 1
        return {
            "items": [],
            "count": 0,
        }


def test_decision_judge_service_returns_rule_fallback_when_context_missing() -> None:
    service = AShareDecisionJudgeService(
        context_service=cast(Any, FakeContextService(available=False)),
        decision_alert_persistence_service=cast(Any, FakeDecisionAlertPersistenceService()),
    )

    result = service.judge(ticker="SZSE:000001", enable_agent=False)

    assert result["available"] is False
    assert result["mode"] == "rule_fallback"
    assert result["agent_enabled"] is False
    assert result["action"] == "继续观察"
    assert result["confidence"] <= 40


def test_decision_judge_service_degrades_for_risk_and_cautious_chasing() -> None:
    service = AShareDecisionJudgeService(
        context_service=cast(Any, FakeContextService()),
        decision_alert_persistence_service=cast(Any, FakeDecisionAlertPersistenceService()),
    )

    result = service.judge(ticker="SZSE:300308", enable_agent=False)

    assert result["mode"] == "rule_fallback"
    assert result["action"] == "暂不参与"
    assert len(result["risk_controls"]) >= 2
    assert result["agent_unavailable_reason"]


def test_decision_judge_service_marks_refresh_only_when_requested() -> None:
    refresh_service = FakeDecisionAlertPersistenceService()
    service = AShareDecisionJudgeService(
        context_service=cast(Any, FakeContextService(has_position=True)),
        decision_alert_persistence_service=cast(Any, refresh_service),
    )

    result = service.judge(
        ticker="SZSE:300308",
        enable_agent=True,
        force_refresh_context=True,
        user_note="不接受追高",
    )

    assert refresh_service.refresh_calls == 1
    assert result["mode"] == "rule_fallback"
    assert result["agent_enabled"] is False
    assert any("用户补充说明" in item for item in result["evidence"])
