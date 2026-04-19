from __future__ import annotations

import datetime as dt
import json
from typing import Any, Optional

from agno.agent import Agent
from pydantic import BaseModel

from valuecell.core.types import BaseResponseDataPayload, NotifyResponseEvent, Role
from valuecell.server.services.conversation_service import ConversationService
from valuecell.utils.model import get_model_for_agent

from .stock_analysis_context_assembler import StockAnalysisContextAssembler
from .stock_analysis_tool_planner import (
    CONTEXT_ONLY_MODE,
    StockAnalysisToolPlanner,
    get_stock_analysis_tool_planner,
)
from .stock_analysis_refresh_service import (
    StockAnalysisRefreshService,
    get_stock_analysis_refresh_service,
)
from .stock_analysis_question_router_service import (
    StockAnalysisQuestionRouterService,
    get_stock_analysis_question_router_service,
)
from .stock_analysis_thread_memory_service import (
    StockAnalysisThreadMemoryService,
    get_stock_analysis_thread_memory_service,
)
from .stock_analysis_thread_compression_service import (
    StockAnalysisThreadCompressionService,
    get_stock_analysis_thread_compression_service,
)
from .stock_analysis_tooling_service import (
    StockAnalysisToolingResult,
    StockAnalysisToolingService,
    get_stock_analysis_tooling_service,
)
from .stock_analysis_workspace_service import (
    DEFAULT_USER_ID,
    STOCK_ANALYSIS_AGENT_NAME,
    StockAnalysisWorkspaceService,
    TEMPORARY_EVIDENCE_SAVED_CONTEXT_TYPE,
)

MESSAGE_LIMIT = 100


class StockAnalysisMessageResult(BaseModel):
    conversation_id: str
    thread_id: int
    answer_basis: str
    mode: str
    used_context_ids: list[int]
    missing_context_hints: list[str]
    compared_tickers: list[str]
    comparison_mode: bool
    stale_context_ids: list[int]
    refresh_recommended_context_ids: list[int]
    tool_reason: str | None = None
    tool_calls_summary: list[str]
    temporary_evidence_blocks: list[dict[str, Any]]
    unavailable_tools: list[dict[str, Any]]
    used_internal_sources: list[str]
    used_external_sources: list[str]
    provider_attempts: list[dict[str, Any]]
    provider_used: list[str]
    provider_fallback_chain: list[str]
    evidence_generated_at: str | None = None
    evidence_staleness_hint: str | None = None
    refreshed_before_answer: bool = False
    refresh_run_summary: str | None = None
    refreshed_context_ids: list[int]
    refresh_failed_context_ids: list[int]
    refresh_skipped_context_ids: list[int]
    refresh_changed_contexts: list[dict[str, Any]]
    used_active_memory: bool = False
    active_memory_id: int | None = None
    active_memory_title: str | None = None
    active_memory_updated_at: str | None = None
    active_memory_version: int | None = None
    used_active_compression: bool = False
    active_compression_id: int | None = None
    active_compression_title: str | None = None
    active_compression_updated_at: str | None = None
    active_compression_version: int | None = None
    active_compression_covered_until_message_id: str | None = None
    active_compression_covered_message_count: int | None = None
    recent_raw_message_count: int = 0
    compression_recommended: bool = False
    compression_reason: str | None = None
    uncompressed_message_count: int = 0
    estimated_history_size: int = 0
    active_compression_stale: bool = False
    question_intent: str | None = None
    response_strategy: str | None = None
    routing_reason: str | None = None
    recommended_next_action: str | None = None
    followup_candidates: list[str]
    suggested_task_titles: list[str]
    user_message: dict[str, Any]
    assistant_message: dict[str, Any]


