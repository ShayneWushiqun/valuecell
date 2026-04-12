from __future__ import annotations

from typing import Any, cast

from valuecell.server.services.assets.opportunity_pool_service import OpportunityPoolService


class FakeThemeCandidateService:
    def get_theme_candidates(self, top_n: int = 12) -> dict[str, Any]:
        return {
            "success": True,
            "data": {
                "items": [
                    {
                        "theme_name": "AI算力",
                        "theme_state": "加强",
                        "trend_state": "加强",
                        "hot_level": 5,
                        "preferred_market": "创业板为主",
                        "is_suitable_for_direct_participation": False,
                        "participation_hint": "方向有热度，但不建议无差别追高，优先低吸或等待更好位置。",
                        "etf_hint": {
                            "title": "可考虑相关场内 ETF 作为替代观察",
                            "summary": "可考虑相关场内 ETF 作为替代观察，暂无匹配具体 ETF。",
                            "risk_hint": "ETF 仍需关注流动性、跟踪误差和板块快速退潮带来的回撤风险。",
                        },
                        "representative_tickers": ["SZSE:300308"],
                        "representative_tickers_json": ["SZSE:300308"],
                        "core_leaders_json": ["SZSE:300308"],
                        "primary_representative": "SZSE:300308",
                        "expectation_gap_level": "高",
                        "rank": 1,
                        "metrics": {"change_value": 2.6},
                    },
                    {
                        "theme_name": "证券",
                        "theme_state": "活跃",
                        "trend_state": "加强",
                        "hot_level": 4,
                        "preferred_market": "主板为主",
                        "is_suitable_for_direct_participation": True,
                        "participation_hint": "可优先围绕主板核心票观察承接，再决定是否参与。",
                        "etf_hint": None,
                        "representative_tickers": ["SSE:600030"],
                        "representative_tickers_json": ["SSE:600030"],
                        "core_leaders_json": ["SSE:600030"],
                        "primary_representative": "SSE:600030",
                        "expectation_gap_level": "中",
                        "rank": 2,
                        "metrics": {"change_value": 1.4},
                    },
                    {
                        "theme_name": "ST板块",
                        "theme_state": "加强",
                        "trend_state": "加强",
                        "hot_level": 5,
                        "preferred_market": "主板为主",
                        "is_suitable_for_direct_participation": False,
                        "participation_hint": "疑似 ST 或高风险方向，默认回避，不建议参与。",
                        "etf_hint": None,
                        "representative_tickers": ["SZSE:000007"],
                        "representative_tickers_json": ["SZSE:000007"],
                        "core_leaders_json": ["SZSE:000007"],
                        "primary_representative": "SZSE:000007",
                        "expectation_gap_level": "低",
                        "rank": 3,
                        "metrics": {"change_value": 6.2},
                    },
                ]
            },
        }


class FakeWatchlistObservationService:
    def get_watchlist_observation(
        self,
        user_id: str,
        theme_items: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return {
            "available": True,
            "items": [],
            "all_items": [
                {
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "watchlist_name": "My Watchlist",
                    "price": "23.51",
                    "change_percent": 2.8,
                    "status": "重点观察",
                    "reason": "与 AI算力 主线共振，日内表现走强。",
                    "theme_name": "AI算力",
                    "tradeability_state": "可观察",
                    "expectation_gap_level": "中",
                    "role_label": "龙头",
                    "trend_quality": "顺势",
                },
                {
                    "ticker": "SZSE:000001",
                    "display_name": "平安银行",
                    "watchlist_name": "My Watchlist",
                    "price": "11.02",
                    "change_percent": -0.8,
                    "status": "常规跟踪",
                    "reason": "当前没有形成更强主线共振，先保持常规跟踪。",
                    "theme_name": "证券",
                    "tradeability_state": "可低吸",
                    "expectation_gap_level": "高",
                    "role_label": "跟风",
                    "trend_quality": "震荡",
                },
            ],
            "empty_message": None,
        }


class FakeAssetService:
    def get_asset_price(self, ticker: str, language: str | None = None) -> dict[str, Any]:
        mapping = {
            "SSE:600030": {"success": True, "price_formatted": "17.20", "change_percent": 1.5},
            "SZSE:000007": {"success": True, "price_formatted": "3.21", "change_percent": 9.8},
        }
        return mapping.get(
            ticker,
            {"success": True, "price_formatted": "10.00", "change_percent": 0.0},
        )

    def get_asset_info(self, ticker: str, language: str | None = None) -> dict[str, Any]:
        mapping = {
            "SSE:600030": {"success": True, "display_name": "中信证券"},
            "SZSE:000007": {"success": True, "display_name": "ST全新"},
        }
        return mapping.get(ticker, {"success": False, "ticker": ticker})


def test_opportunity_pool_service_prioritizes_watchlist_theme_resonance() -> None:
    service = OpportunityPoolService(
        theme_candidate_service=cast(Any, FakeThemeCandidateService()),
        watchlist_observation_service=cast(Any, FakeWatchlistObservationService()),
        asset_service=cast(Any, FakeAssetService()),
    )

    result = service.get_opportunity_candidates("default_user")

    assert result["available"] is True
    assert result["count"] == 4
    assert result["items"][0]["ticker"] == "SZSE:300308"
    assert "theme_resonance" in result["items"][0]["source_tags"]
    assert result["items"][0]["candidate_state"] in {"候选买点", "高优先级买点"}
    assert result["items"][0]["latest_price"] == "23.51"
    assert result["items"][0]["change_percent"] == 2.8
    assert result["items"][0]["reasons"]
    assert result["items"][0]["missing_confirmations"]


def test_opportunity_pool_service_keeps_st_out_of_top_recommendations() -> None:
    service = OpportunityPoolService(
        theme_candidate_service=cast(Any, FakeThemeCandidateService()),
        watchlist_observation_service=cast(Any, FakeWatchlistObservationService()),
        asset_service=cast(Any, FakeAssetService()),
    )

    result = service.get_opportunity_candidates("default_user")

    st_item = next(item for item in result["items"] if item["ticker"] == "SZSE:000007")
    assert st_item["candidate_state"] == "暂不参与"
    assert st_item["priority_score"] < result["items"][0]["priority_score"]
    assert any("回避" in text for text in st_item["invalid_conditions"])


def test_opportunity_pool_service_marks_tradeability_risk_conservatively() -> None:
    service = OpportunityPoolService(
        theme_candidate_service=cast(Any, FakeThemeCandidateService()),
        watchlist_observation_service=cast(Any, FakeWatchlistObservationService()),
        asset_service=cast(Any, FakeAssetService()),
    )

    result = service.get_opportunity_candidates("default_user")

    st_item = next(item for item in result["items"] if item["ticker"] == "SZSE:000007")
    ai_item = next(item for item in result["items"] if item["ticker"] == "SZSE:300308")
    security_watchlist_item = next(
        item for item in result["items"] if item["ticker"] == "SZSE:000001"
    )
    assert "不宜追高" in " ".join(st_item["invalid_conditions"])
    assert st_item["tradeability_state"] == "谨慎追高"
    assert st_item["candidate_state"] == "暂不参与"
    assert st_item["latest_price"] == "3.21"
    assert st_item["change_percent"] == 9.8
    assert security_watchlist_item["source_tags"] == ["watchlist", "theme_resonance"]
    assert ai_item["action_hint"]
    assert result["source_summary"]["watchlist_count"] == 2
