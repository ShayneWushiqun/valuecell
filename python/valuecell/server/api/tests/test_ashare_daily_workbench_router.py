from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.ashare_daily_workbench import (
    create_ashare_daily_workbench_router,
)


class FakeAShareDailyWorkbenchService:
    def get_overview(self, user_id: str = "default_user"):
        return {
            "generated_at": "2025-04-10T10:50:00Z",
            "available": True,
            "empty_message": None,
            "market_digest": {
                "market_state": "震荡偏强",
                "emotion_stage": "主升分歧",
                "temperature_score": 68,
                "action_rhythm": "先看风险，再看持仓，再看机会。",
                "summary": "指数震荡，主线保持活跃。",
            },
            "attention_digest": {
                "unread_alert_count": 3,
                "risk_alert_count": 1,
                "near_entry_count": 2,
                "holding_risk_count": 2,
                "holding_profit_protection_count": 1,
            },
            "top_alerts": [
                {
                    "id": 1,
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "alert_type": "风险回避",
                    "priority": "high",
                    "title": "中际旭创 当前应风险回避",
                    "body": "先回避高波动。",
                    "next_action": "先观察。",
                }
            ],
            "top_opportunities": [
                {
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "topic_name": "AI算力",
                    "action": "接近可参与窗口",
                    "candidate_state": "高优先级买点",
                    "tradeability_state": "可观察",
                    "priority_score": 88,
                }
            ],
            "top_holdings_to_handle": [
                {
                    "holding_id": 1,
                    "ticker": "SZSE:300308",
                    "asset_name": "中际旭创",
                    "action": "纪律止损",
                    "confidence": 70,
                    "summary": "优先收缩风险。",
                    "profit_protection_view": "先控制回撤。",
                }
            ],
            "top_holdings_stable": [
                {
                    "holding_id": 2,
                    "ticker": "SZSE:000001",
                    "asset_name": "平安银行",
                    "action": "继续持有",
                    "confidence": 58,
                    "summary": "逻辑未坏。",
                    "profit_protection_view": "继续跟踪利润变化。",
                }
            ],
            "today_action_queue": [
                {
                    "title": "先看风险回避提醒",
                    "reason": "风险优先。",
                    "target_path": "/home/alerts",
                }
            ],
            "quick_links": {
                "opportunities": "/home/opportunities",
                "alerts": "/home/alerts",
                "strategy_preferences": "/home/strategy-preferences",
                "portfolio": "/home",
            },
        }

    def refresh(self, user_id: str = "default_user"):
        return {
            "generated_at": "2025-04-10T10:55:00Z",
            "success": True,
            "message": "总控台已更新。",
            "refreshed_alert_count": 2,
            "refreshed_holding_signal_count": 3,
            "opportunity_candidate_count": 5,
            "near_entry_count": 2,
            "holding_action_count": 2,
        }


def test_ashare_daily_workbench_router_returns_overview_and_refresh(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.ashare_daily_workbench.get_ashare_daily_workbench_service",
        lambda: FakeAShareDailyWorkbenchService(),
    )
    app = FastAPI()
    app.include_router(create_ashare_daily_workbench_router(), prefix="/api/v1")
    client = TestClient(app)

    overview_response = client.get("/api/v1/ashare-workbench/overview")
    refresh_response = client.post("/api/v1/ashare-workbench/refresh")

    assert overview_response.status_code == 200
    assert overview_response.json()["data"]["attention_digest"]["unread_alert_count"] == 3
    assert refresh_response.status_code == 200
    assert refresh_response.json()["data"]["refreshed_holding_signal_count"] == 3
