from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.decision_alert import create_decision_alert_router


class FakeDecisionAlertService:
    def get_decision_alert_summary(self, user_id: str = "default_user"):
        return {
            "generated_at": "2025-04-10T10:10:00Z",
            "available": True,
            "items": [
                {
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "topic_name": "AI算力",
                    "alert_type": "买点接近",
                    "priority": "high",
                    "title": "中际旭创 接近可参与窗口",
                    "body": "中际旭创 在 AI算力 方向进入接近可参与窗口的观察阶段。",
                    "next_action": "继续观察承接、量价与回踩确认。",
                    "action": "接近可参与窗口",
                    "confidence": 76,
                    "source": "entry_timing_signals",
                    "reasons": ["当前信号更接近可参与窗口，但仍需确认，不构成直接买入建议。"],
                }
            ],
            "count": 1,
            "empty_message": None,
        }


def test_decision_alert_router_returns_structured_response(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.decision_alert.get_decision_alert_service",
        lambda: FakeDecisionAlertService(),
    )
    app = FastAPI()
    app.include_router(create_decision_alert_router(), prefix="/api/v1")
    client = TestClient(app)

    response = client.get("/api/v1/decision-alerts/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"]["available"] is True
    assert payload["data"]["items"][0]["alert_type"] == "买点接近"
    assert payload["data"]["items"][0]["source"] == "entry_timing_signals"
