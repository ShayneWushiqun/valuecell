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
                "breadth_items": [],
                "index_quotes": [],
                "score": None,
                "empty_message": "暂无可用市场快照",
            }

        data = result.get("data")
        if not isinstance(data, dict):
            return {
                "available": False,
                "market_state": None,
                "summary": None,
                "confidence": None,
                "action_hint": None,
                "signals": [],
                "breadth_items": [],
                "index_quotes": [],
                "score": None,
                "empty_message": "暂无可用市场快照",
            }
        signals = data.get("signals_json", [])
        return {
            "available": True,
            "market_state": data.get("market_state"),
            "summary": data.get("summary"),
            "confidence": data.get("confidence"),
            "action_hint": data.get("action_hint"),
            "signals": signals,
            "breadth_items": self._build_market_breadth_items(signals),
            "index_quotes": self._build_market_index_quotes(),
            "score": data.get("score"),
            "empty_message": None,
        }

    def _build_emotion_cycle(self) -> dict[str, Any]:
        try:
            snapshot = self.emotion_cycle_service.get_emotion_cycle_snapshot()
            timeline = self.emotion_cycle_service.get_emotion_cycle_timeline(window_days=30)
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
                "default_window_days": 20,
                "empty_message": "暂无可用情绪周期数据",
            }

        snapshot_data = snapshot.get("data")
        timeline_data = timeline.get("data") if timeline.get("success") else {}
        if not isinstance(snapshot_data, dict):
            return {
                "available": False,
                "cycle_stage": None,
                "summary": None,
                "action_hint": None,
                "trend_direction": None,
                "stage_points": [],
                "turning_points": [],
                "default_window_days": 20,
                "empty_message": "暂无可用情绪周期数据",
            }
        if not isinstance(timeline_data, dict):
            timeline_data = {}
        stage_points = list(timeline_data.get("stage_points_json", []))
        return {
            "available": True,
            "cycle_stage": snapshot_data.get("cycle_stage"),
            "summary": snapshot_data.get("summary"),
            "action_hint": snapshot_data.get("action_hint"),
            "trend_direction": timeline_data.get("trend_direction"),
            "stage_points": stage_points,
            "turning_points": timeline_data.get("turning_points_json", []),
            "default_window_days": 20,
            "empty_message": None,
        }

    def _build_theme_focus(self) -> dict[str, Any]:
        try:
            result = self.theme_focus_service.get_theme_focus_snapshot(top_n=12)
        except Exception as exc:
            logger.warning("Homepage theme focus unavailable: {}", str(exc))
            result = {"success": False}

        if not result.get("success"):
            return {
                "available": False,
                "items": [],
                "empty_message": "暂无可用题材聚焦数据",
            }

        result_data = result.get("data")
        if not isinstance(result_data, dict):
            return {
                "available": False,
                "items": [],
                "empty_message": "暂无可用题材聚焦数据",
            }

        items = self._build_theme_focus_items(result_data.get("items", []))
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
                self._watchlist_status_rank(item["status"]),
                abs(item["change_percent"] or 0),
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
            focus_points.append(
                f"优先跟踪 {item['theme_name']} 方向，重点看 {item['core_leaders_json'][0] if item['core_leaders_json'] else '代表股'}。"
            )

        if portfolio_handling.get("focus_count", 0) > 0:
            avoid_points.append("已有重点持仓待处理时，避免无差别开新仓。")
        if any(
            item.get("status") == "风险观察"
            for item in watchlist_observation.get("items", [])
        ):
            avoid_points.append("对高波动自选股先确认承接，不宜情绪化追价。")
        if market_overview.get("market_state") in {"退潮", "震荡"}:
            avoid_points.append("弱势环境下优先收缩节奏，避免摊大风险暴露。")
        avoid_points.append("ST 板块尽量不要碰，优先回避博弈性过强的方向。")

        participation_preferences = [
            "默认优先主板 10cm 个股，兼顾流动性和容错率。",
            "创业板机会次之，除非主线非常明确，否则不建议无差别追高。",
            "科创板波动更大，应更谨慎处理，优先作为辅助观察方向。",
        ]

        has_context = any(
            [
                market_overview.get("available"),
                emotion_cycle.get("available"),
                theme_focus.get("available"),
                watchlist_observation.get("available"),
                portfolio_handling.get("available"),
            ]
        )
        if not has_context:
            return {
                "available": False,
                "title": "今日操作框架",
                "summary": None,
                "focus_points": [],
                "avoid_points": [],
                "participation_preferences": [],
                "etf_strategy_hint": None,
                "empty_message": "暂无可用操作框架",
            }

        available = bool(focus_points or avoid_points)
        if not available:
            return {
                "available": False,
                "title": "今日操作框架",
                "summary": None,
                "focus_points": [],
                "avoid_points": [],
                "participation_preferences": [],
                "etf_strategy_hint": None,
                "empty_message": "暂无可用操作框架",
            }

        market_state = market_overview.get("market_state") or "中性"
        cycle_stage = emotion_cycle.get("cycle_stage") or "待确认"
        summary = (
            f"当前以{market_state}市场环境、{cycle_stage}情绪阶段来组织今日节奏，"
            "优先处理强势主线与已有重点持仓。"
        )
        etf_strategy_hint = self._build_etf_strategy_hint(theme_focus.get("items", []))
        return {
            "available": True,
            "title": "今日操作框架",
            "summary": summary,
            "focus_points": focus_points[:4],
            "avoid_points": avoid_points[:4],
            "participation_preferences": participation_preferences,
            "etf_strategy_hint": etf_strategy_hint,
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
            "total_position_range": self._resolve_total_position_range(
                market_state=market_state,
                cycle_stage=cycle_stage,
            ),
            "single_position_range": "单票以 10% - 20% 为主，试错环境再收敛。",
            "build_strategy": self._resolve_build_strategy(
                market_state=market_state,
                cycle_stage=cycle_stage,
            ),
            "theme_concentration_hint": "优先集中在 1 到 2 个主线方向，不建议同时分散押注过多题材。",
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

    def _build_market_index_quotes(self) -> list[dict[str, Any]]:
        index_definitions = [
            ("上证", "SSE:000001"),
            ("深成指", "SZSE:399001"),
            ("创业板", "SZSE:399006"),
            ("科创50", "SSE:000688"),
            ("北证50", "BJSE:899050"),
        ]
        quotes: list[dict[str, Any]] = []
        for label, ticker in index_definitions:
            try:
                result = self.asset_service.get_asset_price(ticker, language="zh-CN")
            except Exception as exc:
                logger.warning("Homepage index quote unavailable for {}: {}", ticker, str(exc))
                result = {"success": False}

            quotes.append(
                {
                    "label": label,
                    "ticker": ticker,
                    "price": result.get("price_formatted") if result.get("success") else None,
                    "change_percent": (
                        result.get("change_percent") if result.get("success") else None
                    ),
                }
            )
        return quotes

    @staticmethod
    def _build_market_breadth_items(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {"label": str(signal.get("label") or ""), "value": signal.get("value")}
            for signal in signals[:6]
        ]

    def _build_theme_focus_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized_items: list[dict[str, Any]] = []
        for item in items:
            theme_name = str(item.get("theme_name") or "")
            leaders = list(item.get("core_leaders_json") or [])
            representatives = list(item.get("representative_tickers_json") or [])
            is_st_related = self._is_st_related_theme(
                theme_name=theme_name,
                leaders=leaders,
                representatives=representatives,
            )
            preferred_market = self._resolve_preferred_market(leaders + representatives)
            normalized_items.append(
                {
                    **item,
                    "theme_state": self._normalize_theme_state(item.get("theme_state")),
                    "trend_state": self._resolve_trend_state(item),
                    "hot_level": item.get("metrics", {}).get("hot_count", 0),
                    "primary_representative": (
                        leaders[0] if leaders else (representatives[0] if representatives else None)
                    ),
                    "is_suitable_for_direct_participation": self._is_suitable_for_direct_participation(
                        item=item,
                        preferred_market=preferred_market,
                        is_st_related=is_st_related,
                    ),
                    "participation_hint": self._build_theme_participation_hint(
                        item=item,
                        preferred_market=preferred_market,
                        is_st_related=is_st_related,
                    ),
                    "preferred_market": preferred_market,
                    "etf_hint": self._build_theme_etf_hint(
                        theme_name=theme_name,
                        preferred_market=preferred_market,
                        is_st_related=is_st_related,
                    ),
                }
            )
        normalized_items.sort(
            key=lambda item: (
                1 if self._is_st_related_theme_item(item) else 0,
                0 if item.get("is_suitable_for_direct_participation") else 1,
                int(item.get("rank", 999) or 999),
            )
        )
        return normalized_items

    @staticmethod
    def _normalize_theme_state(theme_state: Any) -> str:
        if theme_state == "观察":
            return "分歧"
        return str(theme_state or "分歧")

    @staticmethod
    def _resolve_trend_state(item: dict[str, Any]) -> str:
        change_value = float(item.get("metrics", {}).get("change_value", 0) or 0)
        state = str(item.get("theme_state") or "")
        if "退潮" in state:
            return "走弱"
        if state in {"加强", "活跃"} and change_value > 1:
            return "加强"
        if state in {"分歧", "观察"}:
            return "分歧"
        return "横盘"

    @staticmethod
    def _resolve_preferred_market(tickers: list[str]) -> str:
        has_kcb = any(ticker.startswith("SSE:688") for ticker in tickers)
        has_gem = any(ticker.startswith("SZSE:30") for ticker in tickers)
        if has_kcb:
            return "科创板为主"
        if has_gem:
            return "创业板为主"
        return "主板为主"

    def _is_suitable_for_direct_participation(
        self,
        *,
        item: dict[str, Any],
        preferred_market: str,
        is_st_related: bool,
    ) -> bool:
        if is_st_related:
            return False
        if preferred_market == "科创板为主":
            return False
        if preferred_market == "创业板为主":
            return str(item.get("expectation_gap_level")) != "高"
        return str(item.get("theme_state")) in {"加强", "活跃"}

    def _build_theme_participation_hint(
        self,
        *,
        item: dict[str, Any],
        preferred_market: str,
        is_st_related: bool,
    ) -> str:
        if is_st_related:
            return "疑似 ST 或高风险方向，默认回避，不建议参与。"
        if preferred_market == "科创板为主":
            return "方向可继续观察，但直接参与需更谨慎，优先考虑替代跟踪工具。"
        if preferred_market == "创业板为主":
            return "方向有热度，但不建议无差别追高，优先低吸或等待更好位置。"
        if str(item.get("theme_state")) == "退潮":
            return "方向走弱，更适合观察而不是直接参与。"
        return "可优先围绕主板核心票观察承接，再决定是否参与。"

    def _build_theme_etf_hint(
        self,
        *,
        theme_name: str,
        preferred_market: str,
        is_st_related: bool,
    ) -> dict[str, str] | None:
        if is_st_related:
            return None
        if preferred_market == "主板为主" and "证券" not in theme_name:
            return None
        return {
            "title": "可考虑相关场内 ETF 作为替代观察",
            "summary": "当核心个股买不进去、追高性价比偏低，或主要集中在创业板/科创板时，可考虑相关场内 ETF 作为替代观察，暂无匹配具体 ETF。",
            "risk_hint": "ETF 仍需关注流动性、跟踪误差和板块快速退潮带来的回撤风险。",
        }

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

    def _build_etf_strategy_hint(self, items: list[dict[str, Any]]) -> str | None:
        for item in items:
            etf_hint = item.get("etf_hint")
            if etf_hint:
                return f"{etf_hint.get('summary')} {etf_hint.get('risk_hint')}"
        return None

    @staticmethod
    def _contains_st_marker(value: str | None) -> bool:
        text = str(value or "").upper().replace(" ", "")
        return "ST" in text

    def _is_st_related_theme(
        self,
        *,
        theme_name: str,
        leaders: list[str],
        representatives: list[str],
    ) -> bool:
        if self._contains_st_marker(theme_name):
            return True
        return any(
            self._contains_st_marker(text)
            for text in [*leaders, *representatives]
        )

    def _is_st_related_theme_item(self, item: dict[str, Any]) -> bool:
        theme_name = str(item.get("theme_name") or "")
        leaders = list(item.get("core_leaders_json") or [])
        representatives = list(item.get("representative_tickers_json") or [])
        primary_representative = item.get("primary_representative")
        return self._is_st_related_theme(
            theme_name=theme_name,
            leaders=[*leaders, str(primary_representative or "")],
            representatives=representatives,
        )

    @staticmethod
    def _resolve_total_position_range(
        *,
        market_state: str | None,
        cycle_stage: str | None,
    ) -> str:
        if market_state == "进攻" and cycle_stage in {"主升发酵", "高潮一致"}:
            return "5-7成"
        if market_state in {"修复", "轮动"}:
            return "3-5成"
        return "2-3成"

    @staticmethod
    def _resolve_build_strategy(
        *,
        market_state: str | None,
        cycle_stage: str | None,
    ) -> str:
        if market_state == "进攻":
            return "确认后加仓"
        if cycle_stage in {"修复试错", "分歧"}:
            return "分批建仓"
        return "试错仓为主"


_homepage_context_service: Optional[HomepageContextService] = None


def get_homepage_context_service() -> HomepageContextService:
    global _homepage_context_service
    if _homepage_context_service is None:
        _homepage_context_service = HomepageContextService()
    return _homepage_context_service


def reset_homepage_context_service() -> None:
    global _homepage_context_service
    _homepage_context_service = None
