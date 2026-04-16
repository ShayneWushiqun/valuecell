from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.holding_lifecycle import create_holding_lifecycle_router


class FakeHoldingLifecycleService:
    def get_overview(self, user_id: str = "default_user"):
        return {
            "generated_at": "2025-04-11T10:00:00Z",
            "available": True,
            "empty_message": None,
            "items": [
                {
                    "holding_id": 1,
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "lifecycle_stage": "主升持有期",
                    "action": "继续持有",
                    "confidence": 66,
                    "summary": "趋势未坏。",
                    "theme_name": "AI算力",
                    "role_label": "龙头",
                    "trend_quality": "顺势",
                    "tradeability_state": "可观察",
                    "expectation_state": "中",
                    "observation_window": "未来 3-5 个交易日。",
                    "invalid_conditions": [],
                    "risk_controls": ["不追高"],
                    "profit_protection_view": "继续跟踪。",
                    "position_hint": "继续持有。",
                    "has_active_alerts": False,
                    "decision_context_available": True,
                }
            ],
            "count": 1,
            "summary": {
                "total_count": 1,
                "need_attention_count": 0,
                "major_hold_count": 1,
                "high_risk_count": 0,
                "active_alert_count": 0,
            },
        }

    def get_holding_lifecycle(self, *, user_id: str, holding_id: int):
        return {
            "generated_at": "2025-04-11T10:00:00Z",
            "available": True,
            "empty_message": None,
            "item": self.get_overview()["items"][0],
        }


def test_holding_lifecycle_router_supports_overview_and_detail(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.holding_lifecycle.get_holding_lifecycle_service",
        lambda: FakeHoldingLifecycleService(),
    )
    app = FastAPI()
    app.include_router(create_holding_lifecycle_router(), prefix="/api/v1")
    client = TestClient(app)

    overview_response = client.get("/api/v1/holding-lifecycle/overview")
    detail_response = client.get("/api/v1/holding-lifecycle/holdings/1")

    assert overview_response.status_code == 200
    assert overview_response.json()["data"]["summary"]["major_hold_count"] == 1
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["item"]["holding_id"] == 1
