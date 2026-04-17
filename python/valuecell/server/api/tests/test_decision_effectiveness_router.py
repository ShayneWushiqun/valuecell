from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.decision_effectiveness import (
    create_decision_effectiveness_router,
)


class FakeDecisionEffectivenessService:
    def get_summary(self, *, user_id: str):
        return {
            "generated_at": "2025-04-20T10:00:00Z",
            "available": True,
            "empty_message": None,
            "overall_summary": "最近样本以继续持有更稳为主。",
            "overall_score": 72,
            "review_count": 5,
            "effective_count": 2,
            "partially_effective_count": 1,
            "failed_count": 1,
            "observing_count": 1,
            "insufficient_count": 0,
            "action_breakdown": [],
            "role_breakdown": [],
            "theme_breakdown": [],
            "recent_successes": [],
            "recent_failures": [],
        }


def test_decision_effectiveness_router_returns_summary(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.decision_effectiveness.get_decision_effectiveness_service",
        lambda: FakeDecisionEffectivenessService(),
    )
    app = FastAPI()
    app.include_router(create_decision_effectiveness_router(), prefix="/api/v1")
    client = TestClient(app)

    response = client.get("/api/v1/decision-effectiveness/summary")

    assert response.status_code == 200
    assert response.json()["data"]["overall_score"] == 72
    assert response.json()["data"]["review_count"] == 5
