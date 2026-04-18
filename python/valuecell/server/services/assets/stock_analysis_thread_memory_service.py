from __future__ import annotations

import datetime as dt
import json
from typing import Any, Optional, Sequence

from loguru import logger

from valuecell.core.types import NotifyResponseEvent
from valuecell.server.services.conversation_service import ConversationService

from ...db.repositories.stock_analysis_thread_memory_repository import (
    StockAnalysisThreadMemoryRepository,
)
from .stock_analysis_workspace_service import StockAnalysisWorkspaceService

MEMORY_MESSAGE_LIMIT = 24


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


class StockAnalysisThreadMemoryService:
    def __init__(
        self,
        stock_analysis_workspace_service: Optional[StockAnalysisWorkspaceService] = None,
        stock_analysis_thread_memory_repository: Optional[
            StockAnalysisThreadMemoryRepository
        ] = None,
        conversation_service: Optional[ConversationService] = None,
    ) -> None:
        self.stock_analysis_workspace_service = (
            stock_analysis_workspace_service or StockAnalysisWorkspaceService()
        )
        self.stock_analysis_thread_memory_repository = (
            stock_analysis_thread_memory_repository
            or StockAnalysisThreadMemoryRepository()
        )
        self.conversation_service = conversation_service or ConversationService()

    async def list_memories(
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
        items = self.stock_analysis_thread_memory_repository.list_memories(
            user_id=user_id,
            thread_id=thread_id,
        )
        serialized = self._serialize_memories(items)
        active_memory = next(
            (item for item in serialized if bool(item.get("is_active"))),
            None,
        )
        return {
            "thread_id": thread_id,
            "active_memory": active_memory,
            "items": serialized,
            "count": len(serialized),
            "generated_at": _utcnow().isoformat(),
        }

    async def get_memory(
        self,
        *,
        user_id: str,
        thread_id: int,
        memory_id: int,
    ) -> dict[str, Any] | None:
        memory = self.stock_analysis_thread_memory_repository.get_memory_by_id(
            user_id=user_id,
            thread_id=thread_id,
            memory_id=memory_id,
        )
        if memory is None:
            return None
        memories = self.stock_analysis_thread_memory_repository.list_memories(
            user_id=user_id,
            thread_id=thread_id,
        )
        serialized = self._serialize_memories(memories)
        return next(
            (item for item in serialized if int(item.get("memory_id") or 0) == memory_id),
            None,
        )

    async def get_active_memory(
        self,
        *,
        user_id: str,
        thread_id: int,
    ) -> dict[str, Any] | None:
        memory = self.stock_analysis_thread_memory_repository.get_active_memory(
            user_id=user_id,
            thread_id=thread_id,
        )
        if memory is None:
            return None
        return await self.get_memory(
            user_id=user_id,
            thread_id=thread_id,
            memory_id=int(memory.id),
        )

    async def capture_memory(
        self,
        *,
        user_id: str,
        thread_id: int,
        title: str | None = None,
    ) -> dict[str, Any] | None:
        return await self._create_memory_snapshot(
            user_id=user_id,
            thread_id=thread_id,
            title_override=title,
            seed_memory=None,
            reason="capture",
        )

    async def activate_memory(
        self,
        *,
        user_id: str,
        thread_id: int,
        memory_id: int,
    ) -> dict[str, Any] | None:
        memory = self.stock_analysis_thread_memory_repository.get_memory_by_id(
            user_id=user_id,
            thread_id=thread_id,
            memory_id=memory_id,
        )
        if memory is None:
            return None
        self.stock_analysis_thread_memory_repository.deactivate_thread_memories(
            user_id=user_id,
            thread_id=thread_id,
            exclude_memory_id=memory_id,
        )
        updated = self.stock_analysis_thread_memory_repository.update_memory(
            user_id=user_id,
            thread_id=thread_id,
            memory_id=memory_id,
            payload={
                "is_active": True,
                "updated_at": _utcnow(),
            },
        )
        if updated is None:
            return None
        return await self.get_memory(
            user_id=user_id,
            thread_id=thread_id,
            memory_id=memory_id,
        )

    async def refresh_memory(
        self,
        *,
        user_id: str,
        thread_id: int,
        memory_id: int,
        title: str | None = None,
    ) -> dict[str, Any] | None:
        seed_memory = await self.get_memory(
            user_id=user_id,
            thread_id=thread_id,
            memory_id=memory_id,
        )
        if seed_memory is None:
            return None
        return await self._create_memory_snapshot(
            user_id=user_id,
            thread_id=thread_id,
            title_override=title,
            seed_memory=seed_memory,
            reason="refresh",
        )

    async def _create_memory_snapshot(
        self,
        *,
        user_id: str,
        thread_id: int,
        title_override: str | None,
        seed_memory: dict[str, Any] | None,
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
            conversation_id=str(thread.get("conversation_id") or ""),
        )
        try:
            payload = self._build_memory_payload(
                user_id=user_id,
                thread=thread,
                context_cards=context_cards,
                messages=messages,
                title_override=title_override,
                seed_memory=seed_memory,
                reason=reason,
            )
        except Exception as exc:
            logger.warning(
                "Stock analysis thread memory synthesis failed, fallback applied: {err}",
                err=str(exc),
            )
            payload = self._build_fallback_memory_payload(
                user_id=user_id,
                thread=thread,
                context_cards=context_cards,
                messages=messages,
                title_override=title_override,
                seed_memory=seed_memory,
                reason=reason,
            )
        self.stock_analysis_thread_memory_repository.deactivate_thread_memories(
            user_id=user_id,
            thread_id=thread_id,
        )
        created = self.stock_analysis_thread_memory_repository.create_memory(payload)
        if created is None:
            return None
        return await self.get_memory(
            user_id=user_id,
            thread_id=thread_id,
            memory_id=int(created.id),
        )

    async def _list_thread_messages(self, *, conversation_id: str) -> list[dict[str, Any]]:
        if not conversation_id:
            return []
        items = await self.conversation_service.core_conversation_service.get_conversation_items(
            conversation_id=conversation_id,
            limit=MEMORY_MESSAGE_LIMIT,
        )
        return [
            self._serialize_message_item(item)
            for item in items
            if str(getattr(item, "event", "")) == str(NotifyResponseEvent.MESSAGE)
        ]

    def _build_memory_payload(
        self,
        *,
        user_id: str,
        thread: dict[str, Any],
        context_cards: Sequence[dict[str, Any]],
        messages: Sequence[dict[str, Any]],
        title_override: str | None,
        seed_memory: dict[str, Any] | None,
        reason: str,
    ) -> dict[str, Any]:
        latest_assistant = next(
            (item for item in reversed(messages) if self._is_assistant_role(item)),
            None,
        )
        latest_user = next(
            (item for item in reversed(messages) if not self._is_assistant_role(item)),
            None,
        )
        compare_targets = list(thread.get("compare_targets_json") or [])
        focus_tickers = _unique_str_list(
            list(thread.get("ticker_refs_json") or [])
            + [ref for item in context_cards for ref in list(item.get("ticker_refs_json") or [])]
        )
        focus_themes = _unique_str_list(
            list(thread.get("theme_refs_json") or [])
            + [ref for item in context_cards for ref in list(item.get("theme_refs_json") or [])]
        )
        compared_tickers = _unique_str_list(
            item.get("ref") for item in compare_targets if item.get("target_type") == "ticker"
        )
        recent_refresh_summary = self._pick_recent_refresh_summary(messages)
        recent_evidence_titles = self._pick_recent_evidence_titles(messages)
        pinned_cards = [item for item in context_cards if bool(item.get("is_pinned"))]
        stale_cards = [item for item in context_cards if bool(item.get("is_stale"))]
        support_points = self._pick_support_points(
            thread=thread,
            pinned_cards=pinned_cards,
            context_cards=context_cards,
            latest_assistant=latest_assistant,
            seed_memory=seed_memory,
        )
        opposing_points = self._pick_opposing_points(
            context_cards=context_cards,
            latest_assistant=latest_assistant,
            seed_memory=seed_memory,
        )
        risk_points = self._pick_risk_points(
            stale_cards=stale_cards,
            context_cards=context_cards,
            compare_targets=compare_targets,
            recent_evidence_titles=recent_evidence_titles,
            seed_memory=seed_memory,
        )
        key_uncertainties = self._pick_uncertainties(
            messages=messages,
            context_cards=context_cards,
            seed_memory=seed_memory,
        )
        invalidation_conditions = self._pick_invalidation_conditions(
            stale_cards=stale_cards,
            compare_targets=compare_targets,
            recent_refresh_summary=recent_refresh_summary,
            seed_memory=seed_memory,
        )
        next_questions = self._pick_next_questions(
            latest_user=latest_user,
            compare_targets=compare_targets,
            seed_memory=seed_memory,
        )
        next_data_to_check = self._pick_next_data_to_check(
            stale_cards=stale_cards,
            messages=messages,
            recent_evidence_titles=recent_evidence_titles,
            seed_memory=seed_memory,
        )
        summary = self._build_summary(
            thread=thread,
            focus_tickers=focus_tickers,
            compared_tickers=compared_tickers,
            context_cards=context_cards,
            latest_assistant=latest_assistant,
            recent_refresh_summary=recent_refresh_summary,
            seed_memory=seed_memory,
        )
        stance = self._resolve_stance(
            thread=thread,
            stale_cards=stale_cards,
            compare_targets=compare_targets,
            seed_memory=seed_memory,
        )
        confidence = self._resolve_confidence(
            context_cards=context_cards,
            stale_cards=stale_cards,
            latest_assistant=latest_assistant,
            seed_memory=seed_memory,
        )
        time_horizon = self._resolve_time_horizon(
            thread=thread,
            latest_assistant=latest_assistant,
            seed_memory=seed_memory,
        )
        linked_message_ids = _unique_str_list(
            item.get("item_id") for item in messages[-8:] if item.get("item_id")
        )
        source_snapshot = {
            "thread_title": thread.get("title"),
            "focus_type": thread.get("focus_type"),
            "reason": reason,
            "context_count": len(context_cards),
            "compare_target_count": len(compare_targets),
            "linked_context_titles": [
                _clean_text(item.get("title"))
                for item in context_cards[:6]
                if _clean_text(item.get("title"))
            ],
            "recent_user_question": _clean_text(
                (latest_user or {}).get("content"),
                fallback="",
            ),
            "recent_refresh_summary": recent_refresh_summary,
            "recent_evidence_titles": recent_evidence_titles,
        }
        return {
            "thread_id": int(thread.get("thread_id") or 0),
            "user_id": user_id,
            "title": self._resolve_memory_title(
                thread=thread,
                title_override=title_override,
                seed_memory=seed_memory,
            ),
            "summary": summary,
            "stance": stance,
            "confidence": confidence,
            "time_horizon": time_horizon,
            "focus_tickers_json": focus_tickers,
            "focus_themes_json": focus_themes,
            "compared_tickers_json": compared_tickers,
            "support_points_json": support_points,
            "opposing_points_json": opposing_points,
            "risk_points_json": risk_points,
            "key_uncertainties_json": key_uncertainties,
            "invalidation_conditions_json": invalidation_conditions,
            "next_questions_json": next_questions,
            "next_data_to_check_json": next_data_to_check,
            "linked_context_ids_json": [
                int(item.get("context_id") or 0)
                for item in context_cards
                if int(item.get("context_id") or 0) > 0
            ],
            "linked_message_ids_json": linked_message_ids,
            "linked_compare_targets_json": compare_targets,
            "source_snapshot_json": source_snapshot,
            "is_active": True,
        }

    def _build_fallback_memory_payload(
        self,
        *,
        user_id: str,
        thread: dict[str, Any],
        context_cards: Sequence[dict[str, Any]],
        messages: Sequence[dict[str, Any]],
        title_override: str | None,
        seed_memory: dict[str, Any] | None,
        reason: str,
    ) -> dict[str, Any]:
        compare_targets = list(thread.get("compare_targets_json") or [])
        latest_assistant = next(
            (item for item in reversed(messages) if self._is_assistant_role(item)),
            None,
        )
        summary = _clean_text(
            (latest_assistant or {}).get("content"),
            fallback="当前线程已形成一轮显式研究讨论，但仍需结合最新上下文继续确认。",
        )[:240]
        stale_titles = [
            _clean_text(item.get("title"))
            for item in context_cards
            if bool(item.get("is_stale")) and _clean_text(item.get("title"))
        ]
        return {
            "thread_id": int(thread.get("thread_id") or 0),
            "user_id": user_id,
            "title": self._resolve_memory_title(
                thread=thread,
                title_override=title_override,
                seed_memory=seed_memory,
            ),
            "summary": summary,
            "stance": "等待刷新后确认" if stale_titles else "继续观察",
            "confidence": 0.3 if stale_titles else 0.45,
            "time_horizon": "短线到波段",
            "focus_tickers_json": list(thread.get("ticker_refs_json") or []),
            "focus_themes_json": list(thread.get("theme_refs_json") or []),
            "compared_tickers_json": [
                item.get("ref")
                for item in compare_targets
                if item.get("target_type") == "ticker"
            ],
            "support_points_json": [
                _clean_text(item.get("title"))
                for item in context_cards[:3]
                if _clean_text(item.get("title"))
            ]
            or ["当前主要依据仍来自已挂载上下文卡片。"],
            "opposing_points_json": list(seed_memory.get("opposing_points_json") or [])
            if seed_memory
            else [],
            "risk_points_json": stale_titles[:3]
            or ["上下文不足时不宜把研究结论外推成强动作。"],
            "key_uncertainties_json": ["仍需结合更多上下文和最新补数继续确认。"],
            "invalidation_conditions_json": [
                "若刷新后的上下文摘要明显变化，则当前研究记忆需要重建。"
            ],
            "next_questions_json": ["下一步需要先核对当前线程中最关键的上下文是否仍有效。"],
            "next_data_to_check_json": stale_titles[:3] or ["最近一轮关键上下文卡片"],
            "linked_context_ids_json": [
                int(item.get("context_id") or 0)
                for item in context_cards
                if int(item.get("context_id") or 0) > 0
            ],
            "linked_message_ids_json": [
                _clean_text(item.get("item_id"))
                for item in messages[-6:]
                if _clean_text(item.get("item_id"))
            ],
            "linked_compare_targets_json": compare_targets,
            "source_snapshot_json": {
                "thread_title": thread.get("title"),
                "focus_type": thread.get("focus_type"),
                "reason": f"{reason}:fallback",
                "context_count": len(context_cards),
            },
            "is_active": True,
        }

    def _serialize_memories(self, memories: Sequence[Any]) -> list[dict[str, Any]]:
        ascending = list(reversed(list(memories)))
        version_map = {
            int(item.id): index + 1
            for index, item in enumerate(ascending)
            if int(getattr(item, "id", 0) or 0) > 0
        }
        result: list[dict[str, Any]] = []
        for item in memories:
            data = item.to_dict()
            data["version"] = int(version_map.get(int(item.id), 0))
            data["linked_context_count"] = len(list(data.get("linked_context_ids_json") or []))
            data["linked_message_count"] = len(list(data.get("linked_message_ids_json") or []))
            data["compare_target_count"] = len(
                list(data.get("linked_compare_targets_json") or [])
            )
            result.append(data)
        return result

    @staticmethod
    def _resolve_memory_title(
        *,
        thread: dict[str, Any],
        title_override: str | None,
        seed_memory: dict[str, Any] | None,
    ) -> str:
        if _clean_text(title_override):
            return _clean_text(title_override)
        if seed_memory and _clean_text(seed_memory.get("title")):
            return _clean_text(seed_memory.get("title"))
        thread_title = _clean_text(thread.get("title"), fallback="未命名线程")
        return f"{thread_title} 研究记忆"

    @staticmethod
    def _build_summary(
        *,
        thread: dict[str, Any],
        focus_tickers: Sequence[str],
        compared_tickers: Sequence[str],
        context_cards: Sequence[dict[str, Any]],
        latest_assistant: dict[str, Any] | None,
        recent_refresh_summary: str | None,
        seed_memory: dict[str, Any] | None,
    ) -> str:
        assistant_excerpt = _clean_text((latest_assistant or {}).get("content"))
        if assistant_excerpt:
            assistant_excerpt = assistant_excerpt[:180]
        object_label = (
            "、".join(compared_tickers[:3])
            if compared_tickers
            else "、".join(focus_tickers[:3]) or _clean_text(thread.get("title"), fallback="当前线程")
        )
        base = (
            f"当前线程围绕 {object_label} 展开研究，已有 {len(context_cards)} 张显式上下文卡片。"
        )
        if assistant_excerpt:
            base += f" 最近一轮关键回答指出：{assistant_excerpt}"
        elif seed_memory and _clean_text(seed_memory.get("summary")):
            base += f" 延续上一版研究记忆：{_clean_text(seed_memory.get('summary'))[:120]}"
        if recent_refresh_summary:
            base += f" 最近刷新摘要：{recent_refresh_summary}"
        return base[:480]

    @staticmethod
    def _resolve_stance(
        *,
        thread: dict[str, Any],
        stale_cards: Sequence[dict[str, Any]],
        compare_targets: Sequence[dict[str, Any]],
        seed_memory: dict[str, Any] | None,
    ) -> str:
        if stale_cards:
            return "等待刷新后确认"
        if len(compare_targets) >= 2:
            return "比较观察"
        if _clean_text((seed_memory or {}).get("stance")):
            return _clean_text(seed_memory.get("stance"))
        focus_type = _clean_text(thread.get("focus_type"), fallback="mixed")
        if focus_type == "holding":
            return "继续观察持仓"
        return "继续观察"

    @staticmethod
    def _resolve_confidence(
        *,
        context_cards: Sequence[dict[str, Any]],
        stale_cards: Sequence[dict[str, Any]],
        latest_assistant: dict[str, Any] | None,
        seed_memory: dict[str, Any] | None,
    ) -> float:
        base = 0.35
        if context_cards:
            base += min(len(context_cards), 4) * 0.08
        if latest_assistant and _clean_text(latest_assistant.get("content")):
            base += 0.08
        if stale_cards:
            base -= 0.2
        if seed_memory and float(seed_memory.get("confidence") or 0.0) > base:
            base = min(float(seed_memory.get("confidence") or 0.0), 0.75)
        return round(min(max(base, 0.15), 0.85), 2)

    @staticmethod
    def _resolve_time_horizon(
        *,
        thread: dict[str, Any],
        latest_assistant: dict[str, Any] | None,
        seed_memory: dict[str, Any] | None,
    ) -> str:
        content = _clean_text((latest_assistant or {}).get("content")).lower()
        if any(token in content for token in ("波段", "一两周", "两周", "一月", "一个月")):
            return "波段"
        if _clean_text((seed_memory or {}).get("time_horizon")):
            return _clean_text(seed_memory.get("time_horizon"))
        focus_type = _clean_text(thread.get("focus_type"))
        if focus_type == "holding":
            return "短线到波段"
        return "短线到波段"

    @staticmethod
    def _pick_support_points(
        *,
        thread: dict[str, Any],
        pinned_cards: Sequence[dict[str, Any]],
        context_cards: Sequence[dict[str, Any]],
        latest_assistant: dict[str, Any] | None,
        seed_memory: dict[str, Any] | None,
    ) -> list[str]:
        points = [
            f"{_clean_text(item.get('title'))}：{_clean_text(item.get('summary'))[:72]}"
            for item in list(pinned_cards)[:3]
            if _clean_text(item.get("title")) and _clean_text(item.get("summary"))
        ]
        if not points:
            points = [
                f"{_clean_text(item.get('title'))}：{_clean_text(item.get('summary'))[:72]}"
                for item in list(context_cards)[:3]
                if _clean_text(item.get("title")) and _clean_text(item.get("summary"))
            ]
        if latest_assistant and _clean_text(latest_assistant.get("content")):
            points.append(f"最近回答：{_clean_text(latest_assistant.get('content'))[:90]}")
        if not points and seed_memory:
            points = list(seed_memory.get("support_points_json") or [])
        if not points:
            points = [f"当前线程标题为：{_clean_text(thread.get('title'), fallback='未命名线程')}"]
        return points[:4]

    @staticmethod
    def _pick_opposing_points(
        *,
        context_cards: Sequence[dict[str, Any]],
        latest_assistant: dict[str, Any] | None,
        seed_memory: dict[str, Any] | None,
    ) -> list[str]:
        points = [
            f"{_clean_text(item.get('title'))} 仍存在条件限制：{_clean_text(item.get('staleness_hint'))[:72]}"
            for item in context_cards
            if _clean_text(item.get("staleness_hint")) and not bool(item.get("is_pinned"))
        ][:2]
        if not points and latest_assistant and _clean_text(latest_assistant.get("tool_reason")):
            points.append(_clean_text(latest_assistant.get("tool_reason"))[:90])
        if not points and seed_memory:
            points = list(seed_memory.get("opposing_points_json") or [])
        return points[:3]

    @staticmethod
    def _pick_risk_points(
        *,
        stale_cards: Sequence[dict[str, Any]],
        context_cards: Sequence[dict[str, Any]],
        compare_targets: Sequence[dict[str, Any]],
        recent_evidence_titles: Sequence[str],
        seed_memory: dict[str, Any] | None,
    ) -> list[str]:
        points: list[str] = []
        if stale_cards:
            points.append("部分关键上下文较旧，刷新前不宜给出强动作。")
        if len(compare_targets) >= 2:
            points.append("比较对象可能处在不同阶段，不能只按单一口径横向外推。")
        if recent_evidence_titles:
            points.append("近期回答依赖过临时补数，需与长期上下文分开看待。")
        if not points and context_cards:
            points.append("当前研究仍依赖有限上下文，结论应保持保守。")
        if not points and seed_memory:
            points = list(seed_memory.get("risk_points_json") or [])
        return points[:4]

    @staticmethod
    def _pick_uncertainties(
        *,
        messages: Sequence[dict[str, Any]],
        context_cards: Sequence[dict[str, Any]],
        seed_memory: dict[str, Any] | None,
    ) -> list[str]:
        latest_assistant = next(
            (item for item in reversed(messages) if StockAnalysisThreadMemoryService._is_assistant_role(item)),
            None,
        )
        hints = list((latest_assistant or {}).get("missing_context_hints") or [])
        result = _unique_str_list(hints)
        if not context_cards:
            result.append("当前线程仍缺少稳定的显式上下文卡片。")
        if not result and seed_memory:
            result = list(seed_memory.get("key_uncertainties_json") or [])
        if not result:
            result = ["当前线程仍需结合下一轮补数或刷新结果继续确认。"]
        return result[:4]

    @staticmethod
    def _pick_invalidation_conditions(
        *,
        stale_cards: Sequence[dict[str, Any]],
        compare_targets: Sequence[dict[str, Any]],
        recent_refresh_summary: str | None,
        seed_memory: dict[str, Any] | None,
    ) -> list[str]:
        points = [
            "若关键上下文刷新后摘要或时间戳出现明显变化，则当前结论需要重建。"
        ]
        if len(compare_targets) >= 2:
            points.append("若比较对象集合发生变化，则本记忆不再适用。")
        if stale_cards:
            points.append("若过期卡片刷新后方向反转，则当前研究倾向失效。")
        if recent_refresh_summary:
            points.append("若下一次 refresh 与当前刷新摘要明显冲突，则应重新 capture。")
        if seed_memory:
            points.extend(list(seed_memory.get("invalidation_conditions_json") or [])[:1])
        return _unique_str_list(points)[:4]

    @staticmethod
    def _pick_next_questions(
        *,
        latest_user: dict[str, Any] | None,
        compare_targets: Sequence[dict[str, Any]],
        seed_memory: dict[str, Any] | None,
    ) -> list[str]:
        result: list[str] = []
        if latest_user and _clean_text(latest_user.get("content")):
            result.append(f"继续追问：{_clean_text(latest_user.get('content'))[:90]}")
        if len(compare_targets) >= 2:
            result.append("当前比较对象里，谁更强、谁仅保持观察？")
        if seed_memory:
            result.extend(list(seed_memory.get("next_questions_json") or [])[:1])
        if not result:
            result.append("刷新关键上下文后，当前研究结论是否仍成立？")
        return _unique_str_list(result)[:4]

    @staticmethod
    def _pick_next_data_to_check(
        *,
        stale_cards: Sequence[dict[str, Any]],
        messages: Sequence[dict[str, Any]],
        recent_evidence_titles: Sequence[str],
        seed_memory: dict[str, Any] | None,
    ) -> list[str]:
        result = [
            _clean_text(item.get("title"))
            for item in stale_cards[:3]
            if _clean_text(item.get("title"))
        ]
        latest_assistant = next(
            (item for item in reversed(messages) if StockAnalysisThreadMemoryService._is_assistant_role(item)),
            None,
        )
        result.extend(
            _clean_text(hint)
            for hint in list((latest_assistant or {}).get("missing_context_hints") or [])[:2]
        )
        result.extend(list(recent_evidence_titles[:1]))
        if seed_memory:
            result.extend(list(seed_memory.get("next_data_to_check_json") or [])[:1])
        if not result:
            result = ["最近一轮关键 context card 与 compare target 的最新状态"]
        return _unique_str_list(result)[:4]

    @staticmethod
    def _pick_recent_refresh_summary(messages: Sequence[dict[str, Any]]) -> str | None:
        for item in reversed(messages):
            summary = _clean_text(item.get("refresh_run_summary"))
            if summary:
                return summary
        return None

    @staticmethod
    def _pick_recent_evidence_titles(messages: Sequence[dict[str, Any]]) -> list[str]:
        for item in reversed(messages):
            blocks = list(item.get("temporary_evidence_blocks") or [])
            titles = [
                _clean_text(block.get("title"))
                for block in blocks
                if _clean_text(block.get("title"))
            ]
            if titles:
                return titles[:3]
        return []

    @staticmethod
    def _serialize_message_item(item: Any) -> dict[str, Any]:
        metadata = StockAnalysisThreadMemoryService._parse_json_dict(item.metadata)
        payload = StockAnalysisThreadMemoryService._parse_json_dict(item.payload)
        return {
            "item_id": getattr(item, "item_id", ""),
            "role": str(getattr(item, "role", "")),
            "content": _clean_text(payload.get("content")),
            "tool_reason": _clean_text(metadata.get("tool_reason")),
            "missing_context_hints": StockAnalysisThreadMemoryService._parse_json_list(
                metadata.get("missing_context_hints_json")
            ),
            "temporary_evidence_blocks": StockAnalysisThreadMemoryService._parse_json_list(
                metadata.get("temporary_evidence_blocks_json")
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


_stock_analysis_thread_memory_service: Optional[StockAnalysisThreadMemoryService] = None


def get_stock_analysis_thread_memory_service() -> StockAnalysisThreadMemoryService:
    global _stock_analysis_thread_memory_service
    if _stock_analysis_thread_memory_service is None:
        _stock_analysis_thread_memory_service = StockAnalysisThreadMemoryService()
    return _stock_analysis_thread_memory_service


def reset_stock_analysis_thread_memory_service() -> None:
    global _stock_analysis_thread_memory_service
    _stock_analysis_thread_memory_service = None
