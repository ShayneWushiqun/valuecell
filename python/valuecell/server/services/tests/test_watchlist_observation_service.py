from __future__ import annotations

from typing import Any, cast

from valuecell.server.services.assets.watchlist_observation_service import (
    WatchlistObservationService,
)


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

    def get_asset_price(self, ticker: str, language: str | None = None) -> dict[str, Any]:
        price, change_percent = self.price_by_ticker.get(ticker, ("10.00", 0.0))
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
    def get_user_watchlists(self, user_id: str) -> list[FakeWatchlist]:
        return [FakeWatchlist()]


def test_watchlist_observation_service_returns_items_and_all_items() -> None:
    service = WatchlistObservationService(
        asset_service=cast(Any, FakeAssetService()),
        watchlist_repository=cast(Any, FakeWatchlistRepository()),
    )

    result = service.get_watchlist_observation(
        "default_user",
        [
            {
                "theme_name": "AI算力",
                "core_leaders_json": ["SZSE:300308"],
                "representative_tickers_json": ["SZSE:300308"],
            }
        ],
    )

    assert result["available"] is True
    assert len(result["items"]) == 5
    assert len(result["all_items"]) == 6
    assert result["items"][0]["ticker"] == "SZSE:300308"
    assert result["items"][0]["status"] == "重点观察"
    assert result["all_items"][1]["status"] == "风险观察"


def test_watchlist_observation_service_returns_empty_state_when_no_watchlist() -> None:
    class EmptyWatchlistRepository:
        def get_user_watchlists(self, user_id: str) -> list[Any]:
            return []

    service = WatchlistObservationService(
        asset_service=cast(Any, FakeAssetService()),
        watchlist_repository=cast(Any, EmptyWatchlistRepository()),
    )

    result = service.get_watchlist_observation("default_user", [])

    assert result["available"] is False
    assert result["items"] == []
    assert result["all_items"] == []
