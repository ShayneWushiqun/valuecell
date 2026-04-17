from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.risk_sizing import create_risk_sizing_router


class FakeRiskSizingService:
    def get_summary(self, *, user_id: str):
        return {
            "generated_at": "2025-04-20T10:00:00Z",
            "available": True,
            "empty_message": None,
            "market_risk_level": "中性",
            "suggested_total_exposure_range": "30% - 50%",
            "suggested_new_position_range": "4% - 7%",
            "suggested_add_position_range": "2% - 4%",
            "holding_risk_note": "先处理风险持仓。",
            "entry_risk_note": "先轻仓试错。",
            "portfolio_balance_note": "先控制题材集中度。",
            "action_queue_note": "先看风险，再看机会。",
            "ticker_suggestions": [],
        }

    def get_ticker_summary(self, *, user_id: str, ticker: str):
        return {
            "ticker": ticker,
            "display_name": "中际旭创",
            "available": True,
            "risk_level": "中",
            "suggested_position_range": "4% - 7%",
            "suggested_first_entry_range": "1% - 3%",
            "suggested_add_range": "1% - 2%",
            "stop_loss_style": "先小后大。",
            "profit_protection_style": "先保护利润。",
            "liquidity_warning": None,
            "summary": "更适合轻仓试错。",
            "reasons": ["当前需要继续确认。"],
            "empty_message": None,
        }


def test_risk_sizing_router_returns_summary_and_ticker(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.risk_sizing.get_risk_sizing_service",
        lambda: FakeRiskSizingService(),
    )
    app = FastAPI()
    app.include_router(create_risk_sizing_router(), prefix="/api/v1")
    client = TestClient(app)

    summary_response = client.get("/api/v1/risk-sizing/summary")
    ticker_response = client.get("/api/v1/risk-sizing/ticker?ticker=SZSE:300308")

    assert summary_response.status_code == 200
    assert summary_response.json()["data"]["market_risk_level"] == "中性"
    assert ticker_response.status_code == 200
    assert ticker_response.json()["data"]["ticker"] == "SZSE:300308"
