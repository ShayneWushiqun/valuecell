from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional

from .opportunity_pool_service import OpportunityPoolService


class EntryTimingService:
    def __init__(
        self,
        opportunity_pool_service: Optional[OpportunityPoolService] = None,
    ) -> None:
        self.opportunity_pool_service = opportunity_pool_service or OpportunityPoolService()

    def get_entry_timing_signals(self, user_id: str = "default_user") -> dict[str, Any]:
        pool_data = self.opportunity_pool_service.get_opportunity_candidates(user_id=user_id)
        candidates = list(pool_data.get("items") or [])
        items = [self._build_signal(candidate) for candidate in candidates]
        items.sort(
            key=lambda item: (
                -int(item.get("confidence") or 0),
                self._action_rank(str(item.get("action") or "")),
                -int(item.get("priority_score") or 0),
                str(item.get("ticker") or ""),
            )
        )
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "available": bool(items),
            "items": items,
            "count": len(items),
            "empty_message": None if items else "暂无可用买点裁决信号",
        }

    def _build_signal(self, candidate: dict[str, Any]) -> dict[str, Any]:
        tradeability_state = str(candidate.get("tradeability_state") or "")
        candidate_state = str(candidate.get("candidate_state") or "")
        priority_score = int(candidate.get("priority_score") or 0)
        expectation_gap_level = str(candidate.get("expectation_gap_level") or "中")
        role_label = str(candidate.get("role_label") or "跟风")
        trend_quality = str(candidate.get("trend_quality") or "震荡")
        missing_confirmations = list(candidate.get("missing_confirmations") or [])
        invalid_conditions = list(candidate.get("invalid_conditions") or [])
        reasons = list(candidate.get("reasons") or [])

        action = self._resolve_action(
            tradeability_state=tradeability_state,
            candidate_state=candidate_state,
            invalid_conditions=invalid_conditions,
            missing_confirmations=missing_confirmations,
        )
        confidence = self._resolve_confidence(
            priority_score=priority_score,
            candidate_state=candidate_state,
            tradeability_state=tradeability_state,
            expectation_gap_level=expectation_gap_level,
            role_label=role_label,
            trend_quality=trend_quality,
            missing_confirmations=missing_confirmations,
            invalid_conditions=invalid_conditions,
        )
        summary = self._build_summary(
            action=action,
            candidate=candidate,
            expectation_gap_level=expectation_gap_level,
        )
        expectation_gap_view = self._build_expectation_gap_view(expectation_gap_level)
        reasons = self._unique_list(
            [
                *reasons[:2],
                *self._build_action_reasons(
                    action=action,
                    tradeability_state=tradeability_state,
                    expectation_gap_level=expectation_gap_level,
                    role_label=role_label,
                    trend_quality=trend_quality,
                    priority_score=priority_score,
                    missing_confirmations=missing_confirmations,
                    invalid_conditions=invalid_conditions,
                ),
            ]
        )

        return {
            "ticker": candidate.get("ticker"),
            "display_name": candidate.get("display_name"),
            "topic_name": candidate.get("topic_name"),
            "action": action,
            "confidence": confidence,
            "summary": summary,
            "reasons": reasons,
            "tradeability_state": tradeability_state,
            "expectation_gap_view": expectation_gap_view,
            "missing_confirmations": missing_confirmations,
            "invalid_conditions": invalid_conditions,
            "candidate_state": candidate_state,
            "priority_score": priority_score,
            "time_horizon": candidate.get("time_horizon"),
        }

    @staticmethod
    def _resolve_action(
        *,
        tradeability_state: str,
        candidate_state: str,
        invalid_conditions: list[str],
        missing_confirmations: list[str],
    ) -> str:
        if tradeability_state == "流动性风险":
            return "暂不参与"
        if invalid_conditions:
            if tradeability_state == "谨慎追高":
                return "仅适合持有"
            return "暂不参与"
        if tradeability_state == "谨慎追高":
            return "等待回踩确认"
        if candidate_state == "高优先级买点":
            return "接近可参与窗口" if missing_confirmations else "继续观察"
        if candidate_state == "候选买点":
            return "等待回踩确认" if missing_confirmations else "接近可参与窗口"
        if candidate_state == "仅适合持有":
            return "仅适合持有"
        return "继续观察"

    @staticmethod
    def _resolve_confidence(
        *,
        priority_score: int,
        candidate_state: str,
        tradeability_state: str,
        expectation_gap_level: str,
        role_label: str,
        trend_quality: str,
        missing_confirmations: list[str],
        invalid_conditions: list[str],
    ) -> int:
        confidence = 30 + int(priority_score * 0.45)
        if candidate_state == "高优先级买点":
            confidence += 8
        elif candidate_state == "候选买点":
            confidence += 4

        if role_label == "龙头":
            confidence += 6
        elif role_label == "中军":
            confidence += 4

        if trend_quality == "顺势":
            confidence += 6
        elif trend_quality == "走弱":
            confidence -= 10

        if expectation_gap_level == "低":
            confidence -= 14
        elif expectation_gap_level == "高":
            confidence += 4

        if tradeability_state == "谨慎追高":
            confidence -= 10
        elif tradeability_state == "流动性风险":
            confidence -= 20

        confidence -= len(missing_confirmations) * 4
        if invalid_conditions:
            confidence -= 18

        return max(0, min(100, confidence))

    @staticmethod
    def _build_summary(
        *,
        action: str,
        candidate: dict[str, Any],
        expectation_gap_level: str,
    ) -> str:
        topic_name = str(candidate.get("topic_name") or "当前方向")
        display_name = str(candidate.get("display_name") or candidate.get("ticker") or "")
        if action == "暂不参与":
            return f"{display_name} 当前存在风险条件，先回避 {topic_name} 方向参与。"
        if action == "仅适合持有":
            return f"{display_name} 更适合持有观察，当前不宜主动追价。"
        if action == "等待回踩确认":
            return f"{display_name} 接近观察窗口，但仍需等待回踩或承接确认。"
        if action == "接近可参与窗口":
            return f"{display_name} 处于较优观察阶段，但仍需等待进一步确认。"
        return f"{display_name} 仍以观察为主，当前预期差{expectation_gap_level}。"

    @staticmethod
    def _build_expectation_gap_view(expectation_gap_level: str) -> str:
        if expectation_gap_level == "高":
            return "仍有预期差，但需要确认承接与持续性。"
        if expectation_gap_level == "低":
            return "预期差偏低，当前风险收益比不足。"
        return "预期差中性，等待更明确的交易窗口。"

    @staticmethod
    def _build_action_reasons(
        *,
        action: str,
        tradeability_state: str,
        expectation_gap_level: str,
        role_label: str,
        trend_quality: str,
        priority_score: int,
        missing_confirmations: list[str],
        invalid_conditions: list[str],
    ) -> list[str]:
        reasons: list[str] = []
        if invalid_conditions:
            reasons.append("存在风险条件，当前不应激进处理。")
        if tradeability_state == "谨慎追高":
            reasons.append("短线位置偏高，更适合等待回踩而不是直接追价。")
        if tradeability_state == "流动性风险":
            reasons.append("流动性与退出条件不足，需优先回避。")
        if expectation_gap_level == "低":
            reasons.append("预期差偏低，风险收益比不足。")
        if role_label in {"龙头", "中军"} and trend_quality == "顺势" and priority_score >= 70:
            reasons.append("个股处于相对核心位置，趋势仍有延续观察价值。")
        if action == "接近可参与窗口" and missing_confirmations:
            reasons.append("已接近可参与窗口，但仍缺少回踩、承接或量价确认。")
        return reasons

    @staticmethod
    def _action_rank(action: str) -> int:
        order = {
            "接近可参与窗口": 0,
            "等待回踩确认": 1,
            "继续观察": 2,
            "仅适合持有": 3,
            "暂不参与": 4,
        }
        return order.get(action, 9)

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


_entry_timing_service: Optional[EntryTimingService] = None


def get_entry_timing_service() -> EntryTimingService:
    global _entry_timing_service
    if _entry_timing_service is None:
        _entry_timing_service = EntryTimingService()
    return _entry_timing_service


def reset_entry_timing_service() -> None:
    global _entry_timing_service
    _entry_timing_service = None
