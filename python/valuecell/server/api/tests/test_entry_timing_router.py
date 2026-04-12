from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.entry_timing import create_entry_timing_router


class FakeEntryTimingService:
    def get_entry_timing_signals(self, user_id: str = "default_user"):
        return {
            "generated_at": "2025-04-10T10:00:00Z",
            "available": True,
            "items": [
                {
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "topic_name": "AI算力",
                    "action": "接近可参与窗口",
                    "confidence": 74,
                    "summary": "接近可参与窗口，但仍需等待进一步确认。",
                    "reasons": ["与主线题材共振。"],
                    "tradeability_state": "可观察",
                    "expectation_gap_view": "预期差中性，等待更明确的交易窗口。",
                    "missing_confirmations": ["仍需等待更明确的承接或回踩确认。"],
                    "invalid_conditions": [],
                    "candidate_state": "高优先级买点",
                    "priority_score": 88,
                    "time_horizon": "1-2周",
                }
            ],
            "count": 1,
            "empty_message": None,
        }


def test_entry_timing_router_returns_structured_response(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.entry_timing.get_entry_timing_service",
        lambda: FakeEntryTimingService(),
    )
    app = FastAPI()
    app.include_router(create_entry_timing_router(), prefix="/api/v1")
    client = TestClient(app)

    response = client.get("/api/v1/entry-timing/signals")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"]["available"] is True
    assert payload["data"]["items"][0]["action"] == "接近可参与窗口"
    assert payload["data"]["items"][0]["confidence"] == 74
