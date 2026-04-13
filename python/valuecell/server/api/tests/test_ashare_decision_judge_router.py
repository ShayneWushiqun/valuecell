from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.ashare_decision_judge import (
    create_ashare_decision_judge_router,
)


class FakeAShareDecisionJudgeService:
    def judge(
        self,
        *,
        ticker: str,
        user_id: str = "default_user",
        enable_agent: bool = False,
        force_refresh_context: bool = False,
        user_note: str | None = None,
    ):
        return {
            "generated_at": "2025-04-10T10:40:00Z",
            "ticker": ticker,
            "available": True,
            "mode": "rule_fallback",
            "agent_enabled": False,
            "agent_unavailable_reason": "当前仅支持规则 fallback。",
            "action": "继续观察",
            "confidence": 38,
            "summary": "当前仍需继续观察，不构成买入指令。",
            "thesis": "证据仍不足以把动作提升到更激进层级。",
            "evidence": ["市场状态偏震荡。"],
            "disagreement": ["题材有热度，但确认不足。"],
            "missing_confirmations": ["仍需确认承接。"],
            "invalid_conditions": ["若情绪继续转弱，当前判断失效。"],
            "risk_controls": ["不追高。", "先确认流动性。"],
            "time_horizon": "1-4周",
            "context_snapshot": {"ticker": ticker},
            "raw_agent_output": None,
            "empty_message": None,
        }


def test_ashare_decision_judge_router_returns_structured_response(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.ashare_decision_judge.get_ashare_decision_judge_service",
        lambda: FakeAShareDecisionJudgeService(),
    )
    app = FastAPI()
    app.include_router(create_ashare_decision_judge_router(), prefix="/api/v1")
    client = TestClient(app)

    response = client.post(
        "/api/v1/ashare-decision/judge",
        json={
            "ticker": "SZSE:300308",
            "enable_agent": False,
            "force_refresh_context": False,
            "user_note": "先看承接",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"]["ticker"] == "SZSE:300308"
    assert payload["data"]["mode"] == "rule_fallback"
    assert payload["data"]["action"] == "继续观察"
