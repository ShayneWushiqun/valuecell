from __future__ import annotations

import datetime as dt
import json
from typing import Any, Optional, Sequence

from loguru import logger

from valuecell.core.types import NotifyResponseEvent
from valuecell.server.services.conversation_service import ConversationService

from ...db.repositories.stock_analysis_thread_compression_repository import (
    StockAnalysisThreadCompressionRepository,
)
from .stock_analysis_thread_memory_service import (
    StockAnalysisThreadMemoryService,
    get_stock_analysis_thread_memory_service,
)
from .stock_analysis_workspace_service import StockAnalysisWorkspaceService

COMPRESSION_MESSAGE_LIMIT = 80
COMPRESSION_RECOMMENDED_MESSAGE_THRESHOLD = 20
COMPRESSION_RECOMMENDED_HISTORY_SIZE = 10_000
COMPRESSION_STALE_UNCOMPRESSED_THRESHOLD = 8
RECENT_RAW_MESSAGE_LIMIT = 8


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


class StockAnalysisThreadCompressionService:
    def __init__(
        self,
        stock_analysis_workspace_service: Optional[StockAnalysisWorkspaceService] = None,
        stock_analysis_thread_compression_repository: Optional[
            StockAnalysisThreadCompressionRepository
        ] = None,
        stock_analysis_thread_memory_service: Optional[
            StockAnalysisThreadMemoryService
        ] = None,
        conversation_service: Optional[ConversationService] = None,
    ) -> None:
        self.stock_analysis_workspace_service = (
            stock_analysis_workspace_service or StockAnalysisWorkspaceService()
        )
        self.stock_analysis_thread_compression_repository = (
            stock_analysis_thread_compression_repository
            or StockAnalysisThreadCompressionRepository()
        )
        self.stock_analysis_thread_memory_service = (
            stock_analysis_thread_memory_service
            or get_stock_analysis_thread_memory_service()
        )
        self.conversation_service = conversation_service or ConversationService()

    async def list_compressions(
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
        messages = await self._list_thread_messages(
            conversation_id=str(thread.conversation_id or "")
        )
        items = self.stock_analysis_thread_compression_repository.list_compressions(
            user_id=user_id,
            thread_id=thread_id,
        )
        serialized = self._serialize_compressions(items)
        active = next((item for item in serialized if bool(item.get("is_active"))), None)
        overview = self._build_recommendation_overview(
            messages=messages,
            active_compression=active,
        )
        return {
            "thread_id": thread_id,
            "active_compression": active,
            "items": serialized,
            "count": len(serialized),
            **overview,
            "generated_at": _utcnow().isoformat(),
        }

    async def get_compression(
        self,
        *,
        user_id: str,
        thread_id: int,
        compression_id: int,
    ) -> dict[str, Any] | None:
        compression = self.stock_analysis_thread_compression_repository.get_compression_by_id(
            user_id=user_id,
            thread_id=thread_id,
            compression_id=compression_id,
        )
        if compression is None:
            return None
        all_items = self.stock_analysis_thread_compression_repository.list_compressions(
            user_id=user_id,
            thread_id=thread_id,
        )
        serialized = self._serialize_compressions(all_items)
        return next(
            (
                item
                for item in serialized
                if int(item.get("compression_id") or 0) == compression_id
            ),
            None,
        )

    async def get_active_compression(
        self,
        *,
        user_id: str,
        thread_id: int,
    ) -> dict[str, Any] | None:
        compression = self.stock_analysis_thread_compression_repository.get_active_compression(
            user_id=user_id,
            thread_id=thread_id,
        )
        if compression is None:
            return None
        return await self.get_compression(
            user_id=user_id,
            thread_id=thread_id,
            compression_id=int(compression.id),
        )

    async def capture_compression(
        self,
        *,
        user_id: str,
        thread_id: int,
        title: str | None = None,
    ) -> dict[str, Any] | None:
        return await self._create_compression_snapshot(
            user_id=user_id,
            thread_id=thread_id,
            title_override=title,
            seed_compression=None,
            reason="manual_capture",
        )

    async def activate_compression(
        self,
        *,
        user_id: str,
        thread_id: int,
        compression_id: int,
    ) -> dict[str, Any] | None:
        compression = self.stock_analysis_thread_compression_repository.get_compression_by_id(
            user_id=user_id,
            thread_id=thread_id,
            compression_id=compression_id,
        )
        if compression is None:
            return None
        self.stock_analysis_thread_compression_repository.deactivate_thread_compressions(
            user_id=user_id,
            thread_id=thread_id,
            exclude_compression_id=compression_id,
        )
        updated = self.stock_analysis_thread_compression_repository.update_compression(
            user_id=user_id,
            thread_id=thread_id,
            compression_id=compression_id,
            payload={
                "is_active": True,
                "updated_at": _utcnow(),
            },
        )
        if updated is None:
            return None
        return await self.get_compression(
            user_id=user_id,
            thread_id=thread_id,
            compression_id=compression_id,
        )

    async def refresh_compression(
        self,
        *,
        user_id: str,
        thread_id: int,
        compression_id: int,
        title: str | None = None,
    ) -> dict[str, Any] | None:
        seed = await self.get_compression(
            user_id=user_id,
            thread_id=thread_id,
            compression_id=compression_id,
        )
        if seed is None:
            return None
        return await self._create_compression_snapshot(
            user_id=user_id,
            thread_id=thread_id,
            title_override=title,
            seed_compression=seed,
            reason="manual_refresh",
        )

    async def get_prompt_context_state(
        self,
        *,
        user_id: str,
        thread_id: int,
        recent_limit: int = RECENT_RAW_MESSAGE_LIMIT,
    ) -> dict[str, Any]:
        thread = self.stock_analysis_workspace_service.stock_analysis_thread_repository.get_thread_by_id(
            user_id=user_id,
            thread_id=thread_id,
        )
        if thread is None:
            return {
                "active_compression": None,
                "recent_raw_messages": [],
                "recent_raw_message_count": 0,
                "compression_recommended": False,
                "compression_reason": None,
                "uncompressed_message_count": 0,
                "estimated_history_size": 0,
                "active_compression_stale": False,
            }
        messages = await self._list_thread_messages(
            conversation_id=str(thread.conversation_id or "")
        )
        active_compression = await self.get_active_compression(
            user_id=user_id,
            thread_id=thread_id,
        )
        recent_raw_messages = self._pick_recent_raw_messages(
            messages=messages,
            active_compression=active_compression,
            recent_limit=recent_limit,
        )
        overview = self._build_recommendation_overview(
            messages=messages,
            active_compression=active_compression,
        )
        return {
            "active_compression": active_compression,
            "recent_raw_messages": recent_raw_messages,
            "recent_raw_message_count": len(recent_raw_messages),
            **overview,
        }

    async def _create_compression_snapshot(
        self,
        *,
        user_id: str,
        thread_id: int,
        title_override: str | None,
        seed_compression: dict[str, Any] | None,
        reason: str,
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
        messages = await self._list_thread_messages(
            conversation_id=str(thread.get("conversation_id") or "")
        )
        active_memory = await self.stock_analysis_thread_memory_service.get_active_memory(
            user_id=user_id,
            thread_id=thread_id,
        )
        try:
            payload = self._build_compression_payload(
                user_id=user_id,
                thread=thread,
                context_cards=context_cards,
                messages=messages,
                active_memory=active_memory,
                title_override=title_override,
                seed_compression=seed_compression,
                reason=reason,
            )
        except Exception as exc:
            logger.warning(
                "Stock analysis thread compression synthesis failed, fallback applied: {err}",
                err=str(exc),
            )
            payload = self._build_fallback_compression_payload(
                user_id=user_id,
                thread=thread,
                context_cards=context_cards,
                messages=messages,
                active_memory=active_memory,
                title_override=title_override,
                seed_compression=seed_compression,
                reason=reason,
            )
        self.stock_analysis_thread_compression_repository.deactivate_thread_compressions(
            user_id=user_id,
            thread_id=thread_id,
        )
        created = self.stock_analysis_thread_compression_repository.create_compression(
            payload
        )
        if created is None:
            return None
        return await self.get_compression(
            user_id=user_id,
            thread_id=thread_id,
            compression_id=int(created.id),
        )

    def _build_compression_payload(
        self,
        *,
        user_id: str,
        thread: dict[str, Any],
        context_cards: Sequence[dict[str, Any]],
        messages: Sequence[dict[str, Any]],
        active_memory: dict[str, Any] | None,
        title_override: str | None,
        seed_compression: dict[str, Any] | None,
        reason: str,
    ) -> dict[str, Any]:
        latest_user = next(
            (item for item in reversed(messages) if not self._is_assistant_role(item)),
            None,
        )
        latest_assistant = next(
            (item for item in reversed(messages) if self._is_assistant_role(item)),
            None,
        )
        compare_targets = list(thread.get("compare_targets_json") or [])
        compared_tickers = _unique_str_list(
            item.get("ref") for item in compare_targets if item.get("target_type") == "ticker"
        )
        resolved_topics = self._pick_resolved_topics(messages=messages, active_memory=active_memory)
        open_questions = self._pick_open_questions(
            latest_user=latest_user,
            latest_assistant=latest_assistant,
            seed_compression=seed_compression,
            active_memory=active_memory,
        )
        recent_refresh_notes = self._pick_recent_refresh_notes(messages)
        recent_tooling_notes = self._pick_recent_tooling_notes(messages)
        recent_evidence_notes = self._pick_recent_evidence_notes(messages)
        recent_compare_notes = self._pick_recent_compare_notes(
            compare_targets=compare_targets,
            latest_assistant=latest_assistant,
        )
        next_questions = self._pick_next_questions(
            open_questions=open_questions,
            seed_compression=seed_compression,
        )
        covered_until_message_id = _clean_text(
            messages[-1].get("item_id") if messages else "",
            fallback="",
        ) or None
        focus_tickers = _unique_str_list(
            list(thread.get("ticker_refs_json") or [])
            + [ref for card in context_cards for ref in list(card.get("ticker_refs_json") or [])]
        )
        focus_themes = _unique_str_list(
            list(thread.get("theme_refs_json") or [])
            + [ref for card in context_cards for ref in list(card.get("theme_refs_json") or [])]
        )
        return {
            "thread_id": int(thread.get("thread_id") or 0),
            "user_id": user_id,
            "conversation_id": str(thread.get("conversation_id") or ""),
            "title": self._resolve_title(
                thread=thread,
                title_override=title_override,
                seed_compression=seed_compression,
            ),
            "summary": self._build_summary(
                thread=thread,
                latest_user=latest_user,
                latest_assistant=latest_assistant,
                active_memory=active_memory,
                recent_refresh_notes=recent_refresh_notes,
                recent_tooling_notes=recent_tooling_notes,
                recent_evidence_notes=recent_evidence_notes,
            ),
            "current_focus": self._build_current_focus(
                thread=thread,
                latest_user=latest_user,
                active_memory=active_memory,
            ),
            "covered_until_message_id": covered_until_message_id,
            "covered_message_count": len(messages),
            "source_message_ids_json": _unique_str_list(
                [item.get("item_id") for item in messages[-8:]]
            ),
            "resolved_topics_json": resolved_topics,
            "open_questions_json": open_questions,
            "recent_compare_notes_json": recent_compare_notes,
            "recent_refresh_notes_json": recent_refresh_notes,
            "recent_tooling_notes_json": recent_tooling_notes,
            "recent_evidence_notes_json": recent_evidence_notes,
            "active_memory_id": int(active_memory.get("memory_id") or 0)
            if active_memory
            else None,
            "focus_tickers_json": focus_tickers,
            "focus_themes_json": focus_themes,
            "compared_tickers_json": compared_tickers,
            "next_questions_json": next_questions,
            "compression_reason": reason,
            "is_active": True,
        }

    def _build_fallback_compression_payload(
        self,
        *,
        user_id: str,
        thread: dict[str, Any],
        context_cards: Sequence[dict[str, Any]],
        messages: Sequence[dict[str, Any]],
        active_memory: dict[str, Any] | None,
        title_override: str | None,
        seed_compression: dict[str, Any] | None,
        reason: str,
    ) -> dict[str, Any]:
        latest_user = next(
            (item for item in reversed(messages) if not self._is_assistant_role(item)),
            None,
        )
        latest_assistant = next(
            (item for item in reversed(messages) if self._is_assistant_role(item)),
            None,
        )
        summary = _clean_text(
            (latest_assistant or {}).get("content"),
            fallback="当前线程已形成多轮对话，建议后续继续基于压缩摘要和最近原始消息推进。",
        )[:240]
        return {
            "thread_id": int(thread.get("thread_id") or 0),
            "user_id": user_id,
            "conversation_id": str(thread.get("conversation_id") or ""),
            "title": self._resolve_title(
                thread=thread,
                title_override=title_override,
                seed_compression=seed_compression,
            ),
            "summary": summary,
            "current_focus": _clean_text(
                (latest_user or {}).get("content"),
                fallback=str(thread.get("title") or "当前线程"),
            )[:120],
            "covered_until_message_id": _clean_text(
                messages[-1].get("item_id") if messages else "",
                fallback="",
            )
            or None,
            "covered_message_count": len(messages),
            "source_message_ids_json": _unique_str_list(
                [item.get("item_id") for item in messages[-6:]]
            ),
            "resolved_topics_json": [
                "最近一轮已回答的问题已进入压缩摘要。"
            ],
            "open_questions_json": [
                _clean_text((latest_user or {}).get("content"), fallback="仍有未完成问题待继续追问。")[:120]
            ],
            "recent_compare_notes_json": [],
            "recent_refresh_notes_json": self._pick_recent_refresh_notes(messages),
            "recent_tooling_notes_json": self._pick_recent_tooling_notes(messages),
            "recent_evidence_notes_json": self._pick_recent_evidence_notes(messages),
            "active_memory_id": int(active_memory.get("memory_id") or 0)
            if active_memory
            else None,
            "focus_tickers_json": _unique_str_list(thread.get("ticker_refs_json") or []),
            "focus_themes_json": _unique_str_list(thread.get("theme_refs_json") or []),
            "compared_tickers_json": [
                item.get("ref")
                for item in list(thread.get("compare_targets_json") or [])
                if item.get("target_type") == "ticker"
            ],
            "next_questions_json": ["继续结合最近原始消息确认当前未完成问题。"],
            "compression_reason": f"{reason}:fallback",
            "is_active": True,
        }

    def _serialize_compressions(self, items: Sequence[Any]) -> list[dict[str, Any]]:
        ascending = list(reversed(list(items)))
        version_map = {
            int(item.id): index + 1
            for index, item in enumerate(ascending)
            if int(getattr(item, "id", 0) or 0) > 0
        }
        result: list[dict[str, Any]] = []
        for item in items:
            data = item.to_dict()
            data["version"] = int(version_map.get(int(item.id), 0))
            data["source_message_count"] = len(list(data.get("source_message_ids_json") or []))
            covered_id = _clean_text(data.get("covered_until_message_id"))
            data["covered_message_range_text"] = (
                f"已覆盖 {data.get('covered_message_count') or 0} 条消息，截止 {covered_id}"
                if covered_id
                else f"已覆盖 {data.get('covered_message_count') or 0} 条消息"
            )
            result.append(data)
        return result

    def _build_recommendation_overview(
        self,
        *,
        messages: Sequence[dict[str, Any]],
        active_compression: dict[str, Any] | None,
    ) -> dict[str, Any]:
        estimated_history_size = sum(len(_clean_text(item.get("content"))) for item in messages)
        uncompressed_messages = self._messages_after_active_compression(
            messages=messages,
            active_compression=active_compression,
        )
        uncompressed_count = len(uncompressed_messages)
        driver_count = 0
        for item in messages[-12:]:
            if _clean_text(item.get("refresh_run_summary")):
                driver_count += 1
            if list(item.get("provider_attempts") or []):
                driver_count += 1
            if list(item.get("temporary_evidence_blocks") or []):
                driver_count += 1
            if list(item.get("compared_tickers") or []):
                driver_count += 1
        active_stale = bool(active_compression) and (
            uncompressed_count >= COMPRESSION_STALE_UNCOMPRESSED_THRESHOLD
            or driver_count >= 3
        )
        recommended = (
            len(messages) >= COMPRESSION_RECOMMENDED_MESSAGE_THRESHOLD
            or estimated_history_size >= COMPRESSION_RECOMMENDED_HISTORY_SIZE
            or driver_count >= 3
        ) and (active_compression is None or active_stale)
        reasons: list[str] = []
        if len(messages) >= COMPRESSION_RECOMMENDED_MESSAGE_THRESHOLD:
            reasons.append(f"消息数已达 {len(messages)} 条")
        if estimated_history_size >= COMPRESSION_RECOMMENDED_HISTORY_SIZE:
            reasons.append(f"历史文本约 {estimated_history_size} 字符")
        if driver_count >= 3:
            reasons.append("最近 compare/refresh/tooling/evidence 变化较多")
        if active_stale:
            reasons.append("当前 active compression 对新消息覆盖不足")
        return {
            "compression_recommended": recommended,
            "compression_reason": "；".join(reasons) if reasons else None,
            "uncompressed_message_count": uncompressed_count,
            "estimated_history_size": estimated_history_size,
            "active_compression_stale": active_stale,
        }

    def _messages_after_active_compression(
        self,
        *,
        messages: Sequence[dict[str, Any]],
        active_compression: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        covered_until = _clean_text((active_compression or {}).get("covered_until_message_id"))
        if not covered_until:
            return list(messages)
        after: list[dict[str, Any]] = []
        covered_found = False
        for item in messages:
            if covered_found:
                after.append(item)
                continue
            if _clean_text(item.get("item_id")) == covered_until:
                covered_found = True
        return after if covered_found else list(messages)

    def _pick_recent_raw_messages(
        self,
        *,
        messages: Sequence[dict[str, Any]],
        active_compression: dict[str, Any] | None,
        recent_limit: int,
    ) -> list[dict[str, Any]]:
        candidates = self._messages_after_active_compression(
            messages=messages,
            active_compression=active_compression,
        )
        if len(candidates) > recent_limit:
            candidates = candidates[-recent_limit:]
        return [
            {
                "item_id": item.get("item_id"),
                "role": item.get("role"),
                "content": item.get("content"),
            }
            for item in candidates
            if _clean_text(item.get("content"))
        ]

    @staticmethod
    def _resolve_title(
        *,
        thread: dict[str, Any],
        title_override: str | None,
        seed_compression: dict[str, Any] | None,
    ) -> str:
        if _clean_text(title_override):
            return _clean_text(title_override)
        if seed_compression and _clean_text(seed_compression.get("title")):
            return _clean_text(seed_compression.get("title"))
        return f"{_clean_text(thread.get('title'), fallback='未命名线程')} 对话压缩"

    @staticmethod
    def _build_summary(
        *,
        thread: dict[str, Any],
        latest_user: dict[str, Any] | None,
        latest_assistant: dict[str, Any] | None,
        active_memory: dict[str, Any] | None,
        recent_refresh_notes: Sequence[str],
        recent_tooling_notes: Sequence[str],
        recent_evidence_notes: Sequence[str],
    ) -> str:
        parts = [
            f"当前线程《{_clean_text(thread.get('title'), fallback='未命名线程')}》已形成一轮可复用的对话压缩摘要。"
        ]
        if latest_user and _clean_text(latest_user.get("content")):
            parts.append(f"最近用户关注：{_clean_text(latest_user.get('content'))[:100]}")
        if latest_assistant and _clean_text(latest_assistant.get("content")):
            parts.append(f"最近关键回答：{_clean_text(latest_assistant.get('content'))[:120]}")
        if active_memory and _clean_text(active_memory.get("summary")):
            parts.append(f"当前 active memory：{_clean_text(active_memory.get('summary'))[:100]}")
        if recent_refresh_notes:
            parts.append(f"最近 refresh：{recent_refresh_notes[0]}")
        if recent_tooling_notes:
            parts.append(f"最近 tooling：{recent_tooling_notes[0]}")
        if recent_evidence_notes:
            parts.append(f"最近 evidence：{recent_evidence_notes[0]}")
        return " ".join(parts)[:480]

    @staticmethod
    def _build_current_focus(
        *,
        thread: dict[str, Any],
        latest_user: dict[str, Any] | None,
        active_memory: dict[str, Any] | None,
    ) -> str:
        if latest_user and _clean_text(latest_user.get("content")):
            return _clean_text(latest_user.get("content"))[:140]
        if active_memory and _clean_text(active_memory.get("summary")):
            return _clean_text(active_memory.get("summary"))[:140]
        return _clean_text(thread.get("title"), fallback="当前线程")

    @staticmethod
    def _pick_resolved_topics(
        *,
        messages: Sequence[dict[str, Any]],
        active_memory: dict[str, Any] | None,
    ) -> list[str]:
        result: list[str] = []
        for item in reversed(messages):
            if not StockAnalysisThreadCompressionService._is_assistant_role(item):
                continue
            content = _clean_text(item.get("content"))
            if content:
                result.append(content[:90])
            if len(result) >= 2:
                break
        if active_memory and _clean_text(active_memory.get("summary")):
            result.append(f"研究结论：{_clean_text(active_memory.get('summary'))[:90]}")
        return _unique_str_list(result)[:4] or ["最近一轮关键回答已纳入压缩摘要。"]

    @staticmethod
    def _pick_open_questions(
        *,
        latest_user: dict[str, Any] | None,
        latest_assistant: dict[str, Any] | None,
        seed_compression: dict[str, Any] | None,
        active_memory: dict[str, Any] | None,
    ) -> list[str]:
        result: list[str] = []
        if latest_user and _clean_text(latest_user.get("content")):
            result.append(_clean_text(latest_user.get("content"))[:100])
        result.extend(list((latest_assistant or {}).get("missing_context_hints") or [])[:2])
        if active_memory:
            result.extend(list(active_memory.get("next_questions_json") or [])[:1])
        if seed_compression:
            result.extend(list(seed_compression.get("open_questions_json") or [])[:1])
        return _unique_str_list(result)[:4] or ["后续仍需基于最近上下文继续追问。"]

    @staticmethod
    def _pick_recent_compare_notes(
        *,
        compare_targets: Sequence[dict[str, Any]],
        latest_assistant: dict[str, Any] | None,
    ) -> list[str]:
        result: list[str] = []
        tickers = [
            item.get("label") or item.get("ref")
            for item in compare_targets
            if item.get("target_type") == "ticker"
        ]
        if len(tickers) >= 2:
            result.append(f"当前 compare targets：{' / '.join(tickers[:4])}")
        if latest_assistant and list(latest_assistant.get("compared_tickers") or []):
            result.append(
                "最近回答比较了："
                + " / ".join(list(latest_assistant.get("compared_tickers") or [])[:4])
            )
        return _unique_str_list(result)[:3]

    @staticmethod
    def _pick_recent_refresh_notes(messages: Sequence[dict[str, Any]]) -> list[str]:
        result: list[str] = []
        for item in reversed(messages):
            summary = _clean_text(item.get("refresh_run_summary"))
            if summary:
                result.append(summary[:120])
            if len(result) >= 2:
                break
        return _unique_str_list(result)[:3]

    @staticmethod
    def _pick_recent_tooling_notes(messages: Sequence[dict[str, Any]]) -> list[str]:
        result: list[str] = []
        for item in reversed(messages):
            summaries = list(item.get("tool_calls_summary") or [])
            result.extend(_clean_text(value)[:120] for value in summaries if _clean_text(value))
            if len(result) >= 2:
                break
        return _unique_str_list(result)[:3]

    @staticmethod
    def _pick_recent_evidence_notes(messages: Sequence[dict[str, Any]]) -> list[str]:
        result: list[str] = []
        for item in reversed(messages):
            blocks = list(item.get("temporary_evidence_blocks") or [])
            for block in blocks:
                title = _clean_text(block.get("title"))
                summary = _clean_text(block.get("summary"))
                if title or summary:
                    result.append(f"{title or '临时证据'}：{summary[:80]}")
            if len(result) >= 2:
                break
        return _unique_str_list(result)[:3]

    @staticmethod
    def _pick_next_questions(
        *,
        open_questions: Sequence[str],
        seed_compression: dict[str, Any] | None,
    ) -> list[str]:
        result = list(open_questions[:2])
        if seed_compression:
            result.extend(list(seed_compression.get("next_questions_json") or [])[:1])
        return _unique_str_list(result)[:4] or ["继续结合最近原始消息推进未完成问题。"]

    async def _list_thread_messages(self, *, conversation_id: str) -> list[dict[str, Any]]:
        if not conversation_id:
            return []
        items = await self.conversation_service.core_conversation_service.get_conversation_items(
            conversation_id=conversation_id,
            limit=COMPRESSION_MESSAGE_LIMIT,
        )
        return [
            self._serialize_message_item(item)
            for item in items
            if str(getattr(item, "event", "")) == str(NotifyResponseEvent.MESSAGE)
        ]

    @staticmethod
    def _serialize_message_item(item: Any) -> dict[str, Any]:
        metadata = StockAnalysisThreadCompressionService._parse_json_dict(item.metadata)
        payload = StockAnalysisThreadCompressionService._parse_json_dict(item.payload)
        return {
            "item_id": getattr(item, "item_id", ""),
            "role": str(getattr(item, "role", "")),
            "content": _clean_text(payload.get("content")),
            "missing_context_hints": StockAnalysisThreadCompressionService._parse_json_list(
                metadata.get("missing_context_hints_json")
            ),
            "compared_tickers": StockAnalysisThreadCompressionService._parse_json_list(
                metadata.get("compared_tickers_json")
            ),
            "tool_calls_summary": StockAnalysisThreadCompressionService._parse_json_list(
                metadata.get("tool_calls_summary_json")
            ),
            "temporary_evidence_blocks": StockAnalysisThreadCompressionService._parse_json_list(
                metadata.get("temporary_evidence_blocks_json")
            ),
            "provider_attempts": StockAnalysisThreadCompressionService._parse_json_list(
                metadata.get("provider_attempts_json")
            ),
            "refresh_run_summary": _clean_text(metadata.get("refresh_run_summary")),
        }

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
        text = str(value or "").strip()
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


_stock_analysis_thread_compression_service: Optional[
    StockAnalysisThreadCompressionService
] = None


def get_stock_analysis_thread_compression_service() -> (
    StockAnalysisThreadCompressionService
):
    global _stock_analysis_thread_compression_service
    if _stock_analysis_thread_compression_service is None:
        _stock_analysis_thread_compression_service = (
            StockAnalysisThreadCompressionService()
        )
    return _stock_analysis_thread_compression_service


def reset_stock_analysis_thread_compression_service() -> None:
    global _stock_analysis_thread_compression_service
    _stock_analysis_thread_compression_service = None
