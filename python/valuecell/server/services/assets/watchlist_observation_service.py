from __future__ import annotations

from typing import Any, Optional

from ...db.repositories.watchlist_repository import WatchlistRepository
from .asset_service import AssetService


class WatchlistObservationService:
    def __init__(
        self,
        asset_service: Optional[AssetService] = None,
        watchlist_repository: Optional[WatchlistRepository] = None,
    ) -> None:
        self.asset_service = asset_service or AssetService()
        self.watchlist_repository = watchlist_repository or WatchlistRepository()

    def get_watchlist_observation(
        self,
        user_id: str,
        theme_items: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        watchlists = self.watchlist_repository.get_user_watchlists(user_id)
        theme_by_ticker = self._build_theme_by_ticker(theme_items or [])
        items: list[dict[str, Any]] = []

        for watchlist in watchlists:
            for watchlist_item in watchlist.items:
                price_result = self.asset_service.get_asset_price(
                    watchlist_item.ticker,
                    language="zh-CN",
                )
                price_value = (
                    price_result.get("price_formatted")
                    if price_result.get("success")
                    else None
                )
                change_percent = (
                    price_result.get("change_percent")
                    if price_result.get("success")
                    else None
                )
                theme_name = theme_by_ticker.get(watchlist_item.ticker)
                status, reason = self._resolve_watchlist_status(
                    ticker=watchlist_item.ticker,
                    change_percent=change_percent,
                    theme_name=theme_name,
                )
                items.append(
                    {
                        "ticker": watchlist_item.ticker,
                        "display_name": watchlist_item.display_name or watchlist_item.symbol,
                        "watchlist_name": watchlist.name,
                        "price": price_value,
                        "change_percent": change_percent,
                        "status": status,
                        "reason": reason,
                        "theme_name": theme_name,
                        "tradeability_state": self._resolve_tradeability_state(
                            change_percent=change_percent
                        ),
                        "expectation_gap_level": self._resolve_expectation_gap(
                            change_percent=change_percent,
                            theme_name=theme_name,
                        ),
                        "role_label": self._resolve_role_label(
                            ticker=watchlist_item.ticker,
                            theme_name=theme_name,
                        ),
                        "trend_quality": self._resolve_trend_quality(
                            change_percent=change_percent
                        ),
                    }
                )

        items.sort(
            key=lambda item: (
                self._watchlist_status_rank(str(item.get("status") or "")),
                abs(float(item.get("change_percent") or 0)),
            )
        )
        if not items:
            return {
                "available": False,
                "items": [],
                "all_items": [],
                "empty_message": "暂无自选观察数据",
            }
        return {
            "available": True,
            "items": items[:5],
            "all_items": items,
            "empty_message": None,
        }

    @staticmethod
    def _build_theme_by_ticker(items: list[dict[str, Any]]) -> dict[str, str]:
        theme_by_ticker: dict[str, str] = {}
        for item in items:
            theme_name = str(item.get("theme_name") or "")
            tickers = [
                *list(item.get("core_leaders_json") or []),
                *list(item.get("representative_tickers_json") or []),
                *list(item.get("representative_tickers") or []),
            ]
            primary_representative = str(item.get("primary_representative") or "").strip()
            if primary_representative:
                tickers.append(primary_representative)
            for ticker in tickers:
                text = str(ticker or "").strip()
                if text and text not in theme_by_ticker:
                    theme_by_ticker[text] = theme_name
        return theme_by_ticker

    @staticmethod
    def _resolve_watchlist_status(
        *,
        ticker: str,
        change_percent: float | None,
        theme_name: str | None,
    ) -> tuple[str, str]:
        if theme_name and change_percent is not None and change_percent >= 1.5:
            return "重点观察", f"与 {theme_name} 主线共振，日内表现走强。"
        if change_percent is not None and change_percent <= -3:
            return "风险观察", "日内回撤较大，先观察承接和修复节奏。"
        if theme_name:
            return "主题联动", f"属于 {theme_name} 方向，建议持续跟踪。"
        if change_percent is not None and abs(change_percent) >= 2:
            return "波动观察", "短线波动放大，适合加入盘中重点观察。"
        return "常规跟踪", f"{ticker} 当前没有形成更强主线共振，先保持常规跟踪。"

    @staticmethod
    def _watchlist_status_rank(status: str) -> int:
        rank_map = {
            "重点观察": 0,
            "风险观察": 1,
            "主题联动": 2,
            "波动观察": 3,
            "常规跟踪": 4,
        }
        return rank_map.get(status, 9)

    @staticmethod
    def _resolve_tradeability_state(change_percent: float | None) -> str:
        if change_percent is None:
            return "可观察"
        if change_percent >= 6:
            return "谨慎追高"
        if change_percent <= -7:
            return "流动性风险"
        if -2 <= change_percent <= 2:
            return "可低吸"
        return "可观察"

    @staticmethod
    def _resolve_expectation_gap(
        *,
        change_percent: float | None,
        theme_name: str | None,
    ) -> str:
        if theme_name and change_percent is not None and change_percent >= 2:
            return "中"
        if change_percent is not None and abs(change_percent) >= 4:
            return "低"
        return "高"

    @staticmethod
    def _resolve_role_label(*, ticker: str, theme_name: str | None) -> str:
        if theme_name and (ticker.startswith("SSE:60") or ticker.startswith("SZSE:00")):
            return "中军"
        if theme_name:
            return "龙头"
        return "跟风"

    @staticmethod
    def _resolve_trend_quality(*, change_percent: float | None) -> str:
        if change_percent is None:
            return "震荡"
        if change_percent >= 2:
            return "顺势"
        if change_percent <= -3:
            return "走弱"
        return "震荡"


_watchlist_observation_service: Optional[WatchlistObservationService] = None


def get_watchlist_observation_service() -> WatchlistObservationService:
    global _watchlist_observation_service
    if _watchlist_observation_service is None:
        _watchlist_observation_service = WatchlistObservationService()
    return _watchlist_observation_service


def reset_watchlist_observation_service() -> None:
    global _watchlist_observation_service
    _watchlist_observation_service = None
