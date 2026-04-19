from __future__ import annotations

import datetime as dt
from typing import Any, Optional, Sequence

from ...db.repositories.stock_analysis_research_feedback_repository import (
    StockAnalysisResearchFeedbackRepository,
)
from .decision_effectiveness_service import DecisionEffectivenessService
from .decision_outcome_review_service import DecisionOutcomeReviewService
from .risk_sizing_service import RiskSizingService
from .stock_analysis_message_service import (
    StockAnalysisMessageService,
    get_stock_analysis_message_service,
)
from .stock_analysis_research_task_service import (
    StockAnalysisResearchTaskService,
    get_stock_analysis_research_task_service,
)
from .stock_analysis_thread_compression_service import (
    StockAnalysisThreadCompressionService,
    get_stock_analysis_thread_compression_service,
)
from .stock_analysis_thread_memory_service import (
    StockAnalysisThreadMemoryService,
    get_stock_analysis_thread_memory_service,
)
from .stock_analysis_workspace_service import StockAnalysisWorkspaceService

OUTCOME_ALIGNMENT_STATUSES = {
    "confirmed",
    "partially_confirmed",
    "unclear",
    "contradicted",
}
PROCESS_QUALITY_STATUSES = {
    "effective",
    "mixed",
    "under_evidenced",
    "over_researched",
}
TRACKING_SUGGESTIONS = {
    "keep_tracking",
    "convert_to_refresh_check",
    "reopen_for_research",
}


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


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


def _unique_int_list(values: Sequence[Any]) -> list[int]:
    result: list[int] = []
    for value in values:
        try:
            normalized = int(value)
        except (TypeError, ValueError):
            continue
        if normalized > 0 and normalized not in result:
            result.append(normalized)
    return result


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    return text in {"1", "true", "yes"}


def _is_assistant_role(value: Any) -> bool:
    role = str(value or "").strip().lower()
    return role in {"assistant", "agent"}


