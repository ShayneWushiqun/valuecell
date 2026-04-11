from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional

from loguru import logger

from ...db.repositories.watchlist_repository import WatchlistRepository
from ..portfolio import DailyBriefingService, HoldingService
from .asset_service import AssetService
from .emotion_cycle_service import EmotionCycleService
from .market_pulse_service import MarketPulseService
from .theme_focus_service import ThemeFocusService


class HomepageContextService:
    def __init__(
        self,
        market_pulse_service: Optional[MarketPulseService] = None,
        emotion_cycle_service: Optional[EmotionCycleService] = None,
        theme_focus_service: Optional[ThemeFocusService] = None,
        holding_service: Optional[HoldingService] = None,
        daily_briefing_service: Optional[DailyBriefingService] = None,
        asset_service: Optional[AssetService] = None,
        watchlist_repository: Optional[WatchlistRepository] = None,
    ) -> None:
        self.market_pulse_service = market_pulse_service or MarketPulseService()
        self.emotion_cycle_service = emotion_cycle_service or EmotionCycleService()
        self.theme_focus_service = theme_focus_service or ThemeFocusService()
        self.holding_service = holding_service or HoldingService()
        self.daily_briefing_service = daily_briefing_service or DailyBriefingService()
        self.asset_service = asset_service or AssetService()
        self.watchlist_repository = watchlist_repository or WatchlistRepository()

    def get_homepage_context(self, user_id: str) -> dict[str, Any]:
        market = self._build_market_overview()
        emotion = self._build_emotion_cycle()
        theme = self._build_theme_focus()
        holdings = self.holding_service.list_holdings(user_id)
        briefing = self._get_briefing(user_id)
        watchlist = self._build_watchlist_observation(user_id, theme)
        portfolio = self._build_portfolio_handling(holdings, briefing)
        action_framework = self._build_action_framework(
            market_overview=market,
            emotion_cycle=emotion,
            theme_focus=theme,
            watchlist_observation=watchlist,
            portfolio_handling=portfolio,
        )
        risk_control = self._build_risk_control(
            market_overview=market,
            emotion_cycle=emotion,
            watchlist_observation=watchlist,
            portfolio_handling=portfolio,
        )

        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "market_overview": market,
            "emotion_cycle": emotion,
            "theme_focus": theme,
            "action_framework": action_framework,
            "watchlist_observation": watchlist,
            "portfolio_handling": portfolio,
            "risk_control": risk_control,
        }

    def _build_market_overview(self) -> dict[str, Any]:
        try:
            result = self.market_pulse_service.get_market_pulse_snapshot()
        except Exception as exc:
            logger.warning("Homepage market overview unavailable: {}", str(exc))
            result = {"success": False}

        if not result.get("success"):
            return {
                "available": False,
                "market_state": None,
                "summary": None,
                "confidence": None,
                "action_hint": None,
                "signals": [],
                "score": None,
                "empty_message": "暂无可用市场快照",
            }

        data = result["data"]
        return {
            "available": True,
            "market_state": data.get("market_state"),
            "summary": data.get("summary"),
            "confidence": data.get("confidence"),
            "action_hint": data.get("action_hint"),
            "signals": data.get("signals_json", []),
            "score": data.get("score"),
            "empty_message": None,
        }

    def _build_emotion_cycle(self) -> dict[str, Any]:
        try:
            snapshot = self.emotion_cycle_service.get_emotion_cycle_snapshot()
            timeline = self.emotion_cycle_service.get_emotion_cycle_timeline(window_days=5)
        except Exception as exc:
            logger.warning("Homepage emotion cycle unavailable: {}", str(exc))
            snapshot = {"success": False}
            timeline = {"success": False}

        if not snapshot.get("success"):
            return {
                "available": False,
                "cycle_stage": None,
                "summary": None,
                "action_hint": None,
                "trend_direction": None,
                "stage_points": [],
                "turning_points": [],
                "empty_message": "暂无可用情绪周期数据",
            }

        snapshot_data = snapshot["data"]
        timeline_data = timeline.get("data", {}) if timeline.get("success") else {}
        return {
            "available": True,
            "cycle_stage": snapshot_data.get("cycle_stage"),
            "summary": snapshot_data.get("summary"),
            "action_hint": snapshot_data.get("action_hint"),
            "trend_direction": timeline_data.get("trend_direction"),
            "stage_points": timeline_data.get("stage_points_json", []),
            "turning_points": timeline_data.get("turning_points_json", []),
            "empty_message": None,
        }

    def _build_theme_focus(self) -> dict[str, Any]:
        try:
            result = self.theme_focus_service.get_theme_focus_snapshot(top_n=3)
        except Exception as exc:
            logger.warning("Homepage theme focus unavailable: {}", str(exc))
            result = {"success": False}

        if not result.get("success"):
            return {
                "available": False,
                "items": [],
                "empty_message": "暂无可用题材聚焦数据",
            }

        items = result.get("data", {}).get("items", [])
        if not items:
            return {
                "available": False,
                "items": [],
                "empty_message": "暂无清晰主流题材",
            }
        return {
            "available": True,
            "items": items,
            "empty_message": None,
        }

    def _build_watchlist_observation(
        self,
        user_id: str,
        theme_focus: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            watchlists = self.watchlist_repository.get_user_watchlists(user_id)
        except Exception as exc:
            logger.warning("Homepage watchlist unavailable: {}", str(exc))
            watchlists = []

        theme_by_ticker = self._build_theme_by_ticker(theme_focus.get("items", []))
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
                    }
                )

        items.sort(
            key=lambda item: (
                self._watchlist_status_rank(item["status"]),
                abs(item["change_percent"] or 0),
            )
        )
        if not items:
            return {
                "available": False,
                "items": [],
                "empty_message": "暂无自选观察数据",
            }
        return {
            "available": True,
            "items": items[:8],
            "empty_message": None,
        }

    def _build_portfolio_handling(
        self,
        holdings: list[dict[str, Any]],
        briefing: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if not holdings:
            return {
                "available": False,
                "summary": None,
                "holding_count": 0,
                "focus_count": 0,
                "action_breakdown": [],
                "empty_message": "暂无持仓，录入后可查看短周期处理建议",
            }

        action_count = {"持有": 0, "减仓": 0, "卖出": 0, "观察": 0}
        focus_count = 0
        for holding in holdings:
            action = holding.get("latest_diagnosis", {}).get("action")
            if action in action_count:
                action_count[action] += 1
            if holding.get("latest_diagnosis", {}).get("is_focus"):
                focus_count += 1

        headline = None
        if briefing:
            headline = briefing.get("summary", {}).get("headline")
        if not headline:
            first_focus = next(
                (
                    holding
                    for holding in holdings
                    if holding.get("latest_diagnosis", {}).get("is_focus")
                ),
                holdings[0],
            )
            action = first_focus.get("latest_diagnosis", {}).get("action") or "观察"
            name = first_focus.get("asset_name") or first_focus.get("ticker")
            headline = f"当前优先处理 {name}，建议以{action}思路应对。"

        action_breakdown = [
            {"label": key, "value": str(value)} for key, value in action_count.items()
        ]
        return {
            "available": True,
            "summary": headline,
            "holding_count": len(holdings),
            "focus_count": focus_count,
            "action_breakdown": action_breakdown,
            "empty_message": None,
        }

    def _build_action_framework(
        self,
        *,
        market_overview: dict[str, Any],
        emotion_cycle: dict[str, Any],
        theme_focus: dict[str, Any],
        watchlist_observation: dict[str, Any],
        portfolio_handling: dict[str, Any],
    ) -> dict[str, Any]:
        focus_points: list[str] = []
        avoid_points: list[str] = []
        if market_overview.get("action_hint"):
            focus_points.append(str(market_overview["action_hint"]))
        if emotion_cycle.get("action_hint"):
            focus_points.append(str(emotion_cycle["action_hint"]))
        for item in theme_focus.get("items", [])[:2]:
            focus_points.append(f"优先跟踪 {item['theme_name']} 方向的核心票。")

        if portfolio_handling.get("focus_count", 0) > 0:
            avoid_points.append("已有重点持仓待处理时，避免无差别开新仓。")
        if any(
            item.get("status") == "风险观察"
            for item in watchlist_observation.get("items", [])
        ):
            avoid_points.append("对高波动自选股先确认承接，不宜情绪化追价。")
        if market_overview.get("market_state") in {"退潮", "震荡"}:
            avoid_points.append("弱势环境下优先收缩节奏，避免摊大风险暴露。")

        available = bool(focus_points or avoid_points)
        if not available:
            return {
                "available": False,
                "title": "今日操作框架",
                "summary": None,
                "focus_points": [],
                "avoid_points": [],
                "empty_message": "暂无可用操作框架",
            }

        market_state = market_overview.get("market_state") or "中性"
        cycle_stage = emotion_cycle.get("cycle_stage") or "待确认"
        summary = (
            f"当前以{market_state}市场环境、{cycle_stage}情绪阶段来组织今日节奏，"
            "优先处理强势主线与已有重点持仓。"
        )
        return {
            "available": True,
            "title": "今日操作框架",
            "summary": summary,
            "focus_points": focus_points[:4],
            "avoid_points": avoid_points[:3],
            "empty_message": None,
        }

    def _build_risk_control(
        self,
        *,
        market_overview: dict[str, Any],
        emotion_cycle: dict[str, Any],
        watchlist_observation: dict[str, Any],
        portfolio_handling: dict[str, Any],
    ) -> dict[str, Any]:
        market_state = market_overview.get("market_state")
        cycle_stage = emotion_cycle.get("cycle_stage")
        if market_state == "进攻" and cycle_stage in {"主升发酵", "高潮一致"}:
            position_suggestion = "建议以 50% - 70% 的活动仓位参与强势主线。"
        elif market_state in {"修复", "轮动"} or cycle_stage in {"修复试错", "分歧"}:
            position_suggestion = "建议以 30% - 50% 的试错仓位参与，优先聚焦少数方向。"
        else:
            position_suggestion = "建议把活动仓位控制在 20% - 30%，以防守和观察为主。"

        signals = []
        if portfolio_handling.get("focus_count", 0) > 0:
            signals.append("已有重点持仓待处理，新增仓位应低于常规节奏。")
        if any(
            item.get("status") == "风险观察"
            for item in watchlist_observation.get("items", [])
        ):
            signals.append("自选中存在风险观察标的，避免把高波动票当作主仓。")
        if market_state in {"退潮", "震荡"}:
            signals.append("弱势环境更重视仓位控制和止损执行。")

        return {
            "available": True,
            "summary": "先管仓位，再谈进攻，优先围绕核心票和流动性较好的方向展开。",
            "position_suggestion": position_suggestion,
            "signals": signals[:3],
            "empty_message": None,
        }

    def _get_briefing(self, user_id: str) -> dict[str, Any] | None:
        try:
            briefing = self.daily_briefing_service.get_latest_briefing(user_id)
            if briefing is None:
                briefing = self.daily_briefing_service.refresh_daily_briefing(user_id)
            return briefing
        except Exception as exc:
            logger.warning("Homepage briefing unavailable: {}", str(exc))
            return None

    @staticmethod
    def _build_theme_by_ticker(items: list[dict[str, Any]]) -> dict[str, str]:
        theme_by_ticker: dict[str, str] = {}
        for item in items:
            theme_name = str(item.get("theme_name") or "")
            tickers = [
                *list(item.get("core_leaders_json") or []),
                *list(item.get("representative_tickers_json") or []),
            ]
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


_homepage_context_service: Optional[HomepageContextService] = None


def get_homepage_context_service() -> HomepageContextService:
    global _homepage_context_service
    if _homepage_context_service is None:
        _homepage_context_service = HomepageContextService()
    return _homepage_context_service


def reset_homepage_context_service() -> None:
    global _homepage_context_service
    _homepage_context_service = None
