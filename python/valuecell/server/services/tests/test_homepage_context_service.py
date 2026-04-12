from __future__ import annotations

from datetime import datetime
from typing import Any, cast

from valuecell.server.services.assets.homepage_context_service import (
    HomepageContextService,
)


class FakeMarketPulseService:
    def __init__(self) -> None:
        self.calls: list[str | None] = []

    def get_market_pulse_snapshot(self, trade_date: str | None = None):
        self.calls.append(trade_date)
        return {
            "success": True,
            "data": {
                "market_state": "修复",
                "summary": "市场风险偏好回升。",
                "confidence": "中",
                "action_hint": "优先关注修复后继续走强的方向。",
                "signals_json": [{"label": "涨停家数", "value": 42}],
                "score": 63,
                "metrics": {
                    "up_limit_count": 42,
                    "down_limit_count": 5,
                    "broken_limit_count": 3,
                    "strongest_board_height": 4,
                },
            },
        }


class FakeEmotionCycleService:
    def get_emotion_cycle_snapshot(self):
        return {
            "success": True,
            "data": {
                "cycle_stage": "修复试错",
                "summary": "情绪处于修复试错阶段。",
                "action_hint": "低位试错优先。",
            },
        }

    def get_emotion_cycle_timeline(self, window_days: int = 30):
        return {
            "success": True,
            "data": {
                "trend_direction": "上行",
                "stage_points_json": [
                    {
                        "trading_date": "20250408",
                        "cycle_stage": "冰点",
                        "stage_score": 20,
                        "up_limit_count": 18,
                        "down_limit_count": 12,
                        "broken_limit_count": 6,
                        "highest_board": 1,
                        "action_hint": "以观察和等待为主。",
                    },
                    {
                        "trading_date": "20250409",
                        "cycle_stage": "修复试错",
                        "stage_score": 48,
                        "up_limit_count": 42,
                        "down_limit_count": 5,
                        "broken_limit_count": 3,
                        "highest_board": 4,
                        "action_hint": "低位试错优先。",
                    },
                ],
                "turning_points_json": [
                    {
                        "trading_date": "20250409",
                        "from_stage": "冰点",
                        "to_stage": "修复试错",
                    }
                ],
            },
        }


class FakeThemeFocusService:
    def get_theme_focus_snapshot(self, top_n: int = 3):
        return {
            "success": True,
            "data": {
                "items": [
                    {
                        "trading_date": "20250410",
                        "theme_name": "AI算力",
                        "theme_code": "885001.TI",
                        "theme_state": "加强",
                        "summary": "AI算力继续加强。",
                        "representative_tickers_json": ["SZSE:300308"],
                        "rank": 1,
                        "expectation_gap_level": "高",
                        "core_leaders_json": ["SZSE:300308", "SSE:603019"],
                        "core_institutions_json": [],
                        "metrics": {
                            "score": 82,
                            "change_value": 3.2,
                            "ths_flow_value": 10.0,
                            "dc_flow_value": 9.0,
                            "kpl_count": 3,
                            "hot_count": 2,
                        },
                    },
                    {
                        "trading_date": "20250410",
                        "theme_name": "ST板块",
                        "theme_code": "885999.TI",
                        "theme_state": "加强",
                        "summary": "ST方向异动。",
                        "representative_tickers_json": ["ST龙头"],
                        "rank": 0,
                        "expectation_gap_level": "低",
                        "core_leaders_json": ["ST龙头"],
                        "core_institutions_json": [],
                        "metrics": {
                            "score": 90,
                            "change_value": 4.5,
                            "ths_flow_value": 6.0,
                            "dc_flow_value": 5.0,
                            "kpl_count": 2,
                            "hot_count": 5,
                        },
                    }
                ]
            },
        }


class FakeHoldingService:
    def list_holdings(self, user_id: str):
        return [
            {
                "ticker": "SZSE:300308",
                "asset_name": "中际旭创",
                "latest_diagnosis": {
                    "action": "减仓",
                    "is_focus": True,
                },
            }
        ]


class FakeDailyBriefingService:
    def get_latest_briefing(self, user_id: str):
        return {
            "summary": {
                "headline": "今日优先处理中际旭创，控制追高节奏。",
            }
        }

    def refresh_daily_briefing(self, user_id: str):
        return self.get_latest_briefing(user_id)


class FakeAssetService:
    def __init__(self) -> None:
        self.price_by_ticker = {
            "SZSE:300308": ("23.51", 2.8),
            "SZSE:000001": ("11.02", -3.6),
            "SZSE:000002": ("8.31", 1.3),
            "SZSE:000004": ("15.22", 6.2),
            "SZSE:000005": ("7.18", -0.4),
            "SZSE:000006": ("9.80", 0.2),
        }

    def get_asset_price(self, ticker: str, language: str | None = None):
        price, change_percent = self.price_by_ticker.get(ticker, ("23.51", 2.8))
        return {
            "success": True,
            "price_formatted": price,
            "change_percent": change_percent,
        }


class FakeWatchlistItem:
    def __init__(self, ticker: str, display_name: str, symbol: str) -> None:
        self.ticker = ticker
        self.display_name = display_name
        self.symbol = symbol


