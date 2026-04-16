from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.ashare_daily_snapshot import (
    create_ashare_daily_snapshot_router,
)


class FakeAShareDailySnapshotService:
    def list_snapshots(
        self,
        *,
        user_id: str,
        limit: int = 20,
        include_today: bool = True,
    ):
        return {
            "generated_at": "2025-04-10T11:05:00Z",
            "count": 1,
            "items": [
                {
                    "snapshot_date": "2025-04-10",
                    "generated_at": "2025-04-10T10:55:00Z",
                    "market_digest": {
                        "market_state": "震荡偏强",
                        "emotion_stage": "主升分歧",
                    },
                    "attention_digest": {
                        "risk_alert_count": 1,
                        "near_entry_count": 2,
                        "holding_risk_count": 2,
                        "holding_profit_protection_count": 1,
                        "unread_alert_count": 3,
                    },
                    "brief_action_queue": ["先看风险回避提醒"],
                    "top_opportunity_count": 1,
                    "top_holding_action_count": 1,
                }
            ],
        }

    def get_snapshot_detail(self, *, user_id: str, snapshot_date: str):
        return {
            "snapshot_date": snapshot_date,
            "generated_at": "2025-04-10T10:55:00Z",
            "market_digest": {"market_state": "震荡偏强"},
            "attention_digest": {"risk_alert_count": 1},
            "top_alerts": [],
            "top_opportunities": [],
            "top_holdings_to_handle": [],
            "top_holdings_stable": [],
            "today_action_queue": [
                {
                    "title": "先看风险回避提醒",
                    "reason": "风险优先。",
                    "target_path": "/home/alerts",
                }
            ],
            "metadata": {"top_opportunity_count": 1},
        }

    def refresh_today_snapshot(self, *, user_id: str):
        return {
            "generated_at": "2025-04-10T11:06:00Z",
            "snapshot_date": "2025-04-10",
            "created_or_updated": "created",
            "summary": "已记录今日快照。",
            "snapshot": {
                "snapshot_date": "2025-04-10",
                "generated_at": "2025-04-10T10:55:00Z",
                "market_digest": {"market_state": "震荡偏强"},
                "attention_digest": {"risk_alert_count": 1},
                "top_alerts": [],
                "top_opportunities": [],
                "top_holdings_to_handle": [],
                "top_holdings_stable": [],
                "today_action_queue": [],
                "metadata": {},
            },
        }


def test_ashare_daily_snapshot_router_supports_list_detail_and_refresh(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.ashare_daily_snapshot.get_ashare_daily_snapshot_service",
        lambda: FakeAShareDailySnapshotService(),
    )
    app = FastAPI()
    app.include_router(create_ashare_daily_snapshot_router(), prefix="/api/v1")
    client = TestClient(app)

    list_response = client.get("/api/v1/ashare-workbench/snapshots?limit=20&include_today=true")
    detail_response = client.get("/api/v1/ashare-workbench/snapshots/2025-04-10")
    refresh_response = client.post("/api/v1/ashare-workbench/snapshots/refresh")

    assert list_response.status_code == 200
    assert list_response.json()["data"]["count"] == 1
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["snapshot_date"] == "2025-04-10"
    assert refresh_response.status_code == 200
    assert refresh_response.json()["data"]["created_or_updated"] == "created"
