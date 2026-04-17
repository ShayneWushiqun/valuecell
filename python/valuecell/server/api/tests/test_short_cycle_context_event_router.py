from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.short_cycle_context_event import (
    create_short_cycle_context_event_router,
)


class FakeShortCycleContextEventService:
    def list_events(self, *, user_id: str, ticker: str | None = None, limit: int = 200):
        return {
            "generated_at": "2025-04-11T10:00:00Z",
            "items": [
                {
                    "event_id": 1,
                    "user_id": user_id,
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "topic_name": "AI算力",
                    "layer": "theme",
                    "event_type": "theme_加强",
                    "source": "theme_radar",
                    "occurred_at": "2025-04-11T10:00:00Z",
                    "ingested_at": "2025-04-11T10:00:00Z",
                    "importance_score": 80,
                    "direction": "bullish",
                    "time_horizon": "10-40个交易日",
                    "tradeability_hint": "优先跟踪核心票。",
                    "summary": "题材继续加强。",
                    "payload_json": {},
                    "record_date": "2025-04-11",
                    "is_active": True,
                }
            ],
            "count": 1,
        }

    def get_event_detail(self, *, user_id: str, event_id: int):
        return self.list_events(user_id=user_id)["items"][0]

    def refresh_events(self, *, user_id: str, ticker: str | None = None):
        return self.list_events(user_id=user_id, ticker=ticker)


def test_short_cycle_context_event_router_supports_list_detail_refresh(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.short_cycle_context_event.get_short_cycle_context_event_service",
        lambda: FakeShortCycleContextEventService(),
    )
    app = FastAPI()
    app.include_router(create_short_cycle_context_event_router(), prefix="/api/v1")
    client = TestClient(app)

    list_response = client.get("/api/v1/short-cycle-context-events")
    detail_response = client.get("/api/v1/short-cycle-context-events/1")
    refresh_response = client.post("/api/v1/short-cycle-context-events/refresh", json={})

    assert list_response.status_code == 200
    assert list_response.json()["data"]["count"] == 1
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["event_id"] == 1
    assert refresh_response.status_code == 200
