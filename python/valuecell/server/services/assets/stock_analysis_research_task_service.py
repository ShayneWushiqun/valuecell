from __future__ import annotations

import datetime as dt
import json
from typing import Any, Optional, Sequence

from valuecell.core.types import NotifyResponseEvent
from valuecell.server.services.conversation_service import ConversationService

from ...db.repositories.stock_analysis_research_task_repository import (
    StockAnalysisResearchTaskRepository,
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

VALID_TASK_TYPES = {
    "compare_followup",
    "refresh_needed",
    "tooling_check",
    "memory_recheck",
    "compression_recheck",
    "risk_recheck",
    "next_question",
    "thesis_validation",
}
VALID_STATUSES = {"open", "completed", "dismissed"}
VALID_PRIORITIES = {"high", "medium", "low"}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


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
            parsed = int(value)
        except (TypeError, ValueError):
            continue
        if parsed > 0 and parsed not in result:
            result.append(parsed)
    return result


class StockAnalysisResearchTaskService:
    def __init__(
        self,
        stock_analysis_workspace_service: Optional[StockAnalysisWorkspaceService] = None,
        stock_analysis_research_task_repository: Optional[
            StockAnalysisResearchTaskRepository
        ] = None,
        stock_analysis_thread_memory_service: Optional[
            StockAnalysisThreadMemoryService
        ] = None,
        stock_analysis_thread_compression_service: Optional[
            StockAnalysisThreadCompressionService
        ] = None,
        conversation_service: Optional[ConversationService] = None,
    ) -> None:
        self.stock_analysis_workspace_service = (
            stock_analysis_workspace_service or StockAnalysisWorkspaceService()
        )
        self.stock_analysis_research_task_repository = (
            stock_analysis_research_task_repository
            or StockAnalysisResearchTaskRepository()
        )
        self.stock_analysis_thread_memory_service = (
            stock_analysis_thread_memory_service
            or get_stock_analysis_thread_memory_service()
        )
        self.stock_analysis_thread_compression_service = (
            stock_analysis_thread_compression_service
            or get_stock_analysis_thread_compression_service()
        )
        self.conversation_service = conversation_service or ConversationService()

    async def list_tasks(
        self,
        *,
        user_id: str,
        thread_id: int,
    ) -> dict[str, Any] | None:
        thread_obj = self.stock_analysis_workspace_service.stock_analysis_thread_repository.get_thread_by_id(
            user_id=user_id,
            thread_id=thread_id,
        )
        if thread_obj is None:
            return None
        context_result = await self.stock_analysis_workspace_service.list_context_cards(
            user_id=user_id,
            thread_id=thread_id,
        )
        context_cards = list((context_result or {}).get("items") or [])
        compression_state = await self.stock_analysis_thread_compression_service.get_prompt_context_state(
            user_id=user_id,
            thread_id=thread_id,
        )
        items = self.stock_analysis_research_task_repository.list_tasks(
            user_id=user_id,
            thread_id=thread_id,
        )
        serialized = self._serialize_tasks(items)
        open_items = [item for item in serialized if item["status"] == "open"]
        generated_items = [
            item for item in serialized if _clean_text(item.get("source_kind")) != "manual"
        ]
        last_generated_at = (
            generated_items[0]["created_at"] if generated_items else None
        )
        stale_count = sum(
            1
            for item in context_cards
            if bool(item.get("is_stale")) or bool(item.get("refresh_recommended"))
        )
        has_actionable_gap = bool(
            stale_count
            or any(item["priority"] == "high" for item in open_items)
            or compression_state["compression_recommended"]
        )
        actionable_gap_summary = self._build_actionable_gap_summary(
            stale_count=stale_count,
            open_items=open_items,
            compression_state=compression_state,
        )
        return {
            "thread_id": thread_id,
            "items": serialized,
            "count": len(serialized),
            "open_count": len(open_items),
            "high_priority_open_count": sum(
                1 for item in open_items if item["priority"] == "high"
            ),
            "last_generated_at": last_generated_at,
            "has_actionable_gap": has_actionable_gap,
            "actionable_gap_summary": actionable_gap_summary,
            "generated_at": _utcnow().isoformat(),
        }

    async def get_task(
        self,
        *,
        user_id: str,
        thread_id: int,
        task_id: int,
    ) -> dict[str, Any] | None:
        item = self.stock_analysis_research_task_repository.get_task_by_id(
            user_id=user_id,
            thread_id=thread_id,
            task_id=task_id,
        )
        if item is None:
            return None
        return self._serialize_task(item)

    async def create_task(
        self,
        *,
        user_id: str,
        thread_id: int,
        title: str,
        summary: str = "",
        task_type: str = "next_question",
        priority: str = "medium",
        source_kind: str = "manual",
        source_ref: str | None = None,
        related_tickers_json: Sequence[str] | None = None,
        related_themes_json: Sequence[str] | None = None,
        related_context_ids_json: Sequence[int] | None = None,
        related_memory_id: int | None = None,
        related_compression_id: int | None = None,
        related_message_id: str | None = None,
    ) -> dict[str, Any] | None:
        thread = self.stock_analysis_workspace_service.stock_analysis_thread_repository.get_thread_by_id(
            user_id=user_id,
            thread_id=thread_id,
        )
        if thread is None:
            return None
        payload = self._normalize_task_payload(
            thread_id=thread_id,
            user_id=user_id,
            title=title,
            summary=summary,
            task_type=task_type,
            priority=priority,
            source_kind=source_kind,
            source_ref=source_ref,
            related_tickers_json=related_tickers_json or [],
            related_themes_json=related_themes_json or [],
            related_context_ids_json=related_context_ids_json or [],
            related_memory_id=related_memory_id,
            related_compression_id=related_compression_id,
            related_message_id=related_message_id,
        )
        updated = self._upsert_open_task(payload=payload)
        if updated is not None:
            return updated
        created = self.stock_analysis_research_task_repository.create_task(payload)
        if created is None:
            return None
        return self._serialize_task(created)

    async def generate_tasks(
        self,
        *,
        user_id: str,
        thread_id: int,
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
        active_memory = await self.stock_analysis_thread_memory_service.get_active_memory(
            user_id=user_id,
            thread_id=thread_id,
        )
        active_compression = await self.stock_analysis_thread_compression_service.get_active_compression(
            user_id=user_id,
            thread_id=thread_id,
        )
        messages = await self._list_thread_messages(
            conversation_id=str(thread.get("conversation_id") or "")
        )
        candidates = self._build_generated_candidates(
            thread=thread,
            context_cards=context_cards,
            active_memory=active_memory,
            active_compression=active_compression,
            messages=messages,
        )
        created_items: list[dict[str, Any]] = []
        updated_count = 0
        for candidate in candidates:
            updated = self._upsert_open_task(payload=candidate)
            if updated is not None:
                updated_count += 1
                created_items.append(updated)
                continue
            created = self.stock_analysis_research_task_repository.create_task(candidate)
            if created is None:
                continue
            created_items.append(self._serialize_task(created))
        created_count = max(len(created_items) - updated_count, 0)
        return {
            "thread_id": thread_id,
            "created_count": created_count,
            "updated_count": updated_count,
            "items": created_items,
            "last_generated_at": _utcnow().isoformat() if created_items else None,
            "summary": (
                f"已生成/更新 {len(created_items)} 条研究任务。"
                if created_items
                else "当前线程暂无新的研究任务可生成。"
            ),
        }

    async def complete_task(
        self,
        *,
        user_id: str,
        thread_id: int,
        task_id: int,
        note: str | None = None,
    ) -> dict[str, Any] | None:
        return await self._update_status(
            user_id=user_id,
            thread_id=thread_id,
            task_id=task_id,
            status="completed",
            note=note,
        )

    async def reopen_task(
        self,
        *,
        user_id: str,
        thread_id: int,
        task_id: int,
    ) -> dict[str, Any] | None:
        item = self.stock_analysis_research_task_repository.update_task(
            user_id=user_id,
            thread_id=thread_id,
            task_id=task_id,
            payload={
                "status": "open",
                "resolution_note": None,
                "dismiss_reason": None,
                "completed_at": None,
                "dismissed_at": None,
                "updated_at": _utcnow(),
            },
        )
        if item is None:
            return None
        return self._serialize_task(item)

    async def dismiss_task(
        self,
        *,
        user_id: str,
        thread_id: int,
        task_id: int,
        note: str | None = None,
    ) -> dict[str, Any] | None:
        return await self._update_status(
            user_id=user_id,
            thread_id=thread_id,
            task_id=task_id,
            status="dismissed",
            note=note,
        )

    async def _update_status(
        self,
        *,
        user_id: str,
        thread_id: int,
        task_id: int,
        status: str,
        note: str | None,
    ) -> dict[str, Any] | None:
        now = _utcnow()
        payload = {
            "status": status,
            "updated_at": now,
            "completed_at": now if status == "completed" else None,
            "dismissed_at": now if status == "dismissed" else None,
            "resolution_note": _clean_text(note) or None if status == "completed" else None,
            "dismiss_reason": _clean_text(note) or None if status == "dismissed" else None,
        }
        item = self.stock_analysis_research_task_repository.update_task(
            user_id=user_id,
            thread_id=thread_id,
            task_id=task_id,
            payload=payload,
        )
        if item is None:
            return None
        return self._serialize_task(item)

    def _build_generated_candidates(
        self,
        *,
        thread: dict[str, Any],
        context_cards: Sequence[dict[str, Any]],
        active_memory: dict[str, Any] | None,
        active_compression: dict[str, Any] | None,
        messages: Sequence[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        compare_targets = list(thread.get("compare_targets_json") or [])
        compare_labels = [
            _clean_text(item.get("label") or item.get("ref")) for item in compare_targets[:2]
        ]
        related_compare_tickers = [
            _clean_text(item.get("ref"))
            for item in compare_targets
            if _clean_text(item.get("target_type")) == "ticker"
        ]
        stale_cards = [
            item
            for item in context_cards
            if bool(item.get("is_stale")) or bool(item.get("refresh_recommended"))
        ]
        latest_assistant = next(
            (item for item in reversed(messages) if self._is_assistant_role(item)),
            None,
        )

        if len(compare_targets) >= 2 and all(compare_labels):
            candidates.append(
                self._normalize_task_payload(
                    thread_id=int(thread.get("thread_id") or 0),
                    user_id=_clean_text(thread.get("user_id"), fallback="default_user"),
                    title=f"补充比较：{compare_labels[0]} vs {compare_labels[1]} 的优先级确认",
                    summary=_clean_text(
                        (active_compression or {}).get("recent_compare_notes_json", [""])[0],
                        fallback="当前线程存在显式 compare targets，建议明确主次、依据和失效条件。",
                    ),
                    task_type="compare_followup",
                    priority="high" if stale_cards else "medium",
                    source_kind="compare",
                    source_ref="compare_targets",
                    related_tickers_json=related_compare_tickers,
                    related_themes_json=[],
                    related_context_ids_json=self._match_context_ids_by_tickers(
                        context_cards=context_cards,
                        tickers=related_compare_tickers,
                    ),
                )
            )

        if stale_cards:
            stale_title = _clean_text(stale_cards[0].get("title"), fallback="关键上下文")
            candidates.append(
                self._normalize_task_payload(
                    thread_id=int(thread.get("thread_id") or 0),
                    user_id=_clean_text(thread.get("user_id"), fallback="default_user"),
                    title=f"刷新 {stale_title} 后重看当前结论",
                    summary="当前线程存在 stale / refresh recommended 上下文，建议刷新后再复核研究结论。",
                    task_type="refresh_needed",
                    priority="high",
                    source_kind="refresh",
                    source_ref="stale_contexts",
                    related_tickers_json=_unique_str_list(
                        ref for item in stale_cards for ref in list(item.get("ticker_refs_json") or [])
                    ),
                    related_themes_json=_unique_str_list(
                        ref for item in stale_cards for ref in list(item.get("theme_refs_json") or [])
                    ),
                    related_context_ids_json=[
                        int(item.get("context_id") or 0)
                        for item in stale_cards
                        if int(item.get("context_id") or 0) > 0
                    ],
                )
            )

        if active_memory:
            for text in list(active_memory.get("key_uncertainties_json") or [])[:2]:
                title = self._to_task_title(text, prefix="复核不确定点")
                candidates.append(
                    self._normalize_task_payload(
                        thread_id=int(thread.get("thread_id") or 0),
                        user_id=_clean_text(thread.get("user_id"), fallback="default_user"),
                        title=title,
                        summary=_clean_text(text, fallback="需要回看当前 thread memory 中的关键不确定点。"),
                        task_type="memory_recheck",
                        priority="medium",
                        source_kind="memory",
                        source_ref="key_uncertainties",
                        related_tickers_json=list(active_memory.get("focus_tickers_json") or []),
                        related_themes_json=list(active_memory.get("focus_themes_json") or []),
                        related_context_ids_json=list(
                            active_memory.get("linked_context_ids_json") or []
                        ),
                        related_memory_id=int(active_memory.get("memory_id") or 0) or None,
                    )
                )
            for text in list(active_memory.get("next_questions_json") or [])[:2]:
                candidates.append(
                    self._normalize_task_payload(
                        thread_id=int(thread.get("thread_id") or 0),
                        user_id=_clean_text(thread.get("user_id"), fallback="default_user"),
                        title=self._to_task_title(text, prefix="继续追问"),
                        summary=_clean_text(text, fallback="来自 active memory 的下一步研究问题。"),
                        task_type="next_question",
                        priority="medium",
                        source_kind="memory",
                        source_ref="next_questions",
                        related_tickers_json=list(active_memory.get("focus_tickers_json") or []),
                        related_themes_json=list(active_memory.get("focus_themes_json") or []),
                        related_context_ids_json=list(
                            active_memory.get("linked_context_ids_json") or []
                        ),
                        related_memory_id=int(active_memory.get("memory_id") or 0) or None,
                    )
                )
            for text in list(active_memory.get("risk_points_json") or [])[:1]:
                candidates.append(
                    self._normalize_task_payload(
                        thread_id=int(thread.get("thread_id") or 0),
                        user_id=_clean_text(thread.get("user_id"), fallback="default_user"),
                        title=self._to_task_title(text, prefix="重看风险点"),
                        summary=_clean_text(text, fallback="来自 active memory 的风险提示。"),
                        task_type="risk_recheck",
                        priority="medium",
                        source_kind="memory",
                        source_ref="risk_points",
                        related_tickers_json=list(active_memory.get("focus_tickers_json") or []),
                        related_themes_json=list(active_memory.get("focus_themes_json") or []),
                        related_context_ids_json=list(
                            active_memory.get("linked_context_ids_json") or []
                        ),
                        related_memory_id=int(active_memory.get("memory_id") or 0) or None,
                    )
                )

        if active_compression:
            for text in list(active_compression.get("open_questions_json") or [])[:2]:
                candidates.append(
                    self._normalize_task_payload(
                        thread_id=int(thread.get("thread_id") or 0),
                        user_id=_clean_text(thread.get("user_id"), fallback="default_user"),
                        title=self._to_task_title(text, prefix="回到未完成问题"),
                        summary=_clean_text(text, fallback="来自 active compression 的未完成问题。"),
                        task_type="compression_recheck",
                        priority="medium",
                        source_kind="compression",
                        source_ref="open_questions",
                        related_tickers_json=list(
                            active_compression.get("focus_tickers_json") or []
                        ),
                        related_themes_json=list(
                            active_compression.get("focus_themes_json") or []
                        ),
                        related_context_ids_json=[],
                        related_compression_id=int(
                            active_compression.get("compression_id") or 0
                        )
                        or None,
                    )
                )
            tooling_notes = list(active_compression.get("recent_tooling_notes_json") or [])
            evidence_notes = list(active_compression.get("recent_evidence_notes_json") or [])
            if tooling_notes or evidence_notes:
                summary = _clean_text(
                    tooling_notes[0] if tooling_notes else evidence_notes[0],
                    fallback="最近一轮回答依赖过 tooling/evidence，建议显式复核。",
                )
                candidates.append(
                    self._normalize_task_payload(
                        thread_id=int(thread.get("thread_id") or 0),
                        user_id=_clean_text(thread.get("user_id"), fallback="default_user"),
                        title="补充最新外部证据并复核当前判断",
                        summary=summary,
                        task_type="tooling_check",
                        priority="medium",
                        source_kind="tooling",
                        source_ref="recent_tooling_or_evidence",
                        related_tickers_json=list(
                            active_compression.get("focus_tickers_json") or []
                        ),
                        related_themes_json=list(
                            active_compression.get("focus_themes_json") or []
                        ),
                        related_context_ids_json=[],
                        related_compression_id=int(
                            active_compression.get("compression_id") or 0
                        )
                        or None,
                    )
                )

        if latest_assistant and _clean_text(latest_assistant.get("question_intent")) in {
            "challenge_conclusion",
            "update_thesis",
        }:
            candidates.append(
                self._normalize_task_payload(
                    thread_id=int(thread.get("thread_id") or 0),
                    user_id=_clean_text(thread.get("user_id"), fallback="default_user"),
                    title="重验当前 thesis 与关键反例",
                    summary=_clean_text(
                        latest_assistant.get("routing_reason"),
                        fallback="最近一轮问题已触发 challenge/update_thesis 路由，建议显式复核当前 thesis。",
                    ),
                    task_type="thesis_validation",
                    priority="high",
                    source_kind="assistant_suggestion",
                    source_ref="routing",
                    related_tickers_json=list(latest_assistant.get("compared_tickers") or []),
                    related_themes_json=[],
                    related_context_ids_json=list(
                        latest_assistant.get("refresh_recommended_context_ids") or []
                    ),
                    related_message_id=_clean_text(latest_assistant.get("item_id")) or None,
                )
            )

        if latest_assistant:
            for title in list(latest_assistant.get("suggested_task_titles") or [])[:2]:
                candidates.append(
                    self._normalize_task_payload(
                        thread_id=int(thread.get("thread_id") or 0),
                        user_id=_clean_text(thread.get("user_id"), fallback="default_user"),
                        title=self._to_task_title(title, prefix="研究任务"),
                        summary=_clean_text(
                            latest_assistant.get("recommended_next_action"),
                            fallback="来自最近 assistant routing 的建议任务。",
                        ),
                        task_type="next_question",
                        priority="medium",
                        source_kind="assistant_suggestion",
                        source_ref="suggested_task_titles",
                        related_tickers_json=list(latest_assistant.get("compared_tickers") or []),
                        related_themes_json=[],
                        related_context_ids_json=list(
                            latest_assistant.get("refresh_recommended_context_ids") or []
                        ),
                        related_message_id=_clean_text(latest_assistant.get("item_id")) or None,
                    )
                )
        return candidates

    async def _list_thread_messages(self, *, conversation_id: str) -> list[dict[str, Any]]:
        if not conversation_id:
            return []
        items = await self.conversation_service.core_conversation_service.get_conversation_items(
            conversation_id=conversation_id,
            limit=24,
        )
        return [
            self._serialize_message_item(item)
            for item in items
            if str(getattr(item, "event", "")) == str(NotifyResponseEvent.MESSAGE)
        ]

    def _upsert_open_task(self, *, payload: dict[str, Any]) -> dict[str, Any] | None:
        open_tasks = self.stock_analysis_research_task_repository.list_tasks(
            user_id=payload["user_id"],
            thread_id=payload["thread_id"],
            status="open",
        )
        title_key = _clean_text(payload["title"]).lower()
        task_type = payload["task_type"]
        for item in open_tasks:
            if _clean_text(item.title).lower() != title_key or item.task_type != task_type:
                continue
            updated = self.stock_analysis_research_task_repository.update_task(
                user_id=payload["user_id"],
                thread_id=payload["thread_id"],
                task_id=int(item.id),
                payload={
                    "summary": payload["summary"],
                    "priority": payload["priority"],
                    "source_kind": payload["source_kind"],
                    "source_ref": payload["source_ref"],
                    "related_tickers_json": payload["related_tickers_json"],
                    "related_themes_json": payload["related_themes_json"],
                    "related_context_ids_json": payload["related_context_ids_json"],
                    "related_memory_id": payload["related_memory_id"],
                    "related_compression_id": payload["related_compression_id"],
                    "related_message_id": payload["related_message_id"],
                    "updated_at": _utcnow(),
                },
            )
            if updated is None:
                return None
            return self._serialize_task(updated)
        return None

    def _normalize_task_payload(
        self,
        *,
        thread_id: int,
        user_id: str,
        title: str,
        summary: str,
        task_type: str,
        priority: str,
        source_kind: str,
        source_ref: str | None,
        related_tickers_json: Sequence[str],
        related_themes_json: Sequence[str],
        related_context_ids_json: Sequence[int],
        related_memory_id: int | None = None,
        related_compression_id: int | None = None,
        related_message_id: str | None = None,
    ) -> dict[str, Any]:
        normalized_task_type = (
            task_type if task_type in VALID_TASK_TYPES else "next_question"
        )
        normalized_priority = priority if priority in VALID_PRIORITIES else "medium"
        return {
            "thread_id": thread_id,
            "user_id": user_id,
            "title": _clean_text(title, fallback="未命名研究任务")[:255],
            "summary": _clean_text(summary)[:2000],
            "task_type": normalized_task_type,
            "status": "open",
            "priority": normalized_priority,
            "source_kind": _clean_text(source_kind, fallback="manual")[:64],
            "source_ref": _clean_text(source_ref)[:255] or None,
            "related_tickers_json": _unique_str_list(related_tickers_json)[:8],
            "related_themes_json": _unique_str_list(related_themes_json)[:8],
            "related_context_ids_json": _unique_int_list(related_context_ids_json)[:12],
            "related_memory_id": related_memory_id,
            "related_compression_id": related_compression_id,
            "related_message_id": _clean_text(related_message_id)[:120] or None,
            "resolution_note": None,
            "dismiss_reason": None,
            "completed_at": None,
            "dismissed_at": None,
        }

    def _serialize_tasks(self, items: Sequence[Any]) -> list[dict[str, Any]]:
        serialized = [self._serialize_task(item) for item in items]
        return sorted(
            serialized,
            key=lambda item: (
                0 if item["status"] == "open" else 1,
                PRIORITY_ORDER.get(item["priority"], 9),
                item["updated_at"],
            ),
        )

    @staticmethod
    def _serialize_task(item: Any) -> dict[str, Any]:
        data = item.to_dict() if hasattr(item, "to_dict") else dict(item or {})
        if _clean_text(data.get("status")) not in VALID_STATUSES:
            data["status"] = "open"
        if _clean_text(data.get("priority")) not in VALID_PRIORITIES:
            data["priority"] = "medium"
        if _clean_text(data.get("task_type")) not in VALID_TASK_TYPES:
            data["task_type"] = "next_question"
        return data

    @staticmethod
    def _build_actionable_gap_summary(
        *,
        stale_count: int,
        open_items: Sequence[dict[str, Any]],
        compression_state: dict[str, Any],
    ) -> str | None:
        parts: list[str] = []
        if stale_count:
            parts.append(f"存在 {stale_count} 张 stale / 建议刷新上下文")
        high_priority = sum(1 for item in open_items if item["priority"] == "high")
        if high_priority:
            parts.append(f"存在 {high_priority} 条高优先级研究任务")
        if compression_state.get("compression_recommended"):
            parts.append("线程对话建议重新压缩")
        return "；".join(parts) if parts else None

    @staticmethod
    def _match_context_ids_by_tickers(
        *,
        context_cards: Sequence[dict[str, Any]],
        tickers: Sequence[str],
    ) -> list[int]:
        ticker_set = {item for item in tickers if _clean_text(item)}
        result: list[int] = []
        for item in context_cards:
            item_tickers = set(list(item.get("ticker_refs_json") or []))
            if ticker_set & item_tickers:
                context_id = int(item.get("context_id") or 0)
                if context_id > 0 and context_id not in result:
                    result.append(context_id)
        return result

    @staticmethod
    def _to_task_title(text: str, *, prefix: str) -> str:
        normalized = _clean_text(text, fallback=prefix)
        if len(normalized) <= 40:
            return normalized
        return f"{prefix}：{normalized[:36]}"

    @staticmethod
    def _parse_json_dict(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        try:
            parsed = json.loads(str(value or "{}"))
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _parse_json_list(value: Any) -> list[Any]:
        if isinstance(value, list):
            return value
        text = _clean_text(value)
        if not text:
            return []
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []

    @staticmethod
    def _is_assistant_role(item: dict[str, Any] | None) -> bool:
        role = _clean_text((item or {}).get("role")).lower()
        return "assistant" in role or "agent" in role

    @classmethod
    def _serialize_message_item(cls, item: Any) -> dict[str, Any]:
        metadata = cls._parse_json_dict(getattr(item, "metadata", "{}"))
        payload = cls._parse_json_dict(getattr(item, "payload", "{}"))
        return {
            "item_id": getattr(item, "item_id", ""),
            "role": str(getattr(item, "role", "")),
            "content": _clean_text(payload.get("content")),
            "compared_tickers": cls._parse_json_list(metadata.get("compared_tickers_json")),
            "refresh_recommended_context_ids": cls._parse_json_list(
                metadata.get("refresh_recommended_context_ids_json")
            ),
            "question_intent": _clean_text(metadata.get("question_intent")),
            "response_strategy": _clean_text(metadata.get("response_strategy")),
            "routing_reason": _clean_text(metadata.get("routing_reason")),
            "recommended_next_action": _clean_text(
                metadata.get("recommended_next_action")
            ),
            "suggested_task_titles": cls._parse_json_list(
                metadata.get("suggested_task_titles_json")
            ),
            "refresh_run_summary": _clean_text(metadata.get("refresh_run_summary")),
            "tool_calls_summary": cls._parse_json_list(
                metadata.get("tool_calls_summary_json")
            ),
            "temporary_evidence_blocks": cls._parse_json_list(
                metadata.get("temporary_evidence_blocks_json")
            ),
        }


_stock_analysis_research_task_service: Optional[StockAnalysisResearchTaskService] = None


def get_stock_analysis_research_task_service() -> StockAnalysisResearchTaskService:
    global _stock_analysis_research_task_service
    if _stock_analysis_research_task_service is None:
        _stock_analysis_research_task_service = StockAnalysisResearchTaskService()
    return _stock_analysis_research_task_service


def reset_stock_analysis_research_task_service() -> None:
    global _stock_analysis_research_task_service
    _stock_analysis_research_task_service = None
