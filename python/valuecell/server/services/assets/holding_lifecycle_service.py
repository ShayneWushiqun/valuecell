from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional

from ..portfolio.holding_exit_signal_service import HoldingExitSignalService
from ..portfolio.holding_service import HoldingService
from .decision_alert_persistence_service import DecisionAlertPersistenceService
from .homepage_context_service import HomepageContextService

STAGE_ORDER = {
    "破逻辑退出期": 0,
    "退潮减仓期": 1,
    "分歧确认期": 2,
    "主升持有期": 3,
    "建仓观察期": 4,
}


class HoldingLifecycleService:
    def __init__(
        self,
        holding_service: Optional[HoldingService] = None,
        holding_exit_signal_service: Optional[HoldingExitSignalService] = None,
        decision_alert_persistence_service: Optional[DecisionAlertPersistenceService] = None,
        homepage_context_service: Optional[HomepageContextService] = None,
    ) -> None:
        self.holding_service = holding_service or HoldingService()
        self.holding_exit_signal_service = (
            holding_exit_signal_service or HoldingExitSignalService()
        )
        self.decision_alert_persistence_service = (
            decision_alert_persistence_service or DecisionAlertPersistenceService()
        )
        self.homepage_context_service = homepage_context_service or HomepageContextService()

    def get_overview(self, user_id: str = "default_user") -> dict[str, Any]:
        holdings = self.holding_service.list_holdings(user_id)
        exit_signal_result = self.holding_exit_signal_service.list_exit_signals(user_id)
        active_alert_result = self.decision_alert_persistence_service.list_alerts(
            user_id=user_id,
            status="active",
            limit=200,
        )
        homepage_context = self.homepage_context_service.get_homepage_context(user_id)
        exit_signal_by_holding_id = {
            int(item.get("holding_id") or 0): item
            for item in list(exit_signal_result.get("items") or [])
            if int(item.get("holding_id") or 0) > 0
        }
        active_alert_tickers = {
            str(item.get("ticker") or "")
            for item in list(active_alert_result.get("items") or [])
            if str(item.get("ticker") or "")
        }
        items = [
            self._build_lifecycle_item(
                holding=holding,
                exit_signal=exit_signal_by_holding_id.get(int(holding.get("id") or 0)),
                homepage_context=homepage_context,
                has_active_alerts=str(holding.get("ticker") or "") in active_alert_tickers,
            )
            for holding in holdings
        ]
        items.sort(key=self._sort_key)
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "available": bool(items),
            "empty_message": None if items else "暂无可用持仓周期视图。",
            "items": items,
            "count": len(items),
            "summary": self._build_summary(items),
        }

    def get_holding_lifecycle(
        self,
        *,
        user_id: str,
        holding_id: int,
    ) -> dict[str, Any] | None:
        overview = self.get_overview(user_id)
        item = next(
            (entry for entry in overview["items"] if int(entry["holding_id"]) == holding_id),
            None,
        )
        if item is None:
            return None
        return {
            "generated_at": overview["generated_at"],
            "available": True,
            "empty_message": None,
            "item": item,
        }

    def _build_lifecycle_item(
        self,
        *,
        holding: dict[str, Any],
        exit_signal: dict[str, Any] | None,
        homepage_context: dict[str, Any],
        has_active_alerts: bool,
    ) -> dict[str, Any]:
        context_snapshot = dict((exit_signal or {}).get("context_snapshot") or {})
        decision_context = dict(context_snapshot.get("decision_context") or {})
        theme_context = dict(decision_context.get("theme_context") or {})
        candidate_context = dict(decision_context.get("candidate_context") or {})
        risk_context = dict(decision_context.get("risk_context") or {})
        market_context = dict(decision_context.get("market_context") or {})
        market_context = market_context or self._build_market_context(homepage_context)
        action = str((exit_signal or {}).get("action") or "持有观察")
        role_label = str(theme_context.get("role_label") or "")
        trend_quality = str(theme_context.get("trend_quality") or "")
        tradeability_state = str(candidate_context.get("tradeability_state") or "")
        expectation_state = str(candidate_context.get("expectation_gap_level") or "")
        risk_items = list(risk_context.get("items") or [])
        invalid_conditions = list((exit_signal or {}).get("invalid_conditions") or [])
        lifecycle_stage = self._resolve_lifecycle_stage(
            action=action,
            role_label=role_label,
            trend_quality=trend_quality,
            tradeability_state=tradeability_state,
            risk_items=risk_items,
            invalid_conditions=invalid_conditions,
        )
        return {
            "holding_id": int(holding.get("id") or 0),
            "ticker": str(holding.get("ticker") or ""),
            "display_name": str(holding.get("asset_name") or holding.get("ticker") or ""),
            "lifecycle_stage": lifecycle_stage,
            "action": action,
            "confidence": int((exit_signal or {}).get("confidence") or 35),
            "summary": str((exit_signal or {}).get("summary") or "保持持仓观察。"),
            "theme_name": theme_context.get("topic_name"),
            "role_label": role_label or None,
            "trend_quality": trend_quality or None,
            "tradeability_state": tradeability_state or None,
            "expectation_state": expectation_state or None,
            "observation_window": self._build_observation_window(
                lifecycle_stage=lifecycle_stage,
                market_state=str(market_context.get("market_state") or ""),
            ),
            "invalid_conditions": invalid_conditions,
            "risk_controls": list((exit_signal or {}).get("risk_controls") or []),
            "profit_protection_view": (exit_signal or {}).get("profit_protection_view"),
            "position_hint": self._build_position_hint(
                lifecycle_stage=lifecycle_stage,
                market_state=str(market_context.get("market_state") or ""),
                role_label=role_label,
            ),
            "has_active_alerts": has_active_alerts,
            "decision_context_available": bool(decision_context.get("available")),
        }

    @staticmethod
    def _build_market_context(homepage_context: dict[str, Any]) -> dict[str, Any]:
        market_overview = dict(homepage_context.get("market_overview") or {})
        emotion_cycle = dict(homepage_context.get("emotion_cycle") or {})
        return {
            "market_state": market_overview.get("market_state"),
            "emotion_stage": emotion_cycle.get("cycle_stage"),
        }

    @staticmethod
    def _resolve_lifecycle_stage(
        *,
        action: str,
        role_label: str,
        trend_quality: str,
        tradeability_state: str,
        risk_items: list[str],
        invalid_conditions: list[str],
    ) -> str:
        risk_text = " ".join(risk_items + invalid_conditions)
        is_core = role_label in {"龙头", "中军"}
        if action == "纪律止损":
            return "破逻辑退出期"
        if action in {"保护利润", "减仓观察"}:
            if any(word in risk_text for word in ("退潮", "走弱", "流动性", "卖不出")):
                return "退潮减仓期"
            return "分歧确认期"
        if action == "持有观察":
            if tradeability_state == "谨慎追高" or invalid_conditions:
                return "分歧确认期"
            return "建仓观察期"
        if is_core and trend_quality != "走弱":
            return "主升持有期"
        return "建仓观察期"

    @staticmethod
    def _build_observation_window(*, lifecycle_stage: str, market_state: str) -> str:
        if lifecycle_stage == "建仓观察期":
            return f"未来 1-3 个交易日关注承接与确认，当前市场状态为 {market_state or '待观察'}。"
        if lifecycle_stage == "主升持有期":
            return "未来 3-5 个交易日重点看趋势是否延续，不把短线噪音外推成失效。"
        if lifecycle_stage == "分歧确认期":
            return "未来 1-2 个交易日重点看分歧后是否修复，以及量价是否继续匹配。"
        if lifecycle_stage == "退潮减仓期":
            return "未来 1-2 个交易日优先观察减仓节奏与退出难度，先控风险再谈机会。"
        return "未来 1 个交易日优先看逻辑是否继续失效，以及是否存在退出难度。"

    @staticmethod
    def _build_position_hint(*, lifecycle_stage: str, market_state: str, role_label: str) -> str:
        if lifecycle_stage == "主升持有期":
            return f"当前以继续持有为主，优先跟踪 {role_label or '核心票'} 的趋势延续，不主动放大动作。"
        if lifecycle_stage == "分歧确认期":
            return f"当前更适合控制节奏，先确认分歧是否修复；市场状态 {market_state or '待观察'}。"
        if lifecycle_stage == "退潮减仓期":
            return "当前应优先收缩风险和保护已有利润，不把任何回抽误判成重新进攻。"
        if lifecycle_stage == "破逻辑退出期":
            return "当前以退出框架和执行顺序为主，若存在流动性压力需优先考虑退出难度。"
        return "当前以持有观察为主，等待更清晰的确认信号。"

    @staticmethod
    def _build_summary(items: list[dict[str, Any]]) -> dict[str, int]:
        need_attention = {"破逻辑退出期", "退潮减仓期", "分歧确认期"}
        high_risk = {"破逻辑退出期", "退潮减仓期"}
        return {
            "total_count": len(items),
            "need_attention_count": len(
                [item for item in items if item.get("lifecycle_stage") in need_attention]
            ),
            "major_hold_count": len(
                [item for item in items if item.get("lifecycle_stage") == "主升持有期"]
            ),
            "high_risk_count": len(
                [item for item in items if item.get("lifecycle_stage") in high_risk]
            ),
            "active_alert_count": len(
                [item for item in items if bool(item.get("has_active_alerts"))]
            ),
        }

    @staticmethod
    def _sort_key(item: dict[str, Any]) -> tuple[int, int, str]:
        return (
            STAGE_ORDER.get(str(item.get("lifecycle_stage") or ""), 99),
            -int(item.get("confidence") or 0),
            str(item.get("ticker") or ""),
        )


_holding_lifecycle_service: Optional[HoldingLifecycleService] = None


def get_holding_lifecycle_service() -> HoldingLifecycleService:
    global _holding_lifecycle_service
    if _holding_lifecycle_service is None:
        _holding_lifecycle_service = HoldingLifecycleService()
    return _holding_lifecycle_service


def reset_holding_lifecycle_service() -> None:
    global _holding_lifecycle_service
    _holding_lifecycle_service = None
