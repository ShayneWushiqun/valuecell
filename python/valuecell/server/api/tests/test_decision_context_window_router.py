from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.decision_context_window import (
    create_decision_context_window_router,
)


class FakeDecisionContextWindowService:
    def list_windows(
        self,
        *,
        user_id: str,
        ticker: str | None = None,
        window_size: int | None = None,
        limit: int = 100,
    ):
        return {
            "generated_at": "2025-04-11T10:00:00Z",
            "items": [
                {
                    "window_id": 1,
                    "user_id": user_id,
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "topic_name": "AI算力",
                    "window_start": "2025-04-01",
                    "window_end": "2025-04-11",
                    "window_size": 10,
                    "market_state": "震荡偏强",
                    "position_state": "主升持有期",
                    "expectation_state": "中",
                    "tradeability_state": "可观察",
                    "role_label": "龙头",
                    "trend_quality": "顺势",
                    "exit_liquidity_plan": None,
                    "support_events_json": [],
                    "opposing_events_json": [],
                    "risk_events_json": [],
                    "summary": "当前仍适合解释型观察。",
                    "judgement_snapshot_json": {"action": "继续观察", "confidence": 54},
                    "available": True,
                    "linked_tags_json": ["holding"],
                    "risk_level": "低",
                    "disagreement_level": "低",
                    "support_count": 1,
                    "opposing_count": 0,
                    "risk_count": 0,
                    "has_holding": True,
                    "has_watchlist": False,
                    "has_opportunity": True,
                }
            ],
            "count": 1,
        }

    def get_window_detail(self, *, user_id: str, window_id: int):
        return self.list_windows(user_id=user_id)["items"][0]

    def refresh_windows(self, *, user_id: str, ticker: str | None = None):
        return self.list_windows(user_id=user_id, ticker=ticker)


def test_decision_context_window_router_supports_list_detail_refresh(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.decision_context_window.get_decision_context_window_service",
        lambda: FakeDecisionContextWindowService(),
    )
    app = FastAPI()
    app.include_router(create_decision_context_window_router(), prefix="/api/v1")
    client = TestClient(app)

    list_response = client.get("/api/v1/decision-context-windows")
    detail_response = client.get("/api/v1/decision-context-windows/1")
    refresh_response = client.post("/api/v1/decision-context-windows/refresh", json={})

    assert list_response.status_code == 200
    assert list_response.json()["data"]["count"] == 1
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["window_id"] == 1
    assert refresh_response.status_code == 200
