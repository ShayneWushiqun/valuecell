from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.decision_alert import create_decision_alert_router


class FakeDecisionAlertPersistenceService:
    def get_decision_alert_summary(self, user_id: str = "default_user"):
        return {
            "generated_at": "2025-04-10T10:10:00Z",
            "available": True,
            "items": [
                {
                    "id": 1,
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

    def list_alerts(
        self,
        *,
        user_id: str,
        status: str = "all",
        alert_type: str | None = None,
        limit: int = 50,
    ):
        return {
            "generated_at": "2025-04-10T10:12:00Z",
            "unread_count": 1,
            "items": [
                {
                    "id": 1,
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
                    "read_at": None,
                    "dismissed_at": None,
                    "created_at": "2025-04-10T10:10:00Z",
                    "updated_at": "2025-04-10T10:10:00Z",
                }
            ],
            "count": 1,
        }

    def refresh_alerts(self, user_id: str = "default_user"):
        return self.list_alerts(user_id=user_id)

    def mark_alert_read(self, *, user_id: str, alert_id: int):
        item = self.list_alerts(user_id=user_id)["items"][0]
        return {
            **item,
            "read_at": "2025-04-10T10:30:00Z",
        }

    def mark_all_read(self, *, user_id: str):
        return {
            "generated_at": "2025-04-10T10:35:00Z",
            "updated_count": 1,
        }

    def dismiss_alert(self, *, user_id: str, alert_id: int):
        item = self.list_alerts(user_id=user_id)["items"][0]
        return {
            **item,
            "dismissed_at": "2025-04-10T10:40:00Z",
        }


def test_decision_alert_router_returns_structured_response(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.decision_alert.get_decision_alert_persistence_service",
        lambda: FakeDecisionAlertPersistenceService(),
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


def test_decision_alert_router_supports_list_refresh_and_state_updates(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.decision_alert.get_decision_alert_persistence_service",
        lambda: FakeDecisionAlertPersistenceService(),
    )
    app = FastAPI()
    app.include_router(create_decision_alert_router(), prefix="/api/v1")
    client = TestClient(app)

    list_response = client.get("/api/v1/decision-alerts")
    refresh_response = client.post("/api/v1/decision-alerts/refresh")
    read_response = client.put("/api/v1/decision-alerts/1/read")
    read_all_response = client.put("/api/v1/decision-alerts/read-all")
    dismiss_response = client.put("/api/v1/decision-alerts/1/dismiss")

    assert list_response.status_code == 200
    assert list_response.json()["data"]["unread_count"] == 1
    assert refresh_response.status_code == 200
    assert refresh_response.json()["data"]["count"] == 1
    assert read_response.status_code == 200
    assert read_response.json()["data"]["read_at"] is not None
    assert read_all_response.status_code == 200
    assert read_all_response.json()["data"]["updated_count"] == 1
    assert dismiss_response.status_code == 200
    assert dismiss_response.json()["data"]["dismissed_at"] is not None
