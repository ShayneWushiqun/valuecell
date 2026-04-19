from __future__ import annotations

from typing import Any, Optional, Sequence

from ...db.repositories.stock_analysis_research_feedback_repository import (
    StockAnalysisResearchFeedbackRepository,
)
from ...api.schemas.stock_analysis_adaptive_planning import (
    StockAnalysisAdaptivePlanningData,
    StockAnalysisPlanningPreferenceData,
)

PLANNING_PROFILES = {
    "balanced",
    "refresh_first",
    "compare_first",
    "internal_first",
    "external_confirm_first",
    "lightweight_research",
}

SOURCE_TO_ACTION = {
    "explicit_context": "inspect_context_cards",
    "compare_targets": "inspect_compare_targets",
    "active_memory": "inspect_active_memory",
    "active_compression": "inspect_active_compression",
    "internal_structured": "collect_internal_structured_evidence",
    "market_price": "collect_market_price_evidence",
    "external_news": "collect_external_evidence",
    "external_confirmation": "collect_external_evidence",
    "validation": "validate_thesis",
    "refresh": "refresh_stale_contexts",
}


def _clean_text(value: Any, *, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def _unique_str_list(values: Sequence[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = _clean_text(value)
        if text and text not in result:
            result.append(text)
    return result


class StockAnalysisAdaptivePlanningService:
    def __init__(
        self,
        stock_analysis_research_feedback_repository: Optional[
            StockAnalysisResearchFeedbackRepository
        ] = None,
    ) -> None:
        self.stock_analysis_research_feedback_repository = (
            stock_analysis_research_feedback_repository
            or StockAnalysisResearchFeedbackRepository()
        )

    def build_adaptive_planning(
        self,
        *,
        user_id: str,
        thread_id: int,
        thread: dict[str, Any],
        context_cards: Sequence[dict[str, Any]],
        active_memory: dict[str, Any] | None,
        active_compression: dict[str, Any] | None,
        open_tasks: Sequence[dict[str, Any]],
        question_routing: dict[str, Any],
        research_task: dict[str, Any] | None = None,
    ) -> StockAnalysisAdaptivePlanningData:
        feedback_items = self.stock_analysis_research_feedback_repository.list_feedbacks(
            user_id=user_id,
            thread_id=thread_id,
            limit=5,
        )
        feedbacks = [item.to_dict() for item in feedback_items]
        compare_helpful_count = sum(
            1 for item in feedbacks if bool(item.get("compare_helpful"))
        )
        refresh_helpful_count = sum(
            1 for item in feedbacks if bool(item.get("refresh_helpful"))
        )
        tooling_helpful_count = sum(
            1 for item in feedbacks if bool(item.get("tooling_helpful"))
        )
        validation_helpful_count = sum(
            1 for item in feedbacks if bool(item.get("validation_helpful"))
        )
        over_researched_count = sum(
            1
            for item in feedbacks
            if _clean_text(item.get("process_quality_status")) == "over_researched"
        )
        under_evidenced_count = sum(
            1
            for item in feedbacks
            if _clean_text(item.get("process_quality_status")) == "under_evidenced"
        )
        stale_context_count = sum(
            1
            for item in context_cards
            if bool(item.get("is_stale")) or bool(item.get("refresh_recommended"))
        )
        compare_target_count = len(list(thread.get("compare_targets_json") or []))
        high_priority_tasks = [
            item for item in open_tasks if _clean_text(item.get("priority")) == "high"
        ]
        task_types = [_clean_text(item.get("task_type")) for item in open_tasks]
        question_intent = _clean_text(question_routing.get("question_intent"))

        prefer_compare_first = compare_helpful_count > refresh_helpful_count and (
            compare_target_count >= 2
            or "compare_followup" in task_types
            or question_intent == "compare_targets"
        )
        prefer_refresh_first = (
            refresh_helpful_count >= max(compare_helpful_count, 1)
            and stale_context_count > 0
        ) or (
            research_task is not None
            and _clean_text(research_task.get("task_type")) == "refresh_needed"
        ) or (
            "refresh_needed" in task_types and question_intent in {"refresh_state_check", "update_thesis"}
        )
        prefer_internal_first = (
            tooling_helpful_count == 0
            or tooling_helpful_count <= max(compare_helpful_count, refresh_helpful_count)
        ) or under_evidenced_count > 0
        prefer_external_confirmation = (
            tooling_helpful_count >= 2
            and question_intent in {
                "external_evidence_check",
                "challenge_conclusion",
                "update_thesis",
            }
        ) or (
            research_task is not None
            and _clean_text(research_task.get("task_type")) == "tooling_check"
        )
        avoid_over_research = over_researched_count >= 2

        planning_profile = "balanced"
        if avoid_over_research:
            planning_profile = "lightweight_research"
        elif prefer_refresh_first:
            planning_profile = "refresh_first"
        elif prefer_compare_first:
            planning_profile = "compare_first"
        elif prefer_external_confirmation:
            planning_profile = "external_confirm_first"
        elif prefer_internal_first:
            planning_profile = "internal_first"
        if planning_profile not in PLANNING_PROFILES:
            planning_profile = "balanced"

        preferred_order = self._build_preferred_evidence_order(
            prefer_compare_first=prefer_compare_first,
            prefer_refresh_first=prefer_refresh_first,
            prefer_internal_first=prefer_internal_first,
            prefer_external_confirmation=prefer_external_confirmation,
            avoid_over_research=avoid_over_research,
            active_memory=active_memory,
            active_compression=active_compression,
        )
        preferred_first_action = self._resolve_preferred_first_action(
            preferred_order=preferred_order,
            planning_profile=planning_profile,
        )
        planning_adjustments = self._build_planning_adjustments(
            planning_profile=planning_profile,
            prefer_compare_first=prefer_compare_first,
            prefer_refresh_first=prefer_refresh_first,
            prefer_external_confirmation=prefer_external_confirmation,
            avoid_over_research=avoid_over_research,
            stale_context_count=stale_context_count,
            high_priority_tasks=high_priority_tasks,
            task_types=task_types,
        )
        feedback_signals_used = _unique_str_list(
            [
                *(["compare_helpful"] if compare_helpful_count else []),
                *(["refresh_helpful"] if refresh_helpful_count else []),
                *(["tooling_helpful"] if tooling_helpful_count else []),
                *(["validation_helpful"] if validation_helpful_count else []),
                *(["over_researched"] if over_researched_count else []),
                *(["under_evidenced"] if under_evidenced_count else []),
                *(["stale_contexts"] if stale_context_count else []),
                *(["high_priority_tasks"] if high_priority_tasks else []),
            ]
        )
        adjustment_reasoning = self._build_adjustment_reasoning(
            planning_profile=planning_profile,
            question_intent=question_intent,
            compare_helpful_count=compare_helpful_count,
            refresh_helpful_count=refresh_helpful_count,
            tooling_helpful_count=tooling_helpful_count,
            over_researched_count=over_researched_count,
            under_evidenced_count=under_evidenced_count,
            stale_context_count=stale_context_count,
            high_priority_tasks=high_priority_tasks,
        )
        confidence_hint = self._build_confidence_hint(
            feedback_count=len(feedbacks),
            feedback_signals_used=feedback_signals_used,
            planning_profile=planning_profile,
        )

        preferences = StockAnalysisPlanningPreferenceData(
            planning_profile=planning_profile,
            feedback_window_size=len(feedbacks),
            feedback_signals_used=feedback_signals_used,
            preferred_first_action=preferred_first_action,
            preferred_evidence_order=preferred_order,
            prefer_compare_first=prefer_compare_first,
            prefer_refresh_first=prefer_refresh_first,
            prefer_internal_first=prefer_internal_first,
            prefer_external_confirmation=prefer_external_confirmation,
            avoid_over_research=avoid_over_research,
            planning_adjustments=planning_adjustments,
            adjustment_reasoning=adjustment_reasoning,
            confidence_hint=confidence_hint,
        )
        return StockAnalysisAdaptivePlanningData(
            **preferences.model_dump(),
            preferences=preferences,
        )

    @staticmethod
    def _build_preferred_evidence_order(
        *,
        prefer_compare_first: bool,
        prefer_refresh_first: bool,
        prefer_internal_first: bool,
        prefer_external_confirmation: bool,
        avoid_over_research: bool,
        active_memory: dict[str, Any] | None,
        active_compression: dict[str, Any] | None,
    ) -> list[str]:
        order = [
            "explicit_context",
            "compare_targets" if prefer_compare_first else "",
            "refresh" if prefer_refresh_first else "",
            "active_memory" if active_memory else "",
            "active_compression" if active_compression else "",
            "internal_structured" if prefer_internal_first or not prefer_external_confirmation else "",
            "market_price",
            "external_confirmation" if prefer_external_confirmation and not avoid_over_research else "",
            "validation",
        ]
        # Ensure fallback order still contains compare / refresh when not preferred but relevant.
        order.extend(
            [
                "compare_targets" if not prefer_compare_first else "",
                "refresh" if not prefer_refresh_first else "",
                "internal_structured" if not prefer_internal_first else "",
                "external_confirmation"
                if not prefer_external_confirmation and not avoid_over_research
                else "",
            ]
        )
        return _unique_str_list(order)

    @staticmethod
    def _resolve_preferred_first_action(
        *,
        preferred_order: Sequence[str],
        planning_profile: str,
    ) -> str:
        if planning_profile == "lightweight_research":
            return "explicit_context"
        for item in preferred_order:
            if item != "explicit_context":
                return item
        return "explicit_context"

    @staticmethod
    def _build_planning_adjustments(
        *,
        planning_profile: str,
        prefer_compare_first: bool,
        prefer_refresh_first: bool,
        prefer_external_confirmation: bool,
        avoid_over_research: bool,
        stale_context_count: int,
        high_priority_tasks: Sequence[dict[str, Any]],
        task_types: Sequence[str],
    ) -> list[str]:
        adjustments: list[str] = []
        if planning_profile == "lightweight_research":
            adjustments.append("本轮尽量减少不必要的外部补数，避免 over-research。")
        if prefer_refresh_first and stale_context_count:
            adjustments.append("当前 stale context 较多，先 refresh 再强化结论。")
        if prefer_compare_first:
            adjustments.append("最近 compare 回看更有效，本轮优先明确比较轴。")
        if prefer_external_confirmation:
            adjustments.append("当前问题更像确认型研究，外部确认会被提前考虑。")
        if high_priority_tasks:
            adjustments.append(
                f"存在 {len(high_priority_tasks)} 条高优先级 task，会显式影响执行顺序。"
            )
        if "thesis_validation" in task_types:
            adjustments.append("validation 相关任务仍在 open，本轮不适合跳过 thesis recheck。")
        if avoid_over_research:
            adjustments.append("若已有足够支持证据，将尽早停止继续扩展 provider。")
        return _unique_str_list(adjustments)

    @staticmethod
    def _build_adjustment_reasoning(
        *,
        planning_profile: str,
        question_intent: str,
        compare_helpful_count: int,
        refresh_helpful_count: int,
        tooling_helpful_count: int,
        over_researched_count: int,
        under_evidenced_count: int,
        stale_context_count: int,
        high_priority_tasks: Sequence[dict[str, Any]],
    ) -> str:
        parts = [
            f"当前问题语义为 {question_intent or 'general_followup'}，规划画像收口为 {planning_profile}。"
        ]
        if compare_helpful_count:
            parts.append(f"最近 feedback 中 compare_helpful 出现 {compare_helpful_count} 次。")
        if refresh_helpful_count:
            parts.append(f"最近 feedback 中 refresh_helpful 出现 {refresh_helpful_count} 次。")
        if tooling_helpful_count:
            parts.append(f"最近 feedback 中 tooling_helpful 出现 {tooling_helpful_count} 次。")
        if stale_context_count:
            parts.append(f"线程当前仍有 {stale_context_count} 个 stale / refresh recommended contexts。")
        if over_researched_count:
            parts.append(f"最近 feedback 有 {over_researched_count} 次提示过度研究。")
        if under_evidenced_count:
            parts.append(f"最近 feedback 有 {under_evidenced_count} 次提示证据不足。")
        if high_priority_tasks:
            parts.append("线程内高优先级任务会直接影响执行优先级。")
        return " ".join(parts)

    @staticmethod
    def _build_confidence_hint(
        *,
        feedback_count: int,
        feedback_signals_used: Sequence[str],
        planning_profile: str,
    ) -> str:
        if feedback_count <= 1:
            return "历史 feedback 样本较少，本轮 planning bias 采用保守偏置。"
        if len(feedback_signals_used) <= 1:
            return "历史反馈信号较单一，本轮仍以当前问题语义和上下文状态为主。"
        if planning_profile == "lightweight_research":
            return "最近存在 over-researched 信号，本轮优先保持轻量、可解释的研究路径。"
        return "最近 feedback 信号较一致，本轮 planning 会显式吸收这些偏好。"


_stock_analysis_adaptive_planning_service: Optional[
    StockAnalysisAdaptivePlanningService
] = None


def get_stock_analysis_adaptive_planning_service() -> (
    StockAnalysisAdaptivePlanningService
):
    global _stock_analysis_adaptive_planning_service
    if _stock_analysis_adaptive_planning_service is None:
        _stock_analysis_adaptive_planning_service = (
            StockAnalysisAdaptivePlanningService()
        )
    return _stock_analysis_adaptive_planning_service


def reset_stock_analysis_adaptive_planning_service() -> None:
    global _stock_analysis_adaptive_planning_service
    _stock_analysis_adaptive_planning_service = None
