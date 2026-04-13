from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.ashare_decision_context import (
    create_ashare_decision_context_router,
)


class FakeAShareDecisionContextService:
    def get_decision_context(self, *, ticker: str, user_id: str = "default_user"):
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
                "priority_score": 89,
                "candidate_state": "高优先级买点",
                "tradeability_state": "可观察",
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
                        "id": 11,
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
                ],
            },
            "preference_context": {
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
            },
            "portfolio_context": {
                "has_position": False,
                "summary": None,
                "latest_action": None,
                "risk_level": None,
                "market_snapshot": None,
            },
            "risk_context": {"items": ["当前处于谨慎追高区间，更适合等待回踩确认。"]},
            "missing_context": ["当前持仓系统没有该 ticker 的持仓摘要。"],
            "rule_based_judgement": {
                "action": "接近可参与窗口",
                "summary": "当前为规则版裁决摘要，仍需继续确认。",
                "reasons": ["主线题材共振。"],
                "missing_confirmations": ["等待承接确认。"],
                "invalid_conditions": [],
            },
            "agent_prompt_preview": "请围绕 A 股短周期 1 到 4 周视角分析。",
        }


def test_ashare_decision_context_router_returns_structured_response(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.ashare_decision_context.get_ashare_decision_context_service",
        lambda: FakeAShareDecisionContextService(),
    )
    app = FastAPI()
    app.include_router(create_ashare_decision_context_router(), prefix="/api/v1")
    client = TestClient(app)

    response = client.get("/api/v1/ashare-decision/context?ticker=SZSE:300308")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"]["ticker"] == "SZSE:300308"
    assert payload["data"]["rule_based_judgement"]["action"] == "接近可参与窗口"
    assert payload["data"]["alert_context"]["active_count"] == 1
