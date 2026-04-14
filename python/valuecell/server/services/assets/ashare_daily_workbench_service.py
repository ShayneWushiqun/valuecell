from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional

from ..portfolio.holding_exit_signal_service import HoldingExitSignalService
from ..portfolio.holding_service import HoldingService
from .decision_alert_persistence_service import DecisionAlertPersistenceService
from .entry_timing_service import EntryTimingService
from .homepage_context_service import HomepageContextService
from .opportunity_pool_service import OpportunityPoolService


class AShareDailyWorkbenchService:
    def __init__(
        self,
        homepage_context_service: Optional[HomepageContextService] = None,
        opportunity_pool_service: Optional[OpportunityPoolService] = None,
        entry_timing_service: Optional[EntryTimingService] = None,
        decision_alert_persistence_service: Optional[DecisionAlertPersistenceService] = None,
        holding_exit_signal_service: Optional[HoldingExitSignalService] = None,
        holding_service: Optional[HoldingService] = None,
    ) -> None:
        self.homepage_context_service = homepage_context_service or HomepageContextService()
        self.opportunity_pool_service = opportunity_pool_service or OpportunityPoolService()
        self.entry_timing_service = entry_timing_service or EntryTimingService()
        self.decision_alert_persistence_service = (
            decision_alert_persistence_service or DecisionAlertPersistenceService()
        )
        self.holding_exit_signal_service = (
            holding_exit_signal_service or HoldingExitSignalService()
        )
        self.holding_service = holding_service or HoldingService()

    def get_overview(self, user_id: str = "default_user") -> dict[str, Any]:
        homepage_context = self.homepage_context_service.get_homepage_context(user_id)
        opportunity_pool = self.opportunity_pool_service.get_opportunity_candidates(user_id)
        entry_timing = self.entry_timing_service.get_entry_timing_signals(user_id)
        active_alerts = self.decision_alert_persistence_service.list_alerts(
            user_id=user_id,
            status="active",
            limit=50,
        )
        unread_alerts = self.decision_alert_persistence_service.list_alerts(
            user_id=user_id,
            status="unread",
            limit=200,
        )
        holding_exit_signals = self.holding_exit_signal_service.list_exit_signals(user_id)

        active_alert_items = list(active_alerts.get("items") or [])
        opportunity_items = list(opportunity_pool.get("items") or [])
        entry_timing_items = list(entry_timing.get("items") or [])
        holding_items = list(holding_exit_signals.get("items") or [])

        top_alerts = self._build_top_alerts(active_alert_items)
        top_opportunities = self._build_top_opportunities(
            opportunity_items=opportunity_items,
            entry_timing_items=entry_timing_items,
        )
        top_holdings_to_handle = self._build_top_holdings_to_handle(holding_items)
        top_holdings_stable = self._build_top_holdings_stable(holding_items)
        overview_available = bool(
            homepage_context or top_alerts or top_opportunities or holding_items
        )

        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "available": overview_available,
            "empty_message": None
            if overview_available
            else "当前暂无可用总控台摘要，请稍后再试。",
            "market_digest": self._build_market_digest(homepage_context),
            "attention_digest": self._build_attention_digest(
                unread_count=int(unread_alerts.get("unread_count") or 0),
                active_alert_items=active_alert_items,
                entry_timing_items=entry_timing_items,
                holding_items=holding_items,
            ),
            "top_alerts": top_alerts,
            "top_opportunities": top_opportunities,
            "top_holdings_to_handle": top_holdings_to_handle,
            "top_holdings_stable": top_holdings_stable,
            "today_action_queue": self._build_today_action_queue(
                active_alert_items=active_alert_items,
                top_opportunities=top_opportunities,
                top_holdings_to_handle=top_holdings_to_handle,
            ),
            "quick_links": {
                "opportunities": "/home/opportunities",
                "alerts": "/home/alerts",
                "strategy_preferences": "/home/strategy-preferences",
                "portfolio": "/home",
            },
        }

    def refresh(self, user_id: str = "default_user") -> dict[str, Any]:
        refreshed_alerts = self.decision_alert_persistence_service.refresh_alerts(user_id=user_id)
        holdings = self.holding_service.list_holdings(user_id)
        refreshed_holding_signals = [
            result
            for result in (
                self.holding_exit_signal_service.get_exit_signal(
                    user_id=user_id,
                    holding_id=int(holding["id"]),
                    force_refresh=True,
                )
                for holding in holdings
            )
            if result is not None
        ]
        opportunity_pool = self.opportunity_pool_service.get_opportunity_candidates(user_id)
        entry_timing = self.entry_timing_service.get_entry_timing_signals(user_id)

        near_entry_count = len(
            [
                item
                for item in list(entry_timing.get("items") or [])
                if str(item.get("action") or "") == "接近可参与窗口"
            ]
        )
        holding_action_count = len(
            [
                item
                for item in refreshed_holding_signals
                if str(item.get("action") or "")
                in {"纪律止损", "保护利润", "减仓观察"}
            ]
        )
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "success": True,
            "message": "总控台已按显式刷新要求更新摘要。",
            "refreshed_alert_count": int(refreshed_alerts.get("count") or 0),
            "refreshed_holding_signal_count": len(refreshed_holding_signals),
            "opportunity_candidate_count": int(opportunity_pool.get("count") or 0),
            "near_entry_count": near_entry_count,
            "holding_action_count": holding_action_count,
        }

    @staticmethod
    def _build_market_digest(homepage_context: dict[str, Any]) -> dict[str, Any]:
        market_overview = homepage_context.get("market_overview") or {}
        emotion_cycle = homepage_context.get("emotion_cycle") or {}
        action_framework = homepage_context.get("action_framework") or {}
        return {
            "market_state": market_overview.get("market_state"),
            "emotion_stage": emotion_cycle.get("cycle_stage"),
            "temperature_score": market_overview.get("score"),
            "action_rhythm": action_framework.get("summary")
            or market_overview.get("action_hint"),
            "summary": market_overview.get("summary"),
        }

    @staticmethod
    def _build_attention_digest(
        *,
        unread_count: int,
        active_alert_items: list[dict[str, Any]],
        entry_timing_items: list[dict[str, Any]],
        holding_items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        risk_alert_count = len(
            [
                item
                for item in active_alert_items
                if str(item.get("alert_type") or "") == "风险回避"
            ]
        )
        near_entry_count = len(
            [
                item
                for item in entry_timing_items
                if str(item.get("action") or "") == "接近可参与窗口"
            ]
        )
        holding_risk_count = len(
            [
                item
                for item in holding_items
                if str(item.get("action") or "") in {"纪律止损", "保护利润", "减仓观察"}
            ]
        )
        holding_profit_protection_count = len(
            [
                item
                for item in holding_items
                if str(item.get("action") or "") == "保护利润"
            ]
        )
        return {
            "unread_alert_count": unread_count,
            "risk_alert_count": risk_alert_count,
            "near_entry_count": near_entry_count,
            "holding_risk_count": holding_risk_count,
            "holding_profit_protection_count": holding_profit_protection_count,
        }

    @staticmethod
    def _build_top_alerts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        def rank(item: dict[str, Any]) -> tuple[int, int]:
            alert_type = str(item.get("alert_type") or "")
            priority = str(item.get("priority") or "")
            return (
                0 if alert_type == "风险回避" else 1,
                0 if priority == "high" else 1,
            )

        sorted_items = sorted(items, key=rank)
        return sorted_items[:5]

    @staticmethod
    def _build_top_opportunities(
        *,
        opportunity_items: list[dict[str, Any]],
        entry_timing_items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        entry_timing_by_ticker = {
            str(item.get("ticker") or ""): item for item in entry_timing_items
        }
        ranked = sorted(
            opportunity_items,
            key=lambda item: (
                0
                if str(
                    (entry_timing_by_ticker.get(str(item.get("ticker") or "")) or {}).get("action")
                    or ""
                )
                == "接近可参与窗口"
                else 1,
                -int(item.get("priority_score") or 0),
            ),
        )
        result: list[dict[str, Any]] = []
        for item in ranked[:5]:
            signal = entry_timing_by_ticker.get(str(item.get("ticker") or "")) or {}
            result.append(
                {
                    "ticker": item.get("ticker"),
                    "display_name": item.get("display_name"),
                    "topic_name": item.get("topic_name"),
                    "action": signal.get("action") or item.get("action_hint"),
                    "candidate_state": item.get("candidate_state"),
                    "tradeability_state": item.get("tradeability_state"),
                    "priority_score": item.get("priority_score"),
                }
            )
        return result

    @staticmethod
    def _build_top_holdings_to_handle(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        action_rank = {
            "纪律止损": 0,
            "保护利润": 1,
            "减仓观察": 2,
            "持有观察": 3,
            "继续持有": 4,
        }
        ranked = sorted(
            [item for item in items if str(item.get("action") or "") != "继续持有"],
            key=lambda item: (
                action_rank.get(str(item.get("action") or ""), 9),
                -int(item.get("confidence") or 0),
            ),
        )
        return ranked[:5]

    @staticmethod
    def _build_top_holdings_stable(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        ranked = sorted(
            [
                item
                for item in items
                if str(item.get("action") or "") in {"继续持有", "持有观察"}
            ],
            key=lambda item: (
                0 if str(item.get("action") or "") == "继续持有" else 1,
                -int(item.get("confidence") or 0),
            ),
        )
        return ranked[:3]

    @staticmethod
    def _build_today_action_queue(
        *,
        active_alert_items: list[dict[str, Any]],
        top_opportunities: list[dict[str, Any]],
        top_holdings_to_handle: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        queue: list[dict[str, Any]] = []
        risk_alert_count = len(
            [
                item
                for item in active_alert_items
                if str(item.get("alert_type") or "") == "风险回避"
            ]
        )
        if risk_alert_count:
            queue.append(
                {
                    "title": "先看风险回避提醒",
                    "reason": f"当前有 {risk_alert_count} 条风险回避提醒，风险优先。",
                    "target_path": "/home/alerts",
                }
            )
        if top_holdings_to_handle:
            queue.append(
                {
                    "title": "再看需要处理的持仓",
                    "reason": "已有持仓的保护利润、减仓观察或纪律止损优先于追新机会。",
                    "target_path": "/home",
                }
            )
        if top_opportunities:
            queue.append(
                {
                    "title": "然后看机会池前排",
                    "reason": "优先确认接近可参与窗口和高优先级候选，但不构成交易指令。",
                    "target_path": "/home/opportunities",
                }
            )
        queue.append(
            {
                "title": "最后检查策略偏好",
                "reason": "确认当前偏好模板是否仍匹配今天的节奏和风险环境。",
                "target_path": "/home/strategy-preferences",
            }
        )
        return queue[:5]


_ashare_daily_workbench_service: Optional[AShareDailyWorkbenchService] = None


def get_ashare_daily_workbench_service() -> AShareDailyWorkbenchService:
    global _ashare_daily_workbench_service
    if _ashare_daily_workbench_service is None:
        _ashare_daily_workbench_service = AShareDailyWorkbenchService()
    return _ashare_daily_workbench_service


def reset_ashare_daily_workbench_service() -> None:
    global _ashare_daily_workbench_service
    _ashare_daily_workbench_service = None
