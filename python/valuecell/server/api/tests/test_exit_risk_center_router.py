from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.exit_risk_center import create_exit_risk_center_router


class FakeExitRiskCenterService:
    def get_overview(self, user_id: str = "default_user"):
        return {
            "generated_at": "2025-04-11T10:00:00Z",
            "available": True,
            "empty_message": None,
            "high_priority_items": [
                {
                    "holding_id": 1,
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "action": "保护利润",
                    "confidence": 65,
                    "risk_type": "保护利润",
                    "summary": "优先保护利润。",
                    "thesis": "高位分歧加大。",
                    "evidence": ["已有浮盈"],
                    "disagreement": ["题材未完全走坏"],
                    "invalid_conditions": ["跌破承接位"],
                    "risk_controls": ["先收缩风险"],
                    "liquidity_warning": None,
                    "expected_exit_plan": "优先收缩风险。",
                    "has_active_alerts": True,
                    "theme_name": "AI算力",
                    "role_label": "龙头",
                }
            ],
            "profit_protection_items": [],
            "discipline_stop_items": [],
            "watch_items": [],
            "risk_buckets": {"保护利润": 1},
            "count": 1,
        }

    def refresh(self, user_id: str = "default_user"):
        return {**self.get_overview(user_id), "refreshed_count": 1}


def test_exit_risk_center_router_supports_overview_and_refresh(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.exit_risk_center.get_exit_risk_center_service",
        lambda: FakeExitRiskCenterService(),
    )
    app = FastAPI()
    app.include_router(create_exit_risk_center_router(), prefix="/api/v1")
    client = TestClient(app)

    overview_response = client.get("/api/v1/exit-risk-center/overview")
    refresh_response = client.post("/api/v1/exit-risk-center/refresh")

    assert overview_response.status_code == 200
    assert overview_response.json()["data"]["count"] == 1
    assert refresh_response.status_code == 200
    assert refresh_response.json()["data"]["refreshed_count"] == 1