class StockAnalysisMessageService:
    def __init__(
        self,
        stock_analysis_workspace_service: Optional[StockAnalysisWorkspaceService] = None,
        conversation_service: Optional[ConversationService] = None,
        context_assembler: Optional[StockAnalysisContextAssembler] = None,
        tool_planner: Optional[StockAnalysisToolPlanner] = None,
        tooling_service: Optional[StockAnalysisToolingService] = None,
        refresh_service: Optional[StockAnalysisRefreshService] = None,
        question_router_service: Optional[StockAnalysisQuestionRouterService] = None,
        thread_memory_service: Optional[StockAnalysisThreadMemoryService] = None,
        thread_compression_service: Optional[
            StockAnalysisThreadCompressionService
        ] = None,
    ) -> None:
        self.stock_analysis_workspace_service = (
            stock_analysis_workspace_service or StockAnalysisWorkspaceService()
        )
        self.conversation_service = conversation_service or ConversationService()
        self.context_assembler = context_assembler or StockAnalysisContextAssembler()
        self.tool_planner = tool_planner or get_stock_analysis_tool_planner()
        self.tooling_service = tooling_service or get_stock_analysis_tooling_service()
        self.refresh_service = refresh_service or get_stock_analysis_refresh_service()
        self.question_router_service = (
            question_router_service or get_stock_analysis_question_router_service()
        )
        self.thread_memory_service = (
            thread_memory_service or get_stock_analysis_thread_memory_service()
        )
        self.thread_compression_service = (
            thread_compression_service
            or get_stock_analysis_thread_compression_service()
        )

    async def list_messages(
        self,
        *,
        user_id: str,
        thread_id: int,
        limit: int = MESSAGE_LIMIT,
    ) -> dict[str, Any] | None:
        thread = self.stock_analysis_workspace_service.stock_analysis_thread_repository.get_thread_by_id(
            user_id=user_id,
            thread_id=thread_id,
        )
        if thread is None:
            return None
        items = await self.conversation_service.core_conversation_service.get_conversation_items(
            conversation_id=thread.conversation_id,
            limit=limit,
        )
        messages = [
            self._serialize_message_item(item)
            for item in items
            if str(item.event) == str(NotifyResponseEvent.MESSAGE)
        ]
        return {
            "conversation_id": thread.conversation_id,
            "thread_id": thread_id,
            "items": messages,
            "count": len(messages),
        }

    async def send_message(
        self,
        *,
        user_id: str,
        thread_id: int,
        message: str,
        force_tooling: bool = False,
        refresh_before_answer: bool = False,
    ) -> StockAnalysisMessageResult | None:
        thread_obj = self.stock_analysis_workspace_service.stock_analysis_thread_repository.get_thread_by_id(
            user_id=user_id,
            thread_id=thread_id,
        )
        if thread_obj is None:
            return None
        refresh_run = None
        if refresh_before_answer:
            refresh_run = await self.refresh_service.refresh_stale_contexts(
                user_id=user_id,
                thread_id=thread_id,
                include_supported_only=True,
                pin_refreshed_cards=False,
            )
        thread = self.stock_analysis_workspace_service._serialize_thread(thread_obj)
        context_result = await self.stock_analysis_workspace_service.list_context_cards(
            user_id=user_id,
            thread_id=thread_id,
        )
        context_cards = list((context_result or {}).get("items") or [])
        active_memory = await self.thread_memory_service.get_active_memory(
            user_id=user_id,
            thread_id=thread_id,
        )
        compression_state = await self.thread_compression_service.get_prompt_context_state(
            user_id=user_id,
            thread_id=thread_id,
        )
        active_compression = compression_state["active_compression"]
        recent_raw_messages = list(compression_state["recent_raw_messages"] or [])
        history_items = await self.conversation_service.core_conversation_service.get_conversation_items(
            conversation_id=thread_obj.conversation_id,
            limit=20,
        )
        history_messages = [
            self._serialize_message_item(item)
            for item in history_items
            if str(item.event) == str(NotifyResponseEvent.MESSAGE)
        ]
        question_routing = self.question_router_service.route_question(
            thread=thread,
            context_cards=context_cards,
            active_memory=active_memory,
            active_compression=active_compression,
            conversation_history=history_messages,
            user_message=message.strip(),
            force_tooling=force_tooling,
            refresh_before_answer=refresh_before_answer,
        )
        assembled = self.context_assembler.assemble(
            thread=thread,
            context_cards=context_cards,
            active_memory=active_memory,
            active_compression=active_compression,
            question_routing=question_routing.model_dump(),
            recent_raw_messages=recent_raw_messages,
            user_question=message,
        )
        planner_result = self.tool_planner.plan(
            thread=thread,
            context_cards=context_cards,
            conversation_history=history_messages,
            user_message=message.strip(),
            force_tooling=force_tooling,
            ticker_refs=assembled["ticker_refs"],
            theme_refs=assembled["theme_refs"],
        )
        effective_missing_hints = list(
            dict.fromkeys(
                list(assembled["missing_context_hints"])
                + list(planner_result.missing_context_hints)
            )
        )
        tooling_result = self.tooling_service.collect_evidence(
            user_id=user_id,
            thread=thread,
            context_cards=context_cards,
            planner_result=planner_result,
            ticker_refs=assembled["ticker_refs"],
            theme_refs=assembled["theme_refs"],
        )

        user_item = await self.conversation_service.core_conversation_service.add_item(
            role=Role.USER,
            event=NotifyResponseEvent.MESSAGE,
            conversation_id=thread_obj.conversation_id,
            payload=BaseResponseDataPayload(content=message.strip()),
            agent_name=STOCK_ANALYSIS_AGENT_NAME,
            metadata={
                "answer_basis": "当前上下文",
                "mode": planner_result.mode,
                "force_tooling": force_tooling,
                "refresh_before_answer": refresh_before_answer,
                "thread_id": thread_id,
            },
        )

        assistant_text = await self._generate_answer(
            assembled_context=assembled["prompt_context"],
            user_question=message.strip(),
            mode=planner_result.mode,
            tool_reason=planner_result.tool_reason,
            tooling_result=tooling_result,
        )
        assistant_metadata = {
            "answer_basis": tooling_result.answer_basis,
            "mode": planner_result.mode,
            "used_context_ids_json": json.dumps(assembled["used_context_ids"], ensure_ascii=False),
            "missing_context_hints_json": json.dumps(effective_missing_hints, ensure_ascii=False),
            "compared_tickers_json": json.dumps(assembled["compared_tickers"], ensure_ascii=False),
            "comparison_mode": assembled["comparison_mode"],
            "stale_context_ids_json": json.dumps(
                assembled["stale_context_ids"],
                ensure_ascii=False,
            ),
            "refresh_recommended_context_ids_json": json.dumps(
                assembled["refresh_recommended_context_ids"],
                ensure_ascii=False,
            ),
            "tool_reason": planner_result.tool_reason or "",
            "tool_calls_summary_json": json.dumps(
                tooling_result.tool_call_summaries,
                ensure_ascii=False,
            ),
            "temporary_evidence_blocks_json": json.dumps(
                tooling_result.temporary_evidence_blocks,
                ensure_ascii=False,
            ),
            "unavailable_tools_json": json.dumps(
                tooling_result.unavailable_tools,
                ensure_ascii=False,
            ),
            "used_internal_sources_json": json.dumps(
                tooling_result.used_internal_sources,
                ensure_ascii=False,
            ),
            "used_external_sources_json": json.dumps(
                tooling_result.used_external_sources,
                ensure_ascii=False,
            ),
            "provider_attempts_json": json.dumps(
                tooling_result.provider_attempts,
                ensure_ascii=False,
            ),
            "provider_used_json": json.dumps(
                tooling_result.provider_used,
                ensure_ascii=False,
            ),
            "provider_fallback_chain_json": json.dumps(
                tooling_result.provider_fallback_chain,
                ensure_ascii=False,
            ),
            "evidence_generated_at": tooling_result.evidence_generated_at or "",
            "evidence_staleness_hint": tooling_result.evidence_staleness_hint or "",
            "refreshed_before_answer": refresh_before_answer,
            "refresh_run_summary": str((refresh_run or {}).get("summary") or "").strip(),
            "refreshed_context_ids_json": json.dumps(
                list((refresh_run or {}).get("refreshed_context_ids") or []),
                ensure_ascii=False,
            ),
            "refresh_failed_context_ids_json": json.dumps(
                list((refresh_run or {}).get("failed_context_ids") or []),
                ensure_ascii=False,
            ),
            "refresh_skipped_context_ids_json": json.dumps(
                list((refresh_run or {}).get("skipped_context_ids") or []),
                ensure_ascii=False,
            ),
            "refresh_changed_contexts_json": json.dumps(
                list((refresh_run or {}).get("changed_contexts") or []),
                ensure_ascii=False,
            ),
            "used_active_memory": assembled["used_active_memory"],
            "active_memory_id": int(active_memory.get("memory_id") or 0)
            if active_memory
            else 0,
            "active_memory_title": str(active_memory.get("title") or "").strip()
            if active_memory
            else "",
            "active_memory_updated_at": str(active_memory.get("updated_at") or "").strip()
            if active_memory
            else "",
            "active_memory_version": int(active_memory.get("version") or 0)
            if active_memory
            else 0,
            "used_active_compression": assembled["used_active_compression"],
            "active_compression_id": int(active_compression.get("compression_id") or 0)
            if active_compression
            else 0,
            "active_compression_title": str(active_compression.get("title") or "").strip()
            if active_compression
            else "",
            "active_compression_updated_at": str(
                active_compression.get("updated_at") or ""
            ).strip()
            if active_compression
            else "",
            "active_compression_version": int(active_compression.get("version") or 0)
            if active_compression
            else 0,
            "active_compression_covered_until_message_id": str(
                active_compression.get("covered_until_message_id") or ""
            ).strip()
            if active_compression
            else "",
            "active_compression_covered_message_count": int(
                active_compression.get("covered_message_count") or 0
            )
            if active_compression
            else 0,
            "recent_raw_message_count": int(
                compression_state["recent_raw_message_count"] or 0
            ),
            "compression_recommended": bool(
                compression_state["compression_recommended"]
            ),
            "compression_reason": str(
                compression_state.get("compression_reason") or ""
            ).strip(),
            "uncompressed_message_count": int(
                compression_state["uncompressed_message_count"] or 0
            ),
            "estimated_history_size": int(
                compression_state["estimated_history_size"] or 0
            ),
            "active_compression_stale": bool(
                compression_state["active_compression_stale"]
            ),
            "question_intent": question_routing.question_intent,
            "response_strategy": question_routing.response_strategy,
            "routing_reason": question_routing.routing_reason,
            "recommended_next_action": question_routing.recommended_next_action,
            "followup_candidates_json": json.dumps(
                question_routing.followup_candidates,
                ensure_ascii=False,
            ),
            "suggested_task_titles_json": json.dumps(
                question_routing.suggested_task_titles,
                ensure_ascii=False,
            ),
            "thread_id": thread_id,
        }
        assistant_item = await self.conversation_service.core_conversation_service.add_item(
            role=Role.AGENT,
            event=NotifyResponseEvent.MESSAGE,
            conversation_id=thread_obj.conversation_id,
            payload=BaseResponseDataPayload(content=assistant_text),
            agent_name=STOCK_ANALYSIS_AGENT_NAME,
            metadata=assistant_metadata,
        )
        self.stock_analysis_workspace_service.stock_analysis_thread_repository.update_thread(
            user_id=user_id,
            thread_id=thread_id,
            payload={"updated_at": dt.datetime.now(dt.UTC)},
        )
        return StockAnalysisMessageResult(
            conversation_id=thread_obj.conversation_id,
            thread_id=thread_id,
            answer_basis=tooling_result.answer_basis,
            mode=planner_result.mode,
            used_context_ids=assembled["used_context_ids"],
            missing_context_hints=effective_missing_hints,
            compared_tickers=assembled["compared_tickers"],
            comparison_mode=assembled["comparison_mode"],
            stale_context_ids=assembled["stale_context_ids"],
            refresh_recommended_context_ids=assembled["refresh_recommended_context_ids"],
            tool_reason=planner_result.tool_reason,
            tool_calls_summary=tooling_result.tool_call_summaries,
            temporary_evidence_blocks=tooling_result.temporary_evidence_blocks,
            unavailable_tools=tooling_result.unavailable_tools,
            used_internal_sources=tooling_result.used_internal_sources,
            used_external_sources=tooling_result.used_external_sources,
            provider_attempts=tooling_result.provider_attempts,
            provider_used=tooling_result.provider_used,
            provider_fallback_chain=tooling_result.provider_fallback_chain,
            evidence_generated_at=tooling_result.evidence_generated_at,
            evidence_staleness_hint=tooling_result.evidence_staleness_hint,
            refreshed_before_answer=refresh_before_answer,
            refresh_run_summary=(refresh_run or {}).get("summary"),
            refreshed_context_ids=list((refresh_run or {}).get("refreshed_context_ids") or []),
            refresh_failed_context_ids=list((refresh_run or {}).get("failed_context_ids") or []),
            refresh_skipped_context_ids=list((refresh_run or {}).get("skipped_context_ids") or []),
            refresh_changed_contexts=list((refresh_run or {}).get("changed_contexts") or []),
            used_active_memory=assembled["used_active_memory"],
            active_memory_id=int(active_memory.get("memory_id") or 0)
            if active_memory
            else None,
            active_memory_title=str(active_memory.get("title") or "").strip() or None
            if active_memory
            else None,
            active_memory_updated_at=str(active_memory.get("updated_at") or "").strip()
            or None
            if active_memory
            else None,
            active_memory_version=int(active_memory.get("version") or 0)
            if active_memory
            else None,
            used_active_compression=assembled["used_active_compression"],
            active_compression_id=int(active_compression.get("compression_id") or 0)
            if active_compression
            else None,
            active_compression_title=str(active_compression.get("title") or "").strip()
            or None
            if active_compression
            else None,
            active_compression_updated_at=str(
                active_compression.get("updated_at") or ""
            ).strip()
            or None
            if active_compression
            else None,
            active_compression_version=int(active_compression.get("version") or 0)
            if active_compression
            else None,
            active_compression_covered_until_message_id=str(
                active_compression.get("covered_until_message_id") or ""
            ).strip()
            or None
            if active_compression
            else None,
            active_compression_covered_message_count=int(
                active_compression.get("covered_message_count") or 0
            )
            if active_compression
            else None,
            recent_raw_message_count=int(compression_state["recent_raw_message_count"] or 0),
            compression_recommended=bool(compression_state["compression_recommended"]),
            compression_reason=str(compression_state.get("compression_reason") or "").strip()
            or None,
            uncompressed_message_count=int(
                compression_state["uncompressed_message_count"] or 0
            ),
            estimated_history_size=int(compression_state["estimated_history_size"] or 0),
            active_compression_stale=bool(compression_state["active_compression_stale"]),
            question_intent=question_routing.question_intent,
            response_strategy=question_routing.response_strategy,
            routing_reason=question_routing.routing_reason,
            recommended_next_action=question_routing.recommended_next_action,
            followup_candidates=question_routing.followup_candidates,
            suggested_task_titles=question_routing.suggested_task_titles,
            user_message=self._serialize_message_item(user_item),
            assistant_message=self._serialize_message_item(assistant_item),
        )

    async def save_temporary_evidence_as_context(
        self,
        *,
        user_id: str,
        thread_id: int,
        message_id: str,
        evidence_index: int,
        pin: bool = False,
        custom_title: str | None = None,
    ) -> dict[str, Any] | None:
        thread_obj = self.stock_analysis_workspace_service.stock_analysis_thread_repository.get_thread_by_id(
            user_id=user_id,
            thread_id=thread_id,
        )
        if thread_obj is None:
            return None
        history_items = await self.conversation_service.core_conversation_service.get_conversation_items(
            conversation_id=thread_obj.conversation_id,
            limit=MESSAGE_LIMIT,
        )
        target_item = next(
            (
                item
                for item in history_items
                if getattr(item, "item_id", "") == message_id
                and str(getattr(item, "event", "")) == str(NotifyResponseEvent.MESSAGE)
            ),
            None,
        )
        if target_item is None:
            return None
        serialized_item = self._serialize_message_item(target_item)
        role_value = str(serialized_item.get("role") or "").lower()
        if not any(token in role_value for token in ("agent", "assistant")):
            return None
        evidence_blocks = list(serialized_item.get("temporary_evidence_blocks") or [])
        if evidence_index < 0 or evidence_index >= len(evidence_blocks):
            return None
        evidence_block = dict(evidence_blocks[evidence_index] or {})
        created = await self.stock_analysis_workspace_service.create_context_card(
            user_id=user_id,
            thread_id=thread_id,
            context_type=TEMPORARY_EVIDENCE_SAVED_CONTEXT_TYPE,
            title=(custom_title or evidence_block.get("title") or "临时证据").strip(),
            subtitle=self._build_saved_evidence_subtitle(evidence_block),
            ticker_refs_json=evidence_block.get("ticker_refs_json") or [],
            theme_refs_json=evidence_block.get("theme_refs_json") or [],
            summary=str(evidence_block.get("summary") or "").strip() or "临时证据摘要",
            snapshot_payload_json={
                "origin_message_id": message_id,
                "origin_evidence_index": evidence_index,
                "from_temporary_evidence": True,
                "evidence_type": evidence_block.get("type"),
                "source_label": evidence_block.get("source_label"),
                "source_module": evidence_block.get("source_module"),
                "is_external": bool(evidence_block.get("is_external")),
                "generated_at": evidence_block.get("generated_at")
                or serialized_item.get("evidence_generated_at"),
                "data_time": evidence_block.get("data_time")
                or serialized_item.get("evidence_generated_at"),
                "evidence_staleness_hint": evidence_block.get("staleness_hint")
                or serialized_item.get("evidence_staleness_hint"),
                "payload": evidence_block.get("payload") or {},
            },
            source_module=str(evidence_block.get("source_module") or "tooling_evidence"),
            source_ref=f"{message_id}:{evidence_index}",
            staleness_hint=(
                str(evidence_block.get("staleness_hint") or "").strip()
                or str(serialized_item.get("evidence_staleness_hint") or "").strip()
                or "该证据来自历史回答的临时补数，可能已过时。"
            ),
            is_pinned=pin,
            mode="replace",
        )
        return created

    async def _generate_answer(
        self,
        *,
        assembled_context: str,
        user_question: str,
        mode: str,
        tool_reason: str | None,
        tooling_result: StockAnalysisToolingResult,
    ) -> str:
        model = get_model_for_agent("research_agent")
        evidence_block = self._build_evidence_prompt_block(tooling_result)
        prompt = "\n\n".join(
            [
                "You are a stock analysis workspace assistant.",
                f"Current Mode: {mode}",
                assembled_context,
                "Temporary Evidence",
                evidence_block,
                "Current User Question",
                user_question,
                "Answer Requirements",
                (
                    "Answer in Chinese. Prioritize explicit reasoning. "
                    "Default to the current context. "
                    "If temporary evidence is present, treat it as temporary supplemental evidence only. "
                    "Do not claim any unavailable tool result. "
                    "If information is still insufficient, clearly say what is missing. "
                    f"Tool reason: {tool_reason or 'No tooling needed.'} "
                    f"Basis label to respect: {tooling_result.answer_basis}."
                ),
            ]
        )
        response = await Agent(model=model, markdown=True).arun(prompt)
        content = str(getattr(response, "content", "") or "").strip()
        if content:
            return content
        if mode == CONTEXT_ONLY_MODE:
            return "回答依据：当前上下文。当前上下文不足以支持更明确结论，请补充相关卡片后继续追问。"
        return (
            f"回答依据：{tooling_result.answer_basis}。"
            "本轮已尝试补充临时证据，但仍缺少足够信息，请继续补充更具体的研究对象。"
        )

    @staticmethod
    def _build_evidence_prompt_block(tooling_result: StockAnalysisToolingResult) -> str:
        if not tooling_result.temporary_evidence_blocks and not tooling_result.unavailable_tools:
            return "No temporary evidence."
        parts: list[str] = []
        for block in tooling_result.temporary_evidence_blocks[:5]:
            parts.append(
                f"{block.get('title')}: {block.get('summary')} (temporary={block.get('temporary')})"
            )
        for item in tooling_result.unavailable_tools[:3]:
            parts.append(
                f"Unavailable {item.get('tool')}: {item.get('reason')}"
            )
        if tooling_result.evidence_summary:
            parts.append(f"Evidence Summary: {tooling_result.evidence_summary}")
        return "\n".join(parts)

    @staticmethod
    def _serialize_message_item(item: Any | None) -> dict[str, Any]:
        if item is None:
            return {
                "item_id": "",
                "role": "",
                "content": "",
                "answer_basis": "当前上下文",
                "mode": CONTEXT_ONLY_MODE,
                "used_context_ids": [],
                "missing_context_hints": [],
                "compared_tickers": [],
                "comparison_mode": False,
                "stale_context_ids": [],
                "refresh_recommended_context_ids": [],
                "tool_reason": None,
                "tool_calls_summary": [],
                "temporary_evidence_blocks": [],
                "unavailable_tools": [],
                "used_internal_sources": [],
                "used_external_sources": [],
                "provider_attempts": [],
                "provider_used": [],
                "provider_fallback_chain": [],
                "evidence_generated_at": None,
                "evidence_staleness_hint": None,
                "refreshed_before_answer": False,
                "refresh_run_summary": None,
                "refreshed_context_ids": [],
                "refresh_failed_context_ids": [],
                "refresh_skipped_context_ids": [],
                "refresh_changed_contexts": [],
                "used_active_memory": False,
                "active_memory_id": None,
                "active_memory_title": None,
                "active_memory_updated_at": None,
                "active_memory_version": None,
                "used_active_compression": False,
                "active_compression_id": None,
                "active_compression_title": None,
                "active_compression_updated_at": None,
                "active_compression_version": None,
                "active_compression_covered_until_message_id": None,
                "active_compression_covered_message_count": None,
                "recent_raw_message_count": 0,
                "compression_recommended": False,
                "compression_reason": None,
                "uncompressed_message_count": 0,
                "estimated_history_size": 0,
                "active_compression_stale": False,
                "question_intent": None,
                "response_strategy": None,
                "routing_reason": None,
                "recommended_next_action": None,
                "followup_candidates": [],
                "suggested_task_titles": [],
            }
        metadata = StockAnalysisMessageService._parse_metadata(item.metadata)
        payload = StockAnalysisMessageService._parse_payload(item.payload)
        return {
            "item_id": item.item_id,
            "role": str(item.role),
            "event": str(item.event),
            "conversation_id": item.conversation_id,
            "content": payload.get("content") or "",
            "answer_basis": metadata.get("answer_basis") or "当前上下文",
            "mode": metadata.get("mode") or CONTEXT_ONLY_MODE,
            "used_context_ids": StockAnalysisMessageService._parse_json_list(
                metadata.get("used_context_ids_json")
            ),
            "missing_context_hints": StockAnalysisMessageService._parse_json_list(
                metadata.get("missing_context_hints_json")
            ),
            "compared_tickers": StockAnalysisMessageService._parse_json_list(
                metadata.get("compared_tickers_json")
            ),
            "comparison_mode": StockAnalysisMessageService._parse_bool(
                metadata.get("comparison_mode")
            ),
            "stale_context_ids": StockAnalysisMessageService._parse_json_list(
                metadata.get("stale_context_ids_json")
            ),
            "refresh_recommended_context_ids": StockAnalysisMessageService._parse_json_list(
                metadata.get("refresh_recommended_context_ids_json")
            ),
            "tool_reason": str(metadata.get("tool_reason") or "").strip() or None,
            "tool_calls_summary": StockAnalysisMessageService._parse_json_list(
                metadata.get("tool_calls_summary_json")
            ),
            "temporary_evidence_blocks": StockAnalysisMessageService._parse_json_list(
                metadata.get("temporary_evidence_blocks_json")
            ),
            "unavailable_tools": StockAnalysisMessageService._parse_json_list(
                metadata.get("unavailable_tools_json")
            ),
            "used_internal_sources": StockAnalysisMessageService._parse_json_list(
                metadata.get("used_internal_sources_json")
            ),
            "used_external_sources": StockAnalysisMessageService._parse_json_list(
                metadata.get("used_external_sources_json")
            ),
            "provider_attempts": StockAnalysisMessageService._parse_json_list(
                metadata.get("provider_attempts_json")
            ),
            "provider_used": StockAnalysisMessageService._parse_json_list(
                metadata.get("provider_used_json")
            ),
            "provider_fallback_chain": StockAnalysisMessageService._parse_json_list(
                metadata.get("provider_fallback_chain_json")
            ),
            "evidence_generated_at": str(metadata.get("evidence_generated_at") or "").strip()
            or None,
            "evidence_staleness_hint": str(
                metadata.get("evidence_staleness_hint") or ""
            ).strip()
            or None,
            "refreshed_before_answer": StockAnalysisMessageService._parse_bool(
                metadata.get("refreshed_before_answer")
            ),
            "refresh_run_summary": str(metadata.get("refresh_run_summary") or "").strip()
            or None,
            "refreshed_context_ids": StockAnalysisMessageService._parse_json_list(
                metadata.get("refreshed_context_ids_json")
            ),
            "refresh_failed_context_ids": StockAnalysisMessageService._parse_json_list(
                metadata.get("refresh_failed_context_ids_json")
            ),
            "refresh_skipped_context_ids": StockAnalysisMessageService._parse_json_list(
                metadata.get("refresh_skipped_context_ids_json")
            ),
            "refresh_changed_contexts": StockAnalysisMessageService._parse_json_list(
                metadata.get("refresh_changed_contexts_json")
            ),
            "used_active_memory": StockAnalysisMessageService._parse_bool(
                metadata.get("used_active_memory")
            ),
            "active_memory_id": StockAnalysisMessageService._parse_optional_int(
                metadata.get("active_memory_id")
            ),
            "active_memory_title": str(metadata.get("active_memory_title") or "").strip()
            or None,
            "active_memory_updated_at": str(
                metadata.get("active_memory_updated_at") or ""
            ).strip()
            or None,
            "active_memory_version": StockAnalysisMessageService._parse_optional_int(
                metadata.get("active_memory_version")
            ),
            "used_active_compression": StockAnalysisMessageService._parse_bool(
                metadata.get("used_active_compression")
            ),
            "active_compression_id": StockAnalysisMessageService._parse_optional_int(
                metadata.get("active_compression_id")
            ),
            "active_compression_title": str(
                metadata.get("active_compression_title") or ""
            ).strip()
            or None,
            "active_compression_updated_at": str(
                metadata.get("active_compression_updated_at") or ""
            ).strip()
            or None,
            "active_compression_version": StockAnalysisMessageService._parse_optional_int(
                metadata.get("active_compression_version")
            ),
            "active_compression_covered_until_message_id": str(
                metadata.get("active_compression_covered_until_message_id") or ""
            ).strip()
            or None,
            "active_compression_covered_message_count": StockAnalysisMessageService._parse_optional_int(
                metadata.get("active_compression_covered_message_count")
            ),
            "recent_raw_message_count": int(
                StockAnalysisMessageService._parse_optional_int(
                    metadata.get("recent_raw_message_count")
                )
                or 0
            ),
            "compression_recommended": StockAnalysisMessageService._parse_bool(
                metadata.get("compression_recommended")
            ),
            "compression_reason": str(metadata.get("compression_reason") or "").strip()
            or None,
            "uncompressed_message_count": int(
                StockAnalysisMessageService._parse_optional_int(
                    metadata.get("uncompressed_message_count")
                )
                or 0
            ),
            "estimated_history_size": int(
                StockAnalysisMessageService._parse_optional_int(
                    metadata.get("estimated_history_size")
                )
                or 0
            ),
            "active_compression_stale": StockAnalysisMessageService._parse_bool(
                metadata.get("active_compression_stale")
            ),
            "question_intent": str(metadata.get("question_intent") or "").strip() or None,
            "response_strategy": str(metadata.get("response_strategy") or "").strip()
            or None,
            "routing_reason": str(metadata.get("routing_reason") or "").strip()
            or None,
            "recommended_next_action": str(
                metadata.get("recommended_next_action") or ""
            ).strip()
            or None,
            "followup_candidates": StockAnalysisMessageService._parse_json_list(
                metadata.get("followup_candidates_json")
            ),
            "suggested_task_titles": StockAnalysisMessageService._parse_json_list(
                metadata.get("suggested_task_titles_json")
            ),
        }

    @staticmethod
    def _build_saved_evidence_subtitle(evidence_block: dict[str, Any]) -> str | None:
        source_label = str(evidence_block.get("source_label") or "").strip()
        data_time = str(evidence_block.get("data_time") or evidence_block.get("generated_at") or "").strip()
        subtitle_parts = [part for part in (source_label, data_time) if part]
        return " · ".join(subtitle_parts) if subtitle_parts else None

    @staticmethod
    def _parse_payload(raw_payload: str) -> dict[str, Any]:
        try:
            return json.loads(raw_payload or "{}")
        except json.JSONDecodeError:
            return {"content": raw_payload or ""}

    @staticmethod
    def _parse_metadata(raw_metadata: str) -> dict[str, Any]:
        try:
            return json.loads(raw_metadata or "{}")
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
    def _parse_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        text = str(value or "").strip().lower()
        return text in {"1", "true", "yes", "on"}

    @staticmethod
    def _parse_optional_int(value: Any) -> int | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        try:
            parsed = int(text)
        except ValueError:
            return None
        return parsed if parsed > 0 else None


_stock_analysis_message_service: Optional[StockAnalysisMessageService] = None


def get_stock_analysis_message_service() -> StockAnalysisMessageService:
    global _stock_analysis_message_service
    if _stock_analysis_message_service is None:
        _stock_analysis_message_service = StockAnalysisMessageService()
    return _stock_analysis_message_service


def reset_stock_analysis_message_service() -> None:
    global _stock_analysis_message_service
    _stock_analysis_message_service = None