class FakeWatchlist:
    name = "My Watchlist"
    items = [
        FakeWatchlistItem("SZSE:300308", "中际旭创", "300308"),
        FakeWatchlistItem("SZSE:000001", "平安银行", "000001"),
        FakeWatchlistItem("SZSE:000002", "万科A", "000002"),
        FakeWatchlistItem("SZSE:000004", "国华网安", "000004"),
        FakeWatchlistItem("SZSE:000005", "世纪星源", "000005"),
        FakeWatchlistItem("SZSE:000006", "深振业A", "000006"),
    ]


class FakeWatchlistRepository:
    def get_user_watchlists(self, user_id: str):
        return [FakeWatchlist()]


class EmptyThemeFocusService:
    def get_theme_focus_snapshot(self, top_n: int = 3):
        return {"success": False}


class EmptyEmotionCycleService:
    def get_emotion_cycle_snapshot(self):
        return {"success": False}

    def get_emotion_cycle_timeline(self, window_days: int = 5):
        return {"success": False}


class EmptyMarketPulseService:
    def get_market_pulse_snapshot(self, trade_date: str | None = None):
        return {"success": False}


class EmptyHoldingService:
    def list_holdings(self, user_id: str):
        return []


class EmptyBriefingService:
    def get_latest_briefing(self, user_id: str):
        return None

    def refresh_daily_briefing(self, user_id: str):
        return None


class EmptyAssetService:
    def get_asset_price(self, ticker: str, language: str | None = None):
        return {"success": False}


class EmptyWatchlistRepository:
    def get_user_watchlists(self, user_id: str):
        return []


def test_homepage_context_service_aggregates_sections() -> None:
    market_pulse_service = FakeMarketPulseService()
    service = HomepageContextService(
        market_pulse_service=cast(Any, market_pulse_service),
        emotion_cycle_service=cast(Any, FakeEmotionCycleService()),
        theme_focus_service=cast(Any, FakeThemeFocusService()),
        holding_service=cast(Any, FakeHoldingService()),
        daily_briefing_service=cast(Any, FakeDailyBriefingService()),
        asset_service=cast(Any, FakeAssetService()),
        watchlist_repository=cast(Any, FakeWatchlistRepository()),
    )

    result = service.get_homepage_context("default_user")

    datetime.fromisoformat(result["generated_at"])
    assert result["market_overview"]["available"] is True
    assert len(result["market_overview"]["index_quotes"]) == 5
    assert result["emotion_cycle"]["cycle_stage"] == "修复试错"
    assert result["emotion_cycle"]["default_window_days"] == 20
    assert result["emotion_cycle"]["stage_points"][0]["up_limit_count"] == 18
    assert result["emotion_cycle"]["stage_points"][0]["action_hint"] == "以观察和等待为主。"
    assert result["theme_focus"]["items"][0]["theme_name"] == "AI算力"
    assert result["theme_focus"]["items"][-1]["theme_name"] == "ST板块"
    assert result["theme_focus"]["items"][-1]["participation_hint"] == "疑似 ST 或高风险方向，默认回避，不建议参与。"
    assert result["theme_focus"]["items"][0]["is_suitable_for_direct_participation"] is False
    assert result["theme_focus"]["items"][0]["etf_hint"]["summary"].endswith("暂无匹配具体 ETF。")
    assert result["watchlist_observation"]["items"][0]["status"] == "重点观察"
    assert len(result["watchlist_observation"]["items"]) == 5
    assert len(result["watchlist_observation"]["all_items"]) == 6
    assert result["watchlist_observation"]["items"][0]["tradeability_state"] == "可观察"
    assert result["portfolio_handling"]["focus_count"] == 1
    assert result["action_framework"]["available"] is True
    assert result["action_framework"]["participation_preferences"]
    assert result["action_framework"]["etf_strategy_hint"]
    assert result["risk_control"]["available"] is True
    assert result["risk_control"]["total_position_range"] == "3-5成"
    assert market_pulse_service.calls == [None]


def test_homepage_context_service_handles_empty_degraded_sections() -> None:
    service = HomepageContextService(
        market_pulse_service=cast(Any, EmptyMarketPulseService()),
        emotion_cycle_service=cast(Any, EmptyEmotionCycleService()),
        theme_focus_service=cast(Any, EmptyThemeFocusService()),
        holding_service=cast(Any, EmptyHoldingService()),
        daily_briefing_service=cast(Any, EmptyBriefingService()),
        asset_service=cast(Any, EmptyAssetService()),
        watchlist_repository=cast(Any, EmptyWatchlistRepository()),
    )

    result = service.get_homepage_context("default_user")

    assert result["market_overview"]["available"] is False
    assert result["emotion_cycle"]["available"] is False
    assert result["theme_focus"]["available"] is False
    assert result["watchlist_observation"]["available"] is False
    assert result["watchlist_observation"]["all_items"] == []
    assert result["portfolio_handling"]["available"] is False
    assert result["action_framework"]["available"] is False
    assert result["risk_control"]["available"] is True
