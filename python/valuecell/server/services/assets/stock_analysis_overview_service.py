from __future__ import annotations

import datetime as dt
from typing import Any, Optional, Sequence

from .stock_analysis_adaptive_planning_service import (
    StockAnalysisAdaptivePlanningService,
    get_stock_analysis_adaptive_planning_service,
)
from .stock_analysis_compare_service import (
    StockAnalysisCompareService,
    get_stock_analysis_compare_service,
)
from .stock_analysis_message_service import (
    StockAnalysisMessageService,
    get_stock_analysis_message_service,
)
from .stock_analysis_research_feedback_service import (
    StockAnalysisResearchFeedbackService,
    get_stock_analysis_research_feedback_service,
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
from .stock_analysis_workspace_service import (
    DEFAULT_USER_ID,
    StockAnalysisWorkspaceService,
)


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def _clean_text(value: Any, *, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def _parse_datetime(value: Any) -> dt.datetime:
    text = _clean_text(value)
    if not text:
        return _utcnow()
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(normalized)
    except ValueError:
        return _utcnow()
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt.UTC)
    return parsed


def _is_assistant_role(value: Any) -> bool:
    role = _clean_text(value).lower()
    return role in {"assistant", "agent"}


def _clamp_score(value: int) -> int:
    return max(0, min(100, value))


class StockAnalysisOverviewService:
    def __init__(
        self,
        stock_analysis_workspace_service: Optional[StockAnalysisWorkspaceService] = None,
        stock_analysis_research_task_service: Optional[
            StockAnalysisResearchTaskService
        ] = None,
        stock_analysis_thread_memory_service: Optional[
            StockAnalysisThreadMemoryService
        ] = None,
        stock_analysis_thread_compression_service: Optional[
            StockAnalysisThreadCompressionService
        ] = None,
        stock_analysis_research_feedback_service: Optional[
            StockAnalysisResearchFeedbackService
        ] = None,
        stock_analysis_adaptive_planning_service: Optional[
            StockAnalysisAdaptivePlanningService
        ] = None,
        stock_analysis_message_service: Optional[StockAnalysisMessageService] = None,
        stock_analysis_compare_service: Optional[StockAnalysisCompareService] = None,
    ) -> None:
        self.stock_analysis_workspace_service = (
            stock_analysis_workspace_service or StockAnalysisWorkspaceService()
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
        self.stock_analysis_research_feedback_service = (
            stock_analysis_research_feedback_service
            or get_stock_analysis_research_feedback_service()
        )
        self.stock_analysis_adaptive_planning_service = (
            stock_analysis_adaptive_planning_service
            or get_stock_analysis_adaptive_planning_service()
        )
        self.stock_analysis_message_service = (
            stock_analysis_message_service or get_stock_analysis_message_service()
        )
        self.stock_analysis_compare_service = (
            stock_analysis_compare_service or get_stock_analysis_compare_service()
        )

    async def get_overview(self, *, user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
        threads_result = await self.stock_analysis_workspace_service.list_threads(
            user_id=user_id
        )
        thread_items = list((threads_result or {}).get("items") or [])
        if not thread_items:
            return {
                "generated_at": _utcnow().isoformat(),
                "available": False,
                "summary": "当前还没有股票研究线程。",
                "thread_overview_items": [],
                "high_priority_tasks": [],
                "high_conflict_threads": [],
                "refresh_needed_threads": [],
                "research_quality_summary": self._empty_research_quality_summary(),
                "planning_profile_summary": self._empty_planning_profile_summary(),
                "recent_feedback_summary": self._empty_recent_feedback_summary(),
                "action_queue": [],
                "empty_message": "先创建一个股票研究线程，再从总览进入研究工作台。",
            }

        overview_items: list[dict[str, Any]] = []
        all_high_priority_tasks: list[dict[str, Any]] = []
        all_action_queue: list[dict[str, Any]] = []
        research_quality_summary = self._empty_research_quality_summary()
        planning_profile_summary = self._empty_planning_profile_summary()
        recent_feedback_summary = self._empty_recent_feedback_summary()

        for thread in thread_items:
            thread_id = int(thread.get("thread_id") or 0)
            if thread_id <= 0:
                continue
            contexts_result = await self.stock_analysis_workspace_service.list_context_cards(
                user_id=user_id,
                thread_id=thread_id,
            )
            context_items = list((contexts_result or {}).get("items") or [])
            compare_result = await self.stock_analysis_compare_service.list_compare_targets(
                user_id=user_id,
                thread_id=thread_id,
            )
            task_result = await self.stock_analysis_research_task_service.list_tasks(
                user_id=user_id,
                thread_id=thread_id,
            )
            task_items = list((task_result or {}).get("items") or [])
            open_tasks = [
                item for item in task_items if _clean_text(item.get("status")) == "open"
            ]
            memory_result = await self.stock_analysis_thread_memory_service.list_memories(
                user_id=user_id,
                thread_id=thread_id,
            )
            compression_result = (
                await self.stock_analysis_thread_compression_service.list_compressions(
                    user_id=user_id,
                    thread_id=thread_id,
                )
            )
            feedback_result = await self.stock_analysis_research_feedback_service.list_feedbacks(
                user_id=user_id,
                thread_id=thread_id,
            )
            message_result = await self.stock_analysis_message_service.list_messages(
                user_id=user_id,
                thread_id=thread_id,
            )
            latest_feedback = (feedback_result or {}).get("latest_feedback")
            latest_assistant_message = self._select_latest_assistant_message(
                list((message_result or {}).get("items") or [])
            )
            adaptive_planning = self.stock_analysis_adaptive_planning_service.build_adaptive_planning(
                user_id=user_id,
                thread_id=thread_id,
                thread=thread,
                context_cards=context_items,
                active_memory=(memory_result or {}).get("active_memory"),
                active_compression=(compression_result or {}).get("active_compression"),
                open_tasks=open_tasks,
                question_routing={
                    "question_intent": _clean_text(
                        (latest_assistant_message or {}).get("question_intent"),
                        fallback="general_followup",
                    ),
                    "response_strategy": _clean_text(
                        (latest_assistant_message or {}).get("response_strategy"),
                        fallback="answer_from_context",
                    ),
                },
                research_task=None,
            )
            item = self._build_thread_overview_item(
                thread=thread,
                context_items=context_items,
                compare_result=compare_result or {},
                task_items=task_items,
                open_tasks=open_tasks,
                active_memory=(memory_result or {}).get("active_memory"),
                compression_result=compression_result or {},
                latest_feedback=latest_feedback,
                latest_assistant_message=latest_assistant_message,
                adaptive_planning=adaptive_planning.model_dump(),
            )
            overview_items.append(item)
            all_high_priority_tasks.extend(
                self._build_high_priority_tasks(
                    thread=item,
                    open_tasks=open_tasks,
                )
            )
            all_action_queue.extend(
                self._build_action_queue_items(
                    thread_item=item,
                    open_tasks=open_tasks,
                )
            )
            self._accumulate_research_quality_summary(
                summary=research_quality_summary,
                latest_feedback=latest_feedback,
            )
            self._accumulate_planning_profile_summary(
                summary=planning_profile_summary,
                planning_profile=item.get("latest_planning_profile"),
            )
            self._accumulate_recent_feedback_summary(
                summary=recent_feedback_summary,
                thread_item=item,
                latest_feedback=latest_feedback,
            )

        overview_items.sort(
            key=lambda item: (
                self._thread_health_priority(item.get("thread_health_status")),
                -int(item.get("thread_health_score") or 0),
                -_parse_datetime(item.get("updated_at")).timestamp(),
            )
        )
        all_high_priority_tasks.sort(
            key=lambda item: (
                0 if _clean_text(item.get("priority")) == "high" else 1,
                item.get("thread_title") or "",
                item.get("title") or "",
            )
        )
        all_action_queue.sort(
            key=lambda item: (
                self._action_priority(item.get("priority")),
                0 if _clean_text(item.get("kind")) == "review_high_conflict" else 1,
                item.get("thread_id") or 0,
            )
        )
        all_action_queue = self._dedupe_action_queue(all_action_queue)
        high_conflict_threads = [
            item
            for item in overview_items
            if item.get("thread_health_status") == "high_conflict"
            or item.get("latest_conflict_level") == "high"
        ][:5]
        refresh_needed_threads = [
            item
            for item in overview_items
            if item.get("thread_health_status") == "needs_refresh"
            or int(item.get("stale_context_count") or 0) > 0
            or int(item.get("refresh_recommended_count") or 0) > 0
        ][:5]
        summary = self._build_overview_summary(
            thread_count=len(overview_items),
            action_queue_count=len(all_action_queue),
            high_conflict_count=len(high_conflict_threads),
            refresh_needed_count=len(refresh_needed_threads),
        )
        return {
            "generated_at": _utcnow().isoformat(),
            "available": True,
            "summary": summary,
            "thread_overview_items": overview_items,
            "high_priority_tasks": all_high_priority_tasks[:8],
            "high_conflict_threads": high_conflict_threads,
            "refresh_needed_threads": refresh_needed_threads,
            "research_quality_summary": research_quality_summary,
            "planning_profile_summary": planning_profile_summary,
            "recent_feedback_summary": recent_feedback_summary,
            "action_queue": all_action_queue[:12],
            "empty_message": None,
        }

    @staticmethod
    def _select_latest_assistant_message(
        items: Sequence[dict[str, Any]],
    ) -> dict[str, Any] | None:
        for item in reversed(list(items)):
            if _is_assistant_role(item.get("role")):
                return item
        return None

    def _build_thread_overview_item(
        self,
        *,
        thread: dict[str, Any],
        context_items: Sequence[dict[str, Any]],
        compare_result: dict[str, Any],
        task_items: Sequence[dict[str, Any]],
        open_tasks: Sequence[dict[str, Any]],
        active_memory: dict[str, Any] | None,
        compression_result: dict[str, Any],
        latest_feedback: dict[str, Any] | None,
        latest_assistant_message: dict[str, Any] | None,
        adaptive_planning: dict[str, Any],
    ) -> dict[str, Any]:
        stale_context_count = sum(
            1 for item in context_items if bool(item.get("is_stale"))
        )
        refresh_recommended_count = sum(
            1 for item in context_items if bool(item.get("refresh_recommended"))
        )
        high_priority_tasks = [
            item for item in open_tasks if _clean_text(item.get("priority")) == "high"
        ]
        latest_conflict_level = _clean_text(
            (latest_assistant_message or {})
            .get("evidence_conflict_summary", {})
            .get("conflict_level")
        ) or None
        latest_validation_status = _clean_text(
            (latest_assistant_message or {})
            .get("validation_summary", {})
            .get("thesis_status")
        ) or None
        latest_planning_profile = (
            _clean_text((latest_assistant_message or {}).get("adaptive_planning_profile"))
            or _clean_text(adaptive_planning.get("planning_profile"))
            or None
        )
        health_status, health_score, health_reason = self._build_thread_health(
            stale_context_count=stale_context_count,
            refresh_recommended_count=refresh_recommended_count,
            latest_conflict_level=latest_conflict_level,
            high_priority_task_count=len(high_priority_tasks),
            latest_process_quality_status=_clean_text(
                (latest_feedback or {}).get("process_quality_status")
            )
            or None,
            active_memory_available=active_memory is not None,
            active_compression_available=bool(
                (compression_result or {}).get("active_compression")
            ),
            latest_validation_status=latest_validation_status,
        )
        next_best_action, next_best_action_reason = self._build_next_best_action(
            health_status=health_status,
            latest_conflict_level=latest_conflict_level,
            stale_context_count=stale_context_count,
            refresh_recommended_count=refresh_recommended_count,
            high_priority_tasks=high_priority_tasks,
            latest_feedback=latest_feedback,
            latest_validation_status=latest_validation_status,
        )
        headline_summary = self._build_headline_summary(
            thread=thread,
            latest_feedback=latest_feedback,
            latest_conflict_level=latest_conflict_level,
            high_priority_task_count=len(high_priority_tasks),
            stale_context_count=stale_context_count,
        )
        return {
            "thread_id": int(thread.get("thread_id") or 0),
            "title": _clean_text(thread.get("title"), fallback="未命名线程"),
            "focus_type": _clean_text(thread.get("focus_type"), fallback="general"),
            "updated_at": _parse_datetime(thread.get("updated_at")).isoformat(),
            "context_count": len(context_items),
            "compare_target_count": len(list(compare_result.get("compare_targets") or [])),
            "open_task_count": len(open_tasks),
            "high_priority_task_count": len(high_priority_tasks),
            "active_memory_available": active_memory is not None,
            "active_compression_available": bool(
                (compression_result or {}).get("active_compression")
            ),
            "refresh_recommended_count": refresh_recommended_count,
            "stale_context_count": stale_context_count,
            "latest_planning_profile": latest_planning_profile,
            "latest_conflict_level": latest_conflict_level,
            "latest_validation_status": latest_validation_status,
            "latest_feedback_alignment_status": _clean_text(
                (latest_feedback or {}).get("outcome_alignment_status")
            )
            or None,
            "latest_process_quality_status": _clean_text(
                (latest_feedback or {}).get("process_quality_status")
            )
            or None,
            "thread_health_status": health_status,
            "thread_health_score": health_score,
            "thread_health_reason": health_reason,
            "headline_summary": headline_summary,
            "next_best_action": next_best_action,
            "next_best_action_reason": next_best_action_reason,
        }

    @staticmethod
    def _build_thread_health(
        *,
        stale_context_count: int,
        refresh_recommended_count: int,
        latest_conflict_level: str | None,
        high_priority_task_count: int,
        latest_process_quality_status: str | None,
        active_memory_available: bool,
        active_compression_available: bool,
        latest_validation_status: str | None,
    ) -> tuple[str, int, str]:
        score = 100
        reasons: list[str] = []
        if stale_context_count:
            score -= min(25, stale_context_count * 10)
            reasons.append(f"{stale_context_count} 张 context 已 stale。")
        if refresh_recommended_count:
            score -= min(15, refresh_recommended_count * 5)
            reasons.append(f"{refresh_recommended_count} 张 context 建议 refresh。")
        if latest_conflict_level == "high":
            score -= 30
            reasons.append("最近 evidence conflict 为 high。")
        elif latest_conflict_level == "medium":
            score -= 15
            reasons.append("最近 evidence conflict 为 medium。")
        if high_priority_task_count:
            score -= min(20, high_priority_task_count * 10)
            reasons.append(f"{high_priority_task_count} 条高优先级任务待处理。")
        if latest_process_quality_status == "under_evidenced":
            score -= 15
            reasons.append("最近反馈提示证据不足。")
        elif latest_process_quality_status == "over_researched":
            score -= 10
            reasons.append("最近反馈提示研究偏重。")
        if not active_memory_available:
            score -= 5
            reasons.append("当前缺少 active memory。")
        if not active_compression_available:
            score -= 5
            reasons.append("当前缺少 active compression。")
        if latest_validation_status == "thesis_recheck_needed":
            score -= 12
            reasons.append("最近 validation 仍需重审 thesis。")
        score = _clamp_score(score)
        if latest_conflict_level == "high":
            return ("high_conflict", score, " ".join(reasons) or "证据冲突较高。")
        if stale_context_count or refresh_recommended_count:
            return ("needs_refresh", score, " ".join(reasons) or "需要先 refresh。")
        if high_priority_task_count or latest_validation_status == "thesis_recheck_needed":
            return ("follow_up_required", score, " ".join(reasons) or "需要后续跟进。")
        if score < 75:
            return ("watch", score, " ".join(reasons) or "建议继续观察。")
        return ("healthy", score, "当前线程结构较完整，适合继续研究。")

    @staticmethod
    def _build_next_best_action(
        *,
        health_status: str,
        latest_conflict_level: str | None,
        stale_context_count: int,
        refresh_recommended_count: int,
        high_priority_tasks: Sequence[dict[str, Any]],
        latest_feedback: dict[str, Any] | None,
        latest_validation_status: str | None,
    ) -> tuple[str, str]:
        if health_status == "high_conflict" or latest_conflict_level == "high":
            return (
                "review_high_conflict",
                "当前支持与反对证据冲突较高，先回到线程里看 conflict summary。",
            )
        if stale_context_count or refresh_recommended_count:
            return (
                "refresh_thread",
                "当前上下文已有 stale / refresh recommended 信号，先 refresh 再强化结论更稳。",
            )
        if high_priority_tasks:
            first_task = high_priority_tasks[0]
            return (
                "follow_up_task",
                f"当前高优先级任务 #{int(first_task.get('task_id') or 0)} 仍在 open，应先处理。",
            )
        if latest_validation_status == "thesis_recheck_needed":
            return (
                "recheck_thesis",
                "最近 validation 仍提示 thesis 需要重审，不宜直接延续旧结论。",
            )
        if _clean_text((latest_feedback or {}).get("process_quality_status")) == "effective":
            return (
                "continue_effective_thread",
                "最近反馈显示该线程研究方式较有效，可优先继续跟进。",
            )
        return ("continue_effective_thread", "当前线程结构较完整，可作为优先继续研究候选。")

    @staticmethod
    def _build_headline_summary(
        *,
        thread: dict[str, Any],
        latest_feedback: dict[str, Any] | None,
        latest_conflict_level: str | None,
        high_priority_task_count: int,
        stale_context_count: int,
    ) -> str:
        parts = [_clean_text(thread.get("title"), fallback="该线程")]
        if latest_feedback:
            parts.append(
                f"最近反馈为 {_clean_text(latest_feedback.get('outcome_alignment_status'), fallback='unclear')} / "
                f"{_clean_text(latest_feedback.get('process_quality_status'), fallback='mixed')}"
            )
        if latest_conflict_level:
            parts.append(f"当前 conflict {latest_conflict_level}")
        if stale_context_count:
            parts.append(f"{stale_context_count} 张 stale context")
        if high_priority_task_count:
            parts.append(f"{high_priority_task_count} 条高优先级 task")
        return "，".join(parts) + "。"

    @staticmethod
    def _build_high_priority_tasks(
        *,
        thread: dict[str, Any],
        open_tasks: Sequence[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for task in open_tasks:
            if _clean_text(task.get("priority")) != "high":
                continue
            result.append(
                {
                    "task_id": int(task.get("task_id") or 0),
                    "thread_id": int(thread.get("thread_id") or 0),
                    "thread_title": _clean_text(thread.get("title")),
                    "title": _clean_text(task.get("title")),
                    "summary": _clean_text(task.get("summary")),
                    "priority": _clean_text(task.get("priority"), fallback="high"),
                    "status": _clean_text(task.get("status"), fallback="open"),
                    "task_type": _clean_text(task.get("task_type"), fallback="general"),
                    "suggested_action": thread.get("next_best_action"),
                    "reason": thread.get("next_best_action_reason"),
                }
            )
        return result

    @staticmethod
    def _build_action_queue_items(
        *,
        thread_item: dict[str, Any],
        open_tasks: Sequence[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        kind = _clean_text(thread_item.get("next_best_action"))
        if kind:
            priority = "medium"
            if kind in {
                "review_high_conflict",
                "refresh_thread",
                "follow_up_task",
                "recheck_thesis",
            }:
                priority = "high"
            items.append(
                {
                    "kind": kind,
                    "thread_id": int(thread_item.get("thread_id") or 0),
                    "title": _clean_text(thread_item.get("title")),
                    "summary": _clean_text(thread_item.get("headline_summary")),
                    "priority": priority,
                    "reason": _clean_text(thread_item.get("next_best_action_reason")),
                    "suggested_action": kind,
                    "target_ref": f"thread:{int(thread_item.get('thread_id') or 0)}",
                }
            )
        for task in open_tasks:
            if _clean_text(task.get("priority")) != "high":
                continue
            items.append(
                {
                    "kind": "follow_up_task",
                    "thread_id": int(thread_item.get("thread_id") or 0),
                    "title": _clean_text(task.get("title")),
                    "summary": _clean_text(task.get("summary")),
                    "priority": "high",
                    "reason": f"高优先级 task 仍为 open，类型 { _clean_text(task.get('task_type')) }。",
                    "suggested_action": "回到线程处理该 task",
                    "target_ref": f"task:{int(task.get('task_id') or 0)}",
                }
            )
        return items

    @staticmethod
    def _dedupe_action_queue(
        items: Sequence[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        deduped: list[dict[str, Any]] = []
        seen: set[tuple[str, int, str]] = set()
        for item in items:
            dedupe_key = (
                _clean_text(item.get("kind")),
                int(item.get("thread_id") or 0),
                _clean_text(item.get("target_ref")),
            )
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            deduped.append(item)
        return deduped

    @staticmethod
    def _accumulate_research_quality_summary(
        *,
        summary: dict[str, Any],
        latest_feedback: dict[str, Any] | None,
    ) -> None:
        if not latest_feedback:
            return
        process_status = _clean_text(latest_feedback.get("process_quality_status"))
        alignment_status = _clean_text(latest_feedback.get("outcome_alignment_status"))
        process_key = f"{process_status}_count"
        alignment_key = f"{alignment_status}_count"
        if process_key in summary:
            summary[process_key] += 1
        if alignment_key in summary:
            summary[alignment_key] += 1

    @staticmethod
    def _accumulate_planning_profile_summary(
        *,
        summary: dict[str, Any],
        planning_profile: str | None,
    ) -> None:
        if not planning_profile:
            return
        key = f"{planning_profile}_count"
        if key in summary:
            summary[key] += 1

    @staticmethod
    def _accumulate_recent_feedback_summary(
        *,
        summary: dict[str, Any],
        thread_item: dict[str, Any],
        latest_feedback: dict[str, Any] | None,
    ) -> None:
        if latest_feedback:
            summary["total_feedback_count"] += 1
            alignment_status = _clean_text(latest_feedback.get("outcome_alignment_status"))
            if alignment_status:
                summary["latest_alignment_statuses"].append(alignment_status)
        if _clean_text(thread_item.get("latest_process_quality_status")) == "effective":
            summary["effective_thread_count"] += 1
        if _clean_text(thread_item.get("latest_conflict_level")) == "high":
            summary["high_conflict_thread_count"] += 1
        if _clean_text(thread_item.get("thread_health_status")) == "needs_refresh":
            summary["needs_refresh_thread_count"] += 1
        if _clean_text(thread_item.get("thread_health_status")) == "follow_up_required":
            summary["follow_up_required_thread_count"] += 1

    @staticmethod
    def _build_overview_summary(
        *,
        thread_count: int,
        action_queue_count: int,
        high_conflict_count: int,
        refresh_needed_count: int,
    ) -> str:
        return (
            f"当前共 {thread_count} 条研究线程，"
            f"其中 {high_conflict_count} 条高冲突、{refresh_needed_count} 条需 refresh，"
            f"action queue 中有 {action_queue_count} 项建议优先处理。"
        )

    @staticmethod
    def _thread_health_priority(status: Any) -> int:
        mapping = {
            "high_conflict": 0,
            "needs_refresh": 1,
            "follow_up_required": 2,
            "watch": 3,
            "healthy": 4,
        }
        return mapping.get(_clean_text(status), 5)

    @staticmethod
    def _action_priority(priority: Any) -> int:
        mapping = {"high": 0, "medium": 1, "low": 2}
        return mapping.get(_clean_text(priority), 3)

    @staticmethod
    def _empty_research_quality_summary() -> dict[str, Any]:
        return {
            "effective_count": 0,
            "mixed_count": 0,
            "under_evidenced_count": 0,
            "over_researched_count": 0,
            "confirmed_count": 0,
            "partially_confirmed_count": 0,
            "unclear_count": 0,
            "contradicted_count": 0,
        }

    @staticmethod
    def _empty_planning_profile_summary() -> dict[str, Any]:
        return {
            "balanced_count": 0,
            "refresh_first_count": 0,
            "compare_first_count": 0,
            "internal_first_count": 0,
            "external_confirm_first_count": 0,
            "lightweight_research_count": 0,
        }

    @staticmethod
    def _empty_recent_feedback_summary() -> dict[str, Any]:
        return {
            "total_feedback_count": 0,
            "effective_thread_count": 0,
            "high_conflict_thread_count": 0,
            "needs_refresh_thread_count": 0,
            "follow_up_required_thread_count": 0,
            "latest_alignment_statuses": [],
        }


_stock_analysis_overview_service: Optional[StockAnalysisOverviewService] = None


def get_stock_analysis_overview_service() -> StockAnalysisOverviewService:
    global _stock_analysis_overview_service
    if _stock_analysis_overview_service is None:
        _stock_analysis_overview_service = StockAnalysisOverviewService()
    return _stock_analysis_overview_service


def reset_stock_analysis_overview_service() -> None:
    global _stock_analysis_overview_service
    _stock_analysis_overview_service = None
