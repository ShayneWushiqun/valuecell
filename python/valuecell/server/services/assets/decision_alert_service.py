from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional

from .entry_timing_service import EntryTimingService


class DecisionAlertService:
    def __init__(
        self,
        entry_timing_service: Optional[EntryTimingService] = None,
    ) -> None:
        self.entry_timing_service = entry_timing_service or EntryTimingService()

    def get_decision_alert_summary(self, user_id: str = "default_user") -> dict[str, Any]:
        items = self.build_decision_alerts(user_id=user_id)
        return self.build_summary_payload(items)

    def build_decision_alerts(self, user_id: str = "default_user") -> list[dict[str, Any]]:
        signal_data = self.entry_timing_service.get_entry_timing_signals(user_id=user_id)
        signals = list(signal_data.get("items") or [])
        items = [self._build_alert(signal) for signal in signals]
        items.sort(
            key=lambda item: (
                -int(item.get("confidence") or 0),
                self._alert_type_rank(str(item.get("alert_type") or "")),
                self._priority_rank(str(item.get("priority") or "")),
                str(item.get("ticker") or ""),
            )
        )
        return items

    @staticmethod
    def build_summary_payload(items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "available": bool(items),
            "items": items,
            "count": len(items),
            "empty_message": None if items else "暂无可用提醒摘要",
        }

    def _build_alert(self, signal: dict[str, Any]) -> dict[str, Any]:
        action = str(signal.get("action") or "继续观察")
        confidence = int(signal.get("confidence") or 0)
        alert_type = self._map_alert_type(action)
        priority = self._resolve_priority(confidence=confidence, alert_type=alert_type)
        title = self._build_title(
            display_name=str(signal.get("display_name") or signal.get("ticker") or ""),
            alert_type=alert_type,
        )
        body = self._build_body(
            signal=signal,
            alert_type=alert_type,
        )
        next_action = self._build_next_action(
            alert_type=alert_type,
            signal=signal,
        )
        reasons = self._unique_list(
            [
                *list(signal.get("reasons") or [])[:2],
                *self._build_reasons(alert_type=alert_type, signal=signal),
            ]
        )
        return {
            "ticker": signal.get("ticker"),
            "display_name": signal.get("display_name"),
            "topic_name": signal.get("topic_name"),
            "alert_type": alert_type,
            "priority": priority,
            "title": title,
            "body": body,
            "next_action": next_action,
            "action": action,
            "confidence": confidence,
            "source": "entry_timing_signals",
            "reasons": reasons,
        }

    @staticmethod
    def _map_alert_type(action: str) -> str:
        mapping = {
            "接近可参与窗口": "买点接近",
            "等待回踩确认": "等待确认",
            "仅适合持有": "持有观察",
            "暂不参与": "风险回避",
            "继续观察": "等待确认",
        }
        return mapping.get(action, "等待确认")

    @staticmethod
    def _resolve_priority(*, confidence: int, alert_type: str) -> str:
        if alert_type == "风险回避":
            return "high" if confidence >= 45 else "medium"
        if confidence >= 75:
            return "high"
        if confidence >= 55:
            return "medium"
        return "low"

    @staticmethod
    def _build_title(*, display_name: str, alert_type: str) -> str:
        if alert_type == "买点接近":
            return f"{display_name} 接近可参与窗口"
        if alert_type == "等待确认":
            return f"{display_name} 仍需等待确认"
        if alert_type == "持有观察":
            return f"{display_name} 更适合持有观察"
        return f"{display_name} 当前应风险回避"

    @staticmethod
    def _build_body(
        *,
        signal: dict[str, Any],
        alert_type: str,
    ) -> str:
        display_name = str(signal.get("display_name") or signal.get("ticker") or "")
        topic_name = str(signal.get("topic_name") or "当前方向")
        summary = str(signal.get("summary") or "")
        if alert_type == "买点接近":
            return f"{display_name} 在 {topic_name} 方向进入接近可参与窗口的观察阶段，{summary}"
        if alert_type == "等待确认":
            return f"{display_name} 目前更适合继续等待确认，{summary}"
        if alert_type == "持有观察":
            return f"{display_name} 当前更适合持有观察，{summary}"
        return f"{display_name} 当前存在风险条件，先回避 {topic_name} 方向，{summary}"

    @staticmethod
    def _build_next_action(
        *,
        alert_type: str,
        signal: dict[str, Any],
    ) -> str:
        missing_confirmations = list(signal.get("missing_confirmations") or [])
        invalid_conditions = list(signal.get("invalid_conditions") or [])
        if alert_type == "买点接近":
            if missing_confirmations:
                return f"继续观察：{missing_confirmations[0]}"
            return "继续观察承接、量价与回踩确认。"
        if alert_type == "等待确认":
            if missing_confirmations:
                return f"下一步重点确认：{missing_confirmations[0]}"
            return "等待更明确的回踩、承接或趋势确认。"
        if alert_type == "持有观察":
            return "优先跟踪趋势是否延续，不主动追价。"
        if invalid_conditions:
            return f"先回避，重点关注：{invalid_conditions[0]}"
        return "先回避风险，等待条件改善后再评估。"

    @staticmethod
    def _build_reasons(
        *,
        alert_type: str,
        signal: dict[str, Any],
    ) -> list[str]:
        reasons: list[str] = []
        if alert_type == "买点接近":
            reasons.append("当前信号更接近可参与窗口，但仍需确认，不构成直接买入建议。")
        elif alert_type == "等待确认":
            reasons.append("当前仍缺少足够确认条件，暂不宜激进处理。")
        elif alert_type == "持有观察":
            reasons.append("当前位置更适合持有与观察，不宜追价。")
        else:
            reasons.append("存在明确风险条件，应优先风险回避。")

        expectation_gap_view = str(signal.get("expectation_gap_view") or "").strip()
        if expectation_gap_view:
            reasons.append(expectation_gap_view)
        return reasons

    @staticmethod
    def _alert_type_rank(alert_type: str) -> int:
        order = {
            "买点接近": 0,
            "等待确认": 1,
            "持有观察": 2,
            "风险回避": 3,
        }
        return order.get(alert_type, 9)

    @staticmethod
    def _priority_rank(priority: str) -> int:
        order = {"high": 0, "medium": 1, "low": 2}
        return order.get(priority, 9)

    @staticmethod
    def _unique_list(values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            text = str(value or "").strip()
            if text and text not in seen:
                seen.add(text)
                result.append(text)
        return result


_decision_alert_service: Optional[DecisionAlertService] = None


def get_decision_alert_service() -> DecisionAlertService:
    global _decision_alert_service
    if _decision_alert_service is None:
        _decision_alert_service = DecisionAlertService()
    return _decision_alert_service


def reset_decision_alert_service() -> None:
    global _decision_alert_service
    _decision_alert_service = None