def _get_step_types(message: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for item in list(message.get("executed_steps") or []):
        step_type = _clean_text((item or {}).get("step_type"))
        if step_type:
            result.add(step_type)
    return result


class StockAnalysisResearchFeedbackService:
    def __init__(
        self,
        stock_analysis_workspace_service: Optional[StockAnalysisWorkspaceService] = None,
        stock_analysis_research_feedback_repository: Optional[
            StockAnalysisResearchFeedbackRepository
        ] = None,
        stock_analysis_message_service: Optional[StockAnalysisMessageService] = None,
        stock_analysis_research_task_service: Optional[
            StockAnalysisResearchTaskService
        ] = None,
        stock_analysis_thread_memory_service: Optional[
            StockAnalysisThreadMemoryService
        ] = None,
        stock_analysis_thread_compression_service: Optional[
            StockAnalysisThreadCompressionService
        ] = None,
        decision_outcome_review_service: Optional[DecisionOutcomeReviewService] = None,
        decision_effectiveness_service: Optional[DecisionEffectivenessService] = None,
        risk_sizing_service: Optional[RiskSizingService] = None,
    ) -> None:
        self.stock_analysis_workspace_service = (
            stock_analysis_workspace_service or StockAnalysisWorkspaceService()
        )
        self.stock_analysis_research_feedback_repository = (
            stock_analysis_research_feedback_repository
            or StockAnalysisResearchFeedbackRepository()
        )
        self.stock_analysis_message_service = (
            stock_analysis_message_service or get_stock_analysis_message_service()
        )
        self.stock_analysis_research_task_service = (
            stock_analysis_research_task_service
            or get_stock_analysis_research_task_service()
        )
        self.stock_analysis_thread_memory_service = (
            stock_analysis_thread_memory_service
            or get_stock_analysis_thread_memory_service()
        )
        self.stock_analysis_thread_compression_service = (
            stock_analysis_thread_compression_service
            or get_stock_analysis_thread_compression_service()
        )
        self.decision_outcome_review_service = (
            decision_outcome_review_service or DecisionOutcomeReviewService()
        )
        self.decision_effectiveness_service = (
            decision_effectiveness_service or DecisionEffectivenessService()
        )
        self.risk_sizing_service = risk_sizing_service or RiskSizingService()

    async def list_feedbacks(
        self,
        *,
        user_id: str,
        thread_id: int,
    ) -> dict[str, Any] | None:
        thread = self.stock_analysis_workspace_service.stock_analysis_thread_repository.get_thread_by_id(
            user_id=user_id,
            thread_id=thread_id,
        )
        if thread is None:
            return None
        items = self.stock_analysis_research_feedback_repository.list_feedbacks(
            user_id=user_id,
            thread_id=thread_id,
        )
        serialized = self._serialize_feedbacks(items)
        return {
            "thread_id": thread_id,
            "items": serialized,
            "latest_feedback": serialized[0] if serialized else None,
            "count": len(serialized),
            "generated_at": _utcnow().isoformat(),
        }

    async def get_feedback(
        self,
        *,
        user_id: str,
        thread_id: int,
        feedback_id: int,
    ) -> dict[str, Any] | None:
        feedback = self.stock_analysis_research_feedback_repository.get_feedback_by_id(
            user_id=user_id,
            thread_id=thread_id,
            feedback_id=feedback_id,
        )
        if feedback is None:
            return None
        items = self.stock_analysis_research_feedback_repository.list_feedbacks(
            user_id=user_id,
            thread_id=thread_id,
        )
        serialized = self._serialize_feedbacks(items)
        return next(
            (
                item
                for item in serialized
                if int(item.get("feedback_id") or 0) == feedback_id
            ),
            None,
        )

    async def capture_feedback(
        self,
        *,
        user_id: str,
        thread_id: int,
        anchor_message_id: str | None = None,
        related_task_ids: Sequence[int] | None = None,
        related_tickers: Sequence[str] | None = None,
        title: str | None = None,
        note: str | None = None,
    ) -> dict[str, Any] | None:
        return await self._create_feedback_snapshot(
            user_id=user_id,
            thread_id=thread_id,
            anchor_message_id=anchor_message_id,
            related_task_ids=related_task_ids or [],
            related_tickers=related_tickers or [],
            title_override=title,
            note=note,
        )

    async def refresh_feedback(
        self,
        *,
        user_id: str,
        thread_id: int,
        feedback_id: int,
        title: str | None = None,
        note: str | None = None,
        related_task_ids: Sequence[int] | None = None,
        related_tickers: Sequence[str] | None = None,
    ) -> dict[str, Any] | None:
        seed_feedback = await self.get_feedback(
            user_id=user_id,
            thread_id=thread_id,
            feedback_id=feedback_id,
        )
        if seed_feedback is None:
            return None
        return await self._create_feedback_snapshot(
            user_id=user_id,
            thread_id=thread_id,
            anchor_message_id=str(seed_feedback.get("anchor_message_id") or ""),
            related_task_ids=related_task_ids
            or list(seed_feedback.get("linked_task_ids_json") or []),
            related_tickers=related_tickers
            or list(seed_feedback.get("linked_tickers_json") or []),
            title_override=title or str(seed_feedback.get("title") or "").strip(),
            note=note or str(seed_feedback.get("detail_note") or "").strip(),
        )

    async def _create_feedback_snapshot(
        self,
        *,
        user_id: str,
        thread_id: int,
        anchor_message_id: str | None,
        related_task_ids: Sequence[int],
        related_tickers: Sequence[str],
        title_override: str | None,
        note: str | None,
    ) -> dict[str, Any] | None:
        thread_obj = self.stock_analysis_workspace_service.stock_analysis_thread_repository.get_thread_by_id(
            user_id=user_id,
            thread_id=thread_id,
        )
        if thread_obj is None:
            return None
        thread = self.stock_analysis_workspace_service._serialize_thread(thread_obj)
        context_result = await self.stock_analysis_workspace_service.list_context_cards(
            user_id=user_id,
            thread_id=thread_id,
        )
        context_cards = list((context_result or {}).get("items") or [])
        messages_result = await self.stock_analysis_message_service.list_messages(
            user_id=user_id,
            thread_id=thread_id,
        )
        messages = list((messages_result or {}).get("items") or [])
        anchor_message = self._select_anchor_message(
            messages=messages,
            anchor_message_id=anchor_message_id,
        )
        if anchor_message is None:
            raise ValueError("No eligible assistant research message found")
        task_result = await self.stock_analysis_research_task_service.list_tasks(
            user_id=user_id,
            thread_id=thread_id,
        )
        all_tasks = list((task_result or {}).get("items") or [])
        related_tasks = self._select_related_tasks(
            all_tasks=all_tasks,
            anchor_message=anchor_message,
            related_task_ids=related_task_ids,
        )
        linked_memory = await self._load_linked_memory(
            user_id=user_id,
            thread_id=thread_id,
            anchor_message=anchor_message,
            related_tasks=related_tasks,
        )
        linked_compression = await self._load_linked_compression(
            user_id=user_id,
            thread_id=thread_id,
            anchor_message=anchor_message,
            related_tasks=related_tasks,
        )
        linkage = self._build_linkage(
            thread=thread,
            context_cards=context_cards,
            anchor_message=anchor_message,
            related_tasks=related_tasks,
            linked_memory=linked_memory,
            linked_compression=linked_compression,
            related_tickers=related_tickers,
        )
        matched_reviews = self._load_matched_reviews(
            user_id=user_id,
            linked_tickers=linkage["linked_tickers_json"],
        )
        outcome_alignment_status = self._resolve_outcome_alignment_status(
            matched_reviews=matched_reviews,
        )
        effectiveness_snapshot = self._build_effectiveness_snapshot(
            user_id=user_id,
            linked_tickers=linkage["linked_tickers_json"],
        )
        risk_sizing_snapshot = self._build_risk_sizing_snapshot(
            user_id=user_id,
            linked_tickers=linkage["linked_tickers_json"],
        )
        attribution = self._build_attribution(
            anchor_message=anchor_message,
            linkage=linkage,
            related_tasks=related_tasks,
            matched_reviews=matched_reviews,
            linked_memory=linked_memory,
            linked_compression=linked_compression,
            outcome_alignment_status=outcome_alignment_status,
        )
        payload = {
            "thread_id": thread_id,
            "user_id": user_id,
            "anchor_message_id": str(anchor_message.get("item_id") or ""),
            "title": self._build_title(
                title_override=title_override,
                anchor_message=anchor_message,
                linkage=linkage,
            ),
            "anchor_question_intent": _clean_text(
                anchor_message.get("question_intent")
            )
            or None,
            "anchor_response_strategy": _clean_text(
                anchor_message.get("response_strategy")
            )
            or None,
            "anchor_mode": _clean_text(anchor_message.get("mode")) or None,
            "anchor_plan_summary": _clean_text(
                anchor_message.get("execution_plan_summary")
            )
            or None,
            "anchor_validation_status": _clean_text(
                (anchor_message.get("validation_summary") or {}).get("thesis_status")
            )
            or None,
            **linkage,
            "linked_outcome_review_ids_json": [
                int(item.get("review_id") or 0)
                for item in matched_reviews
                if int(item.get("review_id") or 0) > 0
            ],
            "linked_effectiveness_snapshot_json": effectiveness_snapshot,
            "linked_risk_sizing_snapshot_json": risk_sizing_snapshot,
            "outcome_alignment_status": outcome_alignment_status,
            "process_quality_status": attribution["process_quality_status"],
            "compare_helpful": attribution["compare_helpful"],
            "refresh_helpful": attribution["refresh_helpful"],
            "tooling_helpful": attribution["tooling_helpful"],
            "validation_helpful": attribution["validation_helpful"],
            "what_helped_json": attribution["what_helped_json"],
            "what_hurt_json": attribution["what_hurt_json"],
            "process_adjustments_json": attribution["process_adjustments_json"],
            "task_followup_suggestions_json": attribution[
                "task_followup_suggestions_json"
            ],
            "summary": self._build_summary(
                outcome_alignment_status=outcome_alignment_status,
                process_quality_status=attribution["process_quality_status"],
                attribution=attribution,
            ),
            "detail_note": self._build_detail_note(
                note=note,
                outcome_alignment_status=outcome_alignment_status,
                process_quality_status=attribution["process_quality_status"],
                matched_reviews=matched_reviews,
            ),
        }
        saved = self.stock_analysis_research_feedback_repository.create_feedback(payload)
        if saved is None:
            return None
        return await self.get_feedback(
            user_id=user_id,
            thread_id=thread_id,
            feedback_id=int(saved.id),
        )

    def _serialize_feedbacks(self, items: Sequence[Any]) -> list[dict[str, Any]]:
        serialized = [item.to_dict() for item in items]
        chronological_ids = [
            int(item.get("feedback_id") or 0)
            for item in reversed(serialized)
            if int(item.get("feedback_id") or 0) > 0
        ]
        version_map = {
            feedback_id: index + 1 for index, feedback_id in enumerate(chronological_ids)
        }
        for item in serialized:
            item["version"] = version_map.get(int(item.get("feedback_id") or 0), 1)
        return serialized

    def _select_anchor_message(
        self,
        *,
        messages: Sequence[dict[str, Any]],
        anchor_message_id: str | None,
    ) -> dict[str, Any] | None:
        if anchor_message_id:
            for item in messages:
                if str(item.get("item_id") or "") != str(anchor_message_id):
                    continue
                if _is_assistant_role(item.get("role")):
                    return item
            raise ValueError("Anchor message not found or not an assistant message")
        for item in reversed(list(messages)):
            if not _is_assistant_role(item.get("role")):
                continue
            if _clean_text(item.get("question_intent")) or _clean_text(
                item.get("execution_plan_summary")
            ):
                return item
            if item.get("validation_summary"):
                return item
        return None

    def _select_related_tasks(
        self,
        *,
        all_tasks: Sequence[dict[str, Any]],
        anchor_message: dict[str, Any],
        related_task_ids: Sequence[int],
    ) -> list[dict[str, Any]]:
        explicit_ids = _unique_int_list(related_task_ids)
        if not explicit_ids:
            explicit_ids = _unique_int_list(anchor_message.get("related_task_ids") or [])
        if not explicit_ids:
            return []
        task_map = {
            int(item.get("task_id") or 0): item
            for item in all_tasks
            if int(item.get("task_id") or 0) > 0
        }
        return [task_map[task_id] for task_id in explicit_ids if task_id in task_map]

    async def _load_linked_memory(
        self,
        *,
        user_id: str,
        thread_id: int,
        anchor_message: dict[str, Any],
        related_tasks: Sequence[dict[str, Any]],
    ) -> dict[str, Any] | None:
        memory_id = int(anchor_message.get("active_memory_id") or 0)
        if memory_id <= 0:
            memory_id = next(
                (
                    int(item.get("related_memory_id") or 0)
                    for item in related_tasks
                    if int(item.get("related_memory_id") or 0) > 0
                ),
                0,
            )
        if memory_id <= 0:
            return None
        return await self.stock_analysis_thread_memory_service.get_memory(
            user_id=user_id,
            thread_id=thread_id,
            memory_id=memory_id,
        )

    async def _load_linked_compression(
        self,
        *,
        user_id: str,
        thread_id: int,
        anchor_message: dict[str, Any],
        related_tasks: Sequence[dict[str, Any]],
    ) -> dict[str, Any] | None:
        compression_id = int(anchor_message.get("active_compression_id") or 0)
        if compression_id <= 0:
            compression_id = next(
                (
                    int(item.get("related_compression_id") or 0)
                    for item in related_tasks
                    if int(item.get("related_compression_id") or 0) > 0
                ),
                0,
            )
        if compression_id <= 0:
            return None
        return await self.stock_analysis_thread_compression_service.get_compression(
            user_id=user_id,
            thread_id=thread_id,
            compression_id=compression_id,
        )

    def _build_linkage(
        self,
        *,
        thread: dict[str, Any],
        context_cards: Sequence[dict[str, Any]],
        anchor_message: dict[str, Any],
        related_tasks: Sequence[dict[str, Any]],
        linked_memory: dict[str, Any] | None,
        linked_compression: dict[str, Any] | None,
        related_tickers: Sequence[str],
    ) -> dict[str, Any]:
        linked_context_ids = _unique_int_list(
            list(anchor_message.get("used_context_ids") or [])
            + list(anchor_message.get("refreshed_context_ids") or [])
            + list(anchor_message.get("stale_context_ids") or [])
            + list(anchor_message.get("refresh_recommended_context_ids") or [])
            + [
                context.get("context_id")
                for context in context_cards
                if context.get("source_ref")
                and context.get("source_ref")
                in {
                    target.get("source_ref")
                    for target in list(thread.get("compare_targets_json") or [])
                }
            ]
            + [
                item
                for task in related_tasks
                for item in list(task.get("related_context_ids_json") or [])
            ]
            + list((linked_memory or {}).get("linked_context_ids_json") or [])
        )
        compare_targets = list(thread.get("compare_targets_json") or [])
        compare_tickers, compare_themes = self._split_compare_targets(compare_targets)
        linked_tickers = _unique_str_list(
            list(related_tickers)
            + list(anchor_message.get("focus_tickers") or [])
            + list(anchor_message.get("compared_tickers") or [])
            + list(thread.get("ticker_refs_json") or [])
            + compare_tickers
            + [
                item
                for task in related_tasks
                for item in list(task.get("related_tickers_json") or [])
            ]
            + list((linked_memory or {}).get("focus_tickers_json") or [])
            + list((linked_memory or {}).get("compared_tickers_json") or [])
            + list((linked_compression or {}).get("focus_tickers_json") or [])
            + list((linked_compression or {}).get("compared_tickers_json") or [])
        )
        linked_themes = _unique_str_list(
            list(anchor_message.get("focus_themes") or [])
            + list(thread.get("theme_refs_json") or [])
            + compare_themes
            + [
                item
                for task in related_tasks
                for item in list(task.get("related_themes_json") or [])
            ]
            + list((linked_memory or {}).get("focus_themes_json") or [])
            + list((linked_compression or {}).get("focus_themes_json") or [])
        )
        return {
            "linked_task_ids_json": _unique_int_list(
                [item.get("task_id") for item in related_tasks]
            ),
            "linked_context_ids_json": linked_context_ids,
            "linked_memory_id": int((linked_memory or {}).get("memory_id") or 0) or None,
            "linked_compression_id": int(
                (linked_compression or {}).get("compression_id") or 0
            )
            or None,
            "linked_compare_targets_json": compare_targets,
            "linked_tickers_json": linked_tickers,
            "linked_themes_json": linked_themes,
        }

    @staticmethod
    def _split_compare_targets(
        compare_targets: Sequence[dict[str, Any]],
    ) -> tuple[list[str], list[str]]:
        tickers: list[str] = []
        themes: list[str] = []
        for item in compare_targets:
            ref = _clean_text(item.get("ref"))
            target_type = _clean_text(item.get("target_type"))
            if not ref:
                continue
            if target_type == "ticker":
                tickers.append(ref)
            elif target_type == "theme":
                themes.append(ref)
        return (_unique_str_list(tickers), _unique_str_list(themes))

    def _load_matched_reviews(
        self,
        *,
        user_id: str,
        linked_tickers: Sequence[str],
    ) -> list[dict[str, Any]]:
        if not linked_tickers:
            return []
        reviews = self.decision_outcome_review_service.list_reviews(
            user_id=user_id,
            limit=120,
        ).get("items") or []
        matched = [
            item
            for item in reviews
            if _clean_text(item.get("ticker")) in set(linked_tickers)
        ]
        matched.sort(
            key=lambda item: (
                str(item.get("review_date") or ""),
                int(item.get("outcome_score") or 0),
                int(item.get("review_id") or 0),
            ),
            reverse=True,
        )
        return matched[:20]

    def _resolve_outcome_alignment_status(
        self,
        *,
        matched_reviews: Sequence[dict[str, Any]],
    ) -> str:
        if not matched_reviews:
            return "unclear"
        statuses = [_clean_text(item.get("outcome_status")) for item in matched_reviews]
        effective = statuses.count("有效")
        partial = statuses.count("部分有效")
        failed = statuses.count("失效")
        observing = statuses.count("仍在观察")
        if effective > 0 and failed == 0 and partial == 0 and observing == 0:
            return "confirmed"
        if failed > 0 and effective == 0 and partial == 0:
            return "contradicted"
        if effective > 0 or partial > 0:
            return "partially_confirmed"
        return "unclear"

    def _build_effectiveness_snapshot(
        self,
        *,
        user_id: str,
        linked_tickers: Sequence[str],
    ) -> dict[str, Any]:
        summary = self.decision_effectiveness_service.get_summary(user_id=user_id)
        recent_successes = [
            item
            for item in list(summary.get("recent_successes") or [])
            if _clean_text(item.get("ticker")) in set(linked_tickers)
        ]
        recent_failures = [
            item
            for item in list(summary.get("recent_failures") or [])
            if _clean_text(item.get("ticker")) in set(linked_tickers)
        ]
        return {
            "available": bool(summary.get("available")),
            "overall_score": int(summary.get("overall_score") or 0),
            "overall_summary": _clean_text(summary.get("overall_summary")),
            "review_count": int(summary.get("review_count") or 0),
            "matched_successes": recent_successes[:3],
            "matched_failures": recent_failures[:3],
        }

    def _build_risk_sizing_snapshot(
        self,
        *,
        user_id: str,
        linked_tickers: Sequence[str],
    ) -> dict[str, Any]:
        summary = self.risk_sizing_service.get_summary(user_id=user_id)
        ticker_suggestions = []
        if summary.get("available"):
            known_map = {
                _clean_text(item.get("ticker")): item
                for item in list(summary.get("ticker_suggestions") or [])
                if _clean_text(item.get("ticker"))
            }
            for ticker in linked_tickers[:3]:
                if ticker in known_map:
                    ticker_suggestions.append(known_map[ticker])
                    continue
                try:
                    detail = self.risk_sizing_service.get_ticker_summary(
                        user_id=user_id,
                        ticker=ticker,
                    )
                except Exception:
                    continue
                if detail.get("available"):
                    ticker_suggestions.append(detail)
        return {
            "available": bool(summary.get("available")),
            "market_risk_level": _clean_text(summary.get("market_risk_level")),
            "suggested_total_exposure_range": _clean_text(
                summary.get("suggested_total_exposure_range")
            ),
            "suggested_new_position_range": _clean_text(
                summary.get("suggested_new_position_range")
            ),
            "suggested_add_position_range": _clean_text(
                summary.get("suggested_add_position_range")
            ),
            "holding_risk_note": _clean_text(summary.get("holding_risk_note")),
            "entry_risk_note": _clean_text(summary.get("entry_risk_note")),
            "ticker_suggestions": ticker_suggestions[:3],
        }

    def _build_attribution(
        self,
        *,
        anchor_message: dict[str, Any],
        linkage: dict[str, Any],
        related_tasks: Sequence[dict[str, Any]],
        matched_reviews: Sequence[dict[str, Any]],
        linked_memory: dict[str, Any] | None,
        linked_compression: dict[str, Any] | None,
        outcome_alignment_status: str,
    ) -> dict[str, Any]:
        step_types = _get_step_types(anchor_message)
        compare_signal = bool(anchor_message.get("comparison_mode")) or (
            len(list(linkage.get("linked_compare_targets_json") or [])) >= 2
        )
        refresh_signal = bool(anchor_message.get("refreshed_before_answer")) or (
            "refresh_stale_contexts" in step_types
        )
        tooling_signal = bool(anchor_message.get("tool_calls_summary")) or bool(
            anchor_message.get("temporary_evidence_blocks")
        ) or any(step.startswith("collect_") for step in step_types)
        validation_signal = bool(anchor_message.get("validation_summary")) or (
            "validate_thesis" in step_types
        )

        what_helped: list[str] = []
        what_hurt: list[str] = []
        adjustments: list[str] = []

        compare_helpful = compare_signal and outcome_alignment_status in {
            "confirmed",
            "partially_confirmed",
        }
        if compare_helpful:
            what_helped.append("对比对象较明确，降低了单票主观判断带来的偏差。")
        elif len(list(linkage.get("linked_tickers_json") or [])) <= 1:
            what_hurt.append("比较对象不足，结论更依赖单点假设。")
            adjustments.append("下次先补一个中军或主线核心票，再进入 compare。")

        refresh_helpful = refresh_signal and (
            outcome_alignment_status != "contradicted"
            or bool(anchor_message.get("refresh_changed_contexts"))
        )
        if refresh_helpful:
            what_helped.append("refresh 帮助回到较新的前提，降低旧 context 干扰。")
        elif list(anchor_message.get("stale_context_ids") or []) or list(
            anchor_message.get("refresh_recommended_context_ids") or []
        ):
            what_hurt.append("当时存在 stale context，但没有先完成 refresh。")
            adjustments.append("下次先 refresh 关键卡片，再比较和验证 thesis。")

        tooling_helpful = tooling_signal and outcome_alignment_status in {
            "confirmed",
            "partially_confirmed",
        }
        if tooling_helpful:
            what_helped.append("tooling 和外部证据补充了新的确认，而不是只重复旧上下文。")
        elif tooling_signal:
            what_hurt.append("tooling 有补充，但目前仍缺少足够结果反馈来验证价值。")
            adjustments.append("外部证据偏弱时，优先回到内部结构化上下文再补证据。")

        validation_status = _clean_text(
            (anchor_message.get("validation_summary") or {}).get("thesis_status")
        )
        validation_helpful = validation_signal and validation_status in {
            "thesis_improved",
            "thesis_recheck_needed",
            "thesis_weakened",
        }
        if validation_helpful:
            what_helped.append("validation 迫使结论显式收口，便于后续结果回看。")
        elif validation_signal:
            what_hurt.append("validation 更多是重复确认，新增信息有限。")
            adjustments.append("先补最缺的数据或任务，再做 validation 会更有效。")

        if linked_memory and _bool(anchor_message.get("used_active_memory")):
            what_helped.append("active memory 帮助维持 thesis 连贯性，减少重复推导。")
        if linked_compression and _bool(anchor_message.get("used_active_compression")):
            what_helped.append("active compression 保留了历史脉络，减少长线程噪音。")

        open_related_tasks = [
            item for item in related_tasks if _clean_text(item.get("status")) == "open"
        ]
        if open_related_tasks:
            what_hurt.append("相关研究任务尚未闭环，部分依据仍需继续跟踪。")
            adjustments.append("把未闭环任务转成持续跟踪或 refresh check，避免一次性结案。")

        if not matched_reviews:
            what_hurt.append("后续结果样本不足，当前只能给保守回看结论。")

        process_quality_status = self._resolve_process_quality_status(
            outcome_alignment_status=outcome_alignment_status,
            helpful_count=sum(
                int(value)
                for value in (
                    compare_helpful,
                    refresh_helpful,
                    tooling_helpful,
                    validation_helpful,
                )
            ),
            hurt_count=len(what_hurt),
            signal_count=sum(
                int(value)
                for value in (
                    compare_signal,
                    refresh_signal,
                    tooling_signal,
                    validation_signal,
                )
            ),
            matched_review_count=len(matched_reviews),
            open_task_count=len(open_related_tasks),
        )
        task_followup_suggestions = self._build_task_followup_suggestions(
            related_tasks=related_tasks,
            outcome_alignment_status=outcome_alignment_status,
            process_quality_status=process_quality_status,
        )
        return {
            "compare_helpful": compare_helpful,
            "refresh_helpful": refresh_helpful,
            "tooling_helpful": tooling_helpful,
            "validation_helpful": validation_helpful,
            "what_helped_json": _unique_str_list(what_helped),
            "what_hurt_json": _unique_str_list(what_hurt),
            "process_adjustments_json": _unique_str_list(adjustments),
            "task_followup_suggestions_json": task_followup_suggestions,
            "process_quality_status": process_quality_status,
        }

    def _resolve_process_quality_status(
        self,
        *,
        outcome_alignment_status: str,
        helpful_count: int,
        hurt_count: int,
        signal_count: int,
        matched_review_count: int,
        open_task_count: int,
    ) -> str:
        if matched_review_count == 0 and helpful_count <= 1:
            return "under_evidenced"
        if (
            signal_count >= 3
            and outcome_alignment_status == "unclear"
            and open_task_count >= 2
        ):
            return "over_researched"
        if outcome_alignment_status == "confirmed" and helpful_count >= 1 and hurt_count <= 1:
            return "effective"
        return "mixed"

    def _build_task_followup_suggestions(
        self,
        *,
        related_tasks: Sequence[dict[str, Any]],
        outcome_alignment_status: str,
        process_quality_status: str,
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for task in related_tasks:
            task_id = int(task.get("task_id") or 0)
            if task_id <= 0:
                continue
            status = _clean_text(task.get("status"))
            suggestion = "keep_tracking"
            reason = "当前仍建议保留该任务，避免研究链路过早中断。"
            if outcome_alignment_status == "confirmed" and status == "open":
                suggestion = "close_after_confirmation"
                reason = "后续结果已基本支持该轮研究，可在补一轮确认后考虑关闭。"
            elif outcome_alignment_status == "unclear" and _clean_text(task.get("task_type")) in {
                "refresh_needed",
                "compression_recheck",
                "memory_recheck",
                "risk_recheck",
            }:
                suggestion = "convert_to_refresh_check"
                reason = "当前更适合保留为 refresh check，而不是直接结束。"
            elif outcome_alignment_status == "contradicted" and status in {
                "completed",
                "dismissed",
            }:
                suggestion = "reopen_for_research"
                reason = "结果与原结论不一致，建议重开并补新的验证依据。"
            elif process_quality_status == "under_evidenced":
                suggestion = "keep_tracking"
                reason = "当前证据仍偏薄，建议继续跟踪而不是直接结案。"
            result.append(
                {
                    "task_id": task_id,
                    "title": _clean_text(task.get("title")),
                    "current_status": status,
                    "suggestion": suggestion,
                    "reason": reason,
                }
            )
        return result

    def _build_title(
        self,
        *,
        title_override: str | None,
        anchor_message: dict[str, Any],
        linkage: dict[str, Any],
    ) -> str:
        if _clean_text(title_override):
            return _clean_text(title_override)
        if linkage.get("linked_tickers_json"):
            first_ticker = list(linkage.get("linked_tickers_json") or [])[0]
            return f"{first_ticker} 研究反馈"
        intent = _clean_text(anchor_message.get("question_intent"))
        if intent:
            return f"{intent} 研究反馈"
        return "线程研究反馈"

    def _build_summary(
        self,
        *,
        outcome_alignment_status: str,
        process_quality_status: str,
        attribution: dict[str, Any],
    ) -> str:
        helped = list(attribution.get("what_helped_json") or [])
        hurt = list(attribution.get("what_hurt_json") or [])
        helped_text = helped[0] if helped else "当前还没有明确证明哪条研究路径最有效"
        hurt_text = hurt[0] if hurt else "当前没有明显噪音路径"
        return (
            f"结果回看为 {outcome_alignment_status}，过程评价为 {process_quality_status}；"
            f"主要帮助因素：{helped_text}；主要拖累因素：{hurt_text}。"
        )

    def _build_detail_note(
        self,
        *,
        note: str | None,
        outcome_alignment_status: str,
        process_quality_status: str,
        matched_reviews: Sequence[dict[str, Any]],
    ) -> str | None:
        review_summary = ""
        if matched_reviews:
            latest = matched_reviews[0]
            review_summary = _clean_text(latest.get("summary"))
        parts = [
            _clean_text(note),
            (
                f"本次 refresh 重新读取了 outcome / effectiveness / risk / tasks，"
                f"当前结论为 {outcome_alignment_status} / {process_quality_status}。"
            ),
            review_summary,
        ]
        merged = [item for item in parts if item]
        return "\n\n".join(merged) if merged else None


_stock_analysis_research_feedback_service: Optional[
    StockAnalysisResearchFeedbackService
] = None


def get_stock_analysis_research_feedback_service() -> (
    StockAnalysisResearchFeedbackService
):
    global _stock_analysis_research_feedback_service
    if _stock_analysis_research_feedback_service is None:
        _stock_analysis_research_feedback_service = (
            StockAnalysisResearchFeedbackService()
        )
    return _stock_analysis_research_feedback_service


def reset_stock_analysis_research_feedback_service() -> None:
    global _stock_analysis_research_feedback_service
    _stock_analysis_research_feedback_service = None
