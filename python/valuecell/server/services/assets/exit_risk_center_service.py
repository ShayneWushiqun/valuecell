from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional

from ..portfolio.holding_exit_signal_service import HoldingExitSignalService
from ..portfolio.holding_service import HoldingService
from .decision_alert_persistence_service import DecisionAlertPersistenceService

ACTION_PRIORITY = {
    "纪律止损": 0,
    "保护利润": 1,
    "减仓观察": 2,
    "持有观察": 3,
    "继续持有": 4,
}


class ExitRiskCenterService:
    def __init__(
        self,
        holding_service: Optional[HoldingService] = None,
        holding_exit_signal_service: Optional[HoldingExitSignalService] = None,
        decision_alert_persistence_service: Optional[DecisionAlertPersistenceService] = None,
    ) -> None:
        self.holding_service = holding_service or HoldingService()
        self.holding_exit_signal_service = (
            holding_exit_signal_service or HoldingExitSignalService()
        )
        self.decision_alert_persistence_service = (
            decision_alert_persistence_service or DecisionAlertPersistenceService()
        )

    def get_overview(self, user_id: str = "default_user") -> dict[str, Any]:
        holdings = self.holding_service.list_holdings(user_id)
        exit_signal_result = self.holding_exit_signal_service.list_exit_signals(user_id)
        active_alert_result = self.decision_alert_persistence_service.list_alerts(
            user_id=user_id,
            status="active",
            limit=200,
        )
        holding_by_id = {int(item.get("id") or 0): item for item in holdings}
        active_alert_tickers = {
            str(item.get("ticker") or "")
            for item in list(active_alert_result.get("items") or [])
            if str(item.get("ticker") or "")
        }
        items = [
            self._build_risk_item(
                exit_signal=item,
                holding=holding_by_id.get(int(item.get("holding_id") or 0)),
                has_active_alerts=str(item.get("ticker") or "") in active_alert_tickers,
            )
            for item in list(exit_signal_result.get("items") or [])
        ]
        items.sort(key=self._sort_key)
        return self._build_overview_payload(items)

    def refresh(self, user_id: str = "default_user") -> dict[str, Any]:
        holdings = self.holding_service.list_holdings(user_id)
        for holding in holdings:
            holding_id = int(holding.get("id") or 0)
            if holding_id <= 0:
                continue
            self.holding_exit_signal_service.get_exit_signal(
                user_id=user_id,
                holding_id=holding_id,
                force_refresh=True,
            )
        overview = self.get_overview(user_id)
        overview["refreshed_count"] = len(holdings)
        return overview

    def _build_risk_item(
        self,
        *,
        exit_signal: dict[str, Any],
        holding: dict[str, Any] | None,
        has_active_alerts: bool,
    ) -> dict[str, Any]:
        context_snapshot = dict(exit_signal.get("context_snapshot") or {})
        decision_context = dict(context_snapshot.get("decision_context") or {})
        theme_context = dict(decision_context.get("theme_context") or {})
        risk_context = dict(decision_context.get("risk_context") or {})
        risk_items = list(risk_context.get("items") or [])
        invalid_conditions = list(exit_signal.get("invalid_conditions") or [])
        risk_text = " ".join(risk_items + invalid_conditions)
        liquidity_warning = self._build_liquidity_warning(risk_text)
        risk_type = self._resolve_risk_type(
            action=str(exit_signal.get("action") or "持有观察"),
            role_label=str(theme_context.get("role_label") or ""),
            trend_quality=str(theme_context.get("trend_quality") or ""),
            risk_text=risk_text,
            has_active_alerts=has_active_alerts,
        )
        return {
            "holding_id": int(exit_signal.get("holding_id") or 0),
            "ticker": str(exit_signal.get("ticker") or ""),
            "display_name": str(
                exit_signal.get("asset_name")
                or (holding or {}).get("asset_name")
                or exit_signal.get("ticker")
                or ""
            ),
            "action": str(exit_signal.get("action") or "持有观察"),
            "confidence": int(exit_signal.get("confidence") or 35),
            "risk_type": risk_type,
            "summary": str(exit_signal.get("summary") or "保持观察。"),
            "thesis": str(exit_signal.get("thesis") or "以持仓风险框架为主。"),
            "evidence": list(exit_signal.get("evidence") or []),
            "disagreement": list(exit_signal.get("disagreement") or []),
            "invalid_conditions": invalid_conditions,
            "risk_controls": list(exit_signal.get("risk_controls") or []),
            "liquidity_warning": liquidity_warning,
            "expected_exit_plan": self._build_expected_exit_plan(
                action=str(exit_signal.get("action") or "持有观察"),
                liquidity_warning=liquidity_warning,
            ),
            "has_active_alerts": has_active_alerts,
            "theme_name": theme_context.get("topic_name"),
            "role_label": theme_context.get("role_label"),
        }

    @staticmethod
    def _resolve_risk_type(
        *,
        action: str,
        role_label: str,
        trend_quality: str,
        risk_text: str,
        has_active_alerts: bool,
    ) -> str:
        if action == "保护利润":
            return "保护利润"
        if "流动性" in risk_text or "卖不出" in risk_text or "跌停" in risk_text:
            return "流动性风险"
        if "退潮" in risk_text:
            return "题材退潮"
        if "证伪" in risk_text or action == "纪律止损":
            return "预期证伪"
        if role_label not in {"龙头", "中军"} and trend_quality == "走弱":
            return "跟风掉队"
        if has_active_alerts and "公告" in risk_text:
            return "事件风险"
        return "节奏转弱"

    @staticmethod
    def _build_liquidity_warning(risk_text: str) -> str | None:
        if "流动性" in risk_text or "卖不出" in risk_text or "跌停" in risk_text:
            return "当前存在退出难度或流动性压力，处理时需要优先考虑成交与滑点风险。"
        return None

    @staticmethod
    def _build_expected_exit_plan(*, action: str, liquidity_warning: str | None) -> str:
        if action == "纪律止损":
            return "优先确认失效条件是否继续成立，并在可成交前提下执行退出计划。"
        if action == "保护利润":
            return "优先收缩风险和保护已有利润，不把回抽误判成重新进攻。"
        if action == "减仓观察":
            return "先减轻暴露，再观察题材与趋势是否修复。"
        if action == "持有观察":
            return "当前以持有观察为主，等待更清晰确认，再决定是否调整。"
        if liquidity_warning:
            return "当前先看退出难度，再决定处理顺序。"
        return "当前以继续持有和风险跟踪为主。"

    def _build_overview_payload(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        profit_protection_items = [item for item in items if item["action"] == "保护利润"]
        discipline_stop_items = [item for item in items if item["action"] == "纪律止损"]
        watch_items = [item for item in items if item["action"] in {"继续持有", "持有观察"}]
        high_priority_items = [
            item for item in items if item["action"] in {"纪律止损", "保护利润", "减仓观察"}
        ]
        risk_buckets: dict[str, int] = {}
        for item in items:
            risk_type = str(item.get("risk_type") or "节奏转弱")
            risk_buckets[risk_type] = risk_buckets.get(risk_type, 0) + 1
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "available": bool(items),
            "empty_message": None if items else "暂无可用卖点与风险中心数据。",
            "high_priority_items": high_priority_items,
            "profit_protection_items": profit_protection_items,
            "discipline_stop_items": discipline_stop_items,
            "watch_items": watch_items,
            "risk_buckets": risk_buckets,
            "count": len(items),
        }

    @staticmethod
    def _sort_key(item: dict[str, Any]) -> tuple[int, int, str]:
        return (
            ACTION_PRIORITY.get(str(item.get("action") or ""), 99),
            -int(item.get("confidence") or 0),
            str(item.get("ticker") or ""),
        )


_exit_risk_center_service: Optional[ExitRiskCenterService] = None


def get_exit_risk_center_service() -> ExitRiskCenterService:
    global _exit_risk_center_service
    if _exit_risk_center_service is None:
        _exit_risk_center_service = ExitRiskCenterService()
    return _exit_risk_center_service


def reset_exit_risk_center_service() -> None:
    global _exit_risk_center_service
    _exit_risk_center_service = None
