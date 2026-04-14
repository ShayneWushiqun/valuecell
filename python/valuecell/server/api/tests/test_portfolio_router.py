from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.portfolio import create_portfolio_router


class FakeHoldingService:
    def list_holdings(self, user_id: str = "default_user"):
        return []

    def get_holding(self, user_id: str, holding_id: int):
        return {
            "id": holding_id,
            "user_id": user_id,
            "ticker": "SZSE:300308",
            "exchange": "SZSE",
            "asset_name": "中际旭创",
            "quantity": 100,
            "cost_price": 100.0,
            "position_weight": 20.0,
            "buy_date": None,
            "thesis_note": None,
            "notes": None,
            "latest_diagnosis": None,
            "market_snapshot": {
                "current_price": 123.4,
                "latest_change_percent": 1.2,
                "profit_percent": 12.3,
            },
            "created_at": "2025-04-10T10:00:00Z",
            "updated_at": "2025-04-10T10:00:00Z",
        }


class FakeHoldingDiagnosisService:
    def refresh_latest_diagnosis(self, user_id: str, holding_id: int):
        return {
            "id": 1,
            "holding_id": holding_id,
            "diagnosis_date": "2025-04-10",
            "action": "持有",
            "risk_level": "中",
            "confidence": "中",
            "summary": "已有仓位，先看承接。",
            "key_risk": None,
            "reasons": ["趋势仍需确认。"],
            "trigger_conditions": [],
            "invalid_conditions": [],
            "is_focus": False,
            "raw_context": {},
            "created_at": "2025-04-10T10:00:00Z",
        }

    def get_latest_diagnosis(self, user_id: str, holding_id: int):
        return self.refresh_latest_diagnosis(user_id, holding_id)


class FakeDailyBriefingService:
    def get_latest_briefing(self, user_id: str = "default_user"):
        return None

    def refresh_daily_briefing(self, user_id: str = "default_user"):
        return {
            "id": 1,
            "user_id": user_id,
            "briefing_date": "2025-04-10",
            "content_markdown": "briefing",
            "summary": {
                "headline": "headline",
                "focus_items": [],
                "holding_actions": [],
                "watchlist_highlights": [],
            },
            "created_at": "2025-04-10T10:00:00Z",
            "updated_at": "2025-04-10T10:00:00Z",
        }


class FakeHoldingExitSignalService:
    def list_exit_signals(self, user_id: str = "default_user"):
        item = self._item()
        return {
            "generated_at": "2025-04-10T10:40:00Z",
            "items": [item],
            "count": 1,
        }

    def get_exit_signal(self, *, user_id: str, holding_id: int, force_refresh: bool = False):
        return self._item(holding_id=holding_id)

    @staticmethod
    def _item(holding_id: int = 1):
        return {
            "generated_at": "2025-04-10T10:40:00Z",
            "holding_id": holding_id,
            "ticker": "SZSE:300308",
            "asset_name": "中际旭创",
            "available": True,
            "action": "保护利润",
            "confidence": 68,
            "summary": "当前更适合以保护利润为主。",
            "thesis": "已有浮盈，优先防守利润回撤。",
            "evidence": ["当前已有仓位。"],
            "disagreement": ["题材仍强，但节奏偏拥挤。"],
            "invalid_conditions": ["若承接继续转弱，当前判断失效。"],
            "risk_controls": ["不构成交易指令。", "先确认流动性。"],
            "profit_protection_view": "优先考虑保护利润回撤。",
            "time_horizon": "1-4周",
            "context_snapshot": {},
            "empty_message": None,
        }


def test_portfolio_router_supports_exit_signal_endpoints(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.portfolio.get_holding_service",
        lambda: FakeHoldingService(),
    )
    monkeypatch.setattr(
        "valuecell.server.api.routers.portfolio.get_holding_diagnosis_service",
        lambda: FakeHoldingDiagnosisService(),
    )
    monkeypatch.setattr(
        "valuecell.server.api.routers.portfolio.get_daily_briefing_service",
        lambda: FakeDailyBriefingService(),
    )
    monkeypatch.setattr(
        "valuecell.server.api.routers.portfolio.get_holding_exit_signal_service",
        lambda: FakeHoldingExitSignalService(),
    )
    app = FastAPI()
    app.include_router(create_portfolio_router(), prefix="/api/v1")
    client = TestClient(app)

    list_response = client.get("/api/v1/portfolio/exit-signals")
    detail_response = client.get("/api/v1/portfolio/holdings/1/exit-signal")
    refresh_response = client.post("/api/v1/portfolio/holdings/1/exit-signal/refresh")

    assert list_response.status_code == 200
    assert list_response.json()["data"]["count"] == 1
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["action"] == "保护利润"
    assert refresh_response.status_code == 200
    assert refresh_response.json()["data"]["holding_id"] == 1
