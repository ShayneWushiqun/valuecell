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
                "breadth_items": [{"label": "涨停家数", "value": 42}],
                "index_quotes": [
                    {
                        "label": "上证",
                        "ticker": "SSE:000001",
                        "price": "3200.00",
                        "change_percent": 0.82,
                    }
                ],
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
                        "up_limit_count": 42,
                        "down_limit_count": 5,
                        "broken_limit_count": 3,
                        "highest_board": 4,
                        "action_hint": "低位试错优先。",
                    }
                ],
                "turning_points": [],
                "default_window_days": 20,
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
                        "primary_representative": "SZSE:300308",
                        "trend_state": "加强",
                        "hot_level": 2,
                        "is_suitable_for_direct_participation": False,
                        "participation_hint": "方向有热度，但不建议无差别追高。",
                        "preferred_market": "创业板为主",
                        "core_institutions_json": [],
                        "etf_hint": {
                            "title": "可考虑相关场内 ETF 作为替代观察",
                            "summary": "可考虑相关场内 ETF 作为替代观察，暂无匹配具体 ETF。",
                            "risk_hint": "注意流动性、跟踪误差和板块退潮风险。",
                        },
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
                "participation_preferences": ["默认优先主板 10cm 个股。"],
                "etf_strategy_hint": "可考虑相关场内 ETF 作为替代观察，暂无匹配具体 ETF。 注意流动性、跟踪误差和板块退潮风险。",
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
                        "tradeability_state": "可观察",
                        "expectation_gap_level": "中",
                        "role_label": "龙头",
                        "trend_quality": "顺势",
                    }
                ],
                "all_items": [
                    {
                        "ticker": "SZSE:300308",
                        "display_name": "中际旭创",
                        "watchlist_name": "My Watchlist",
                        "price": "23.51",
                        "change_percent": 2.8,
                        "status": "重点观察",
                        "reason": "与主线共振。",
                        "theme_name": "AI算力",
                        "tradeability_state": "可观察",
                        "expectation_gap_level": "中",
                        "role_label": "龙头",
                        "trend_quality": "顺势",
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
                "total_position_range": "3-5成",
                "single_position_range": "单票以 10% - 20% 为主。",
                "build_strategy": "分批建仓",
                "theme_concentration_hint": "优先集中在 1 到 2 个主线方向。",
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
    assert payload["data"]["watchlist_observation"]["all_items"][0]["ticker"] == "SZSE:300308"
