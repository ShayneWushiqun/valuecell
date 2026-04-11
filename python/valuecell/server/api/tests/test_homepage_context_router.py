from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.homepage_context import create_homepage_context_router


class FakeHomepageContextService:
    def get_homepage_context(self, user_id: str):
        return {
            "generated_at": "2025-04-10T09:30:00",
            "market_overview": {
                "available": True,
                "market_state": "修复",
                "summary": "市场开始修复。",
                "confidence": "中",
                "action_hint": "优先看修复后继续走强的方向。",
                "signals": [{"label": "涨停家数", "value": 42}],
                "score": 61,
                "empty_message": None,
            },
            "emotion_cycle": {
                "available": True,
                "cycle_stage": "修复试错",
                "summary": "情绪处于修复试错。",
                "action_hint": "低位试错优先。",
                "trend_direction": "上行",
                "stage_points": [
                    {
                        "trading_date": "20250410",
                        "cycle_stage": "修复试错",
                        "stage_score": 48,
                    }
                ],
                "turning_points": [],
                "empty_message": None,
            },
            "theme_focus": {
                "available": True,
                "items": [
                    {
                        "trading_date": "20250410",
                        "theme_name": "AI算力",
                        "theme_code": "885001.TI",
                        "theme_state": "加强",
                        "summary": "AI算力走强。",
                        "representative_tickers_json": ["SZSE:300308"],
                        "rank": 1,
                        "expectation_gap_level": "高",
                        "core_leaders_json": ["SZSE:300308"],
                        "core_institutions_json": [],
                        "metrics": {
                            "score": 82,
                            "change_value": 3.2,
                            "ths_flow_value": 10.0,
                            "dc_flow_value": 9.0,
                            "kpl_count": 3,
                            "hot_count": 2,
                        },
                    }
                ],
                "empty_message": None,
            },
            "action_framework": {
                "available": True,
                "title": "今日操作框架",
                "summary": "先看强势题材，再处理重点持仓。",
                "focus_points": ["优先跟踪 AI算力。"],
                "avoid_points": ["不要无差别追高。"],
                "empty_message": None,
            },
            "watchlist_observation": {
                "available": True,
                "items": [
                    {
                        "ticker": "SZSE:300308",
                        "display_name": "中际旭创",
                        "watchlist_name": "My Watchlist",
                        "price": "23.51",
                        "change_percent": 2.8,
                        "status": "重点观察",
                        "reason": "与主线共振。",
                        "theme_name": "AI算力",
                    }
                ],
                "empty_message": None,
            },
            "portfolio_handling": {
                "available": True,
                "summary": "优先处理重点持仓。",
                "holding_count": 1,
                "focus_count": 1,
                "action_breakdown": [{"label": "减仓", "value": "1"}],
                "empty_message": None,
            },
            "risk_control": {
                "available": True,
                "summary": "先管仓位，再谈进攻。",
                "position_suggestion": "建议 30% - 50% 仓位参与。",
                "signals": ["弱势环境先控仓。"],
                "empty_message": None,
            },
        }


def test_homepage_context_router_returns_structured_response(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.homepage_context.get_homepage_context_service",
        lambda: FakeHomepageContextService(),
    )
    app = FastAPI()
    app.include_router(create_homepage_context_router(), prefix="/api/v1")
    client = TestClient(app)

    response = client.get("/api/v1/homepage/context")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"]["market_overview"]["market_state"] == "修复"
    assert payload["data"]["watchlist_observation"]["items"][0]["status"] == "重点观察"
