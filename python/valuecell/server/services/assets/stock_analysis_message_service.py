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
    evidence_generated_at: str | None = None
    evidence_staleness_hint: str | None = None
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
    ) -> None:
        self.stock_analysis_workspace_service = (
            stock_analysis_workspace_service or StockAnalysisWorkspaceService()
        )
        self.conversation_service = conversation_service or ConversationService()
        self.context_assembler = context_assembler or StockAnalysisContextAssembler()
        self.tool_planner = tool_planner or get_stock_analysis_tool_planner()
        self.tooling_service = tooling_service or get_stock_analysis_tooling_service()

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
    ) -> StockAnalysisMessageResult | None:
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
        assembled = self.context_assembler.assemble(
            thread=thread,
            context_cards=context_cards,
            user_question=message,
        )
        history_items = await self.conversation_service.core_conversation_service.get_conversation_items(
            conversation_id=thread_obj.conversation_id,
            limit=20,
        )
        history_messages = [
            self._serialize_message_item(item)
            for item in history_items
            if str(item.event) == str(NotifyResponseEvent.MESSAGE)
        ]
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
                "thread_id": thread_id,
            },
        )

        assistant_text = await self._generate_answer(
            assembled_context=assembled["prompt_context"],
            history_messages=history_messages,
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
            "evidence_generated_at": tooling_result.evidence_generated_at or "",
            "evidence_staleness_hint": tooling_result.evidence_staleness_hint or "",
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
            evidence_generated_at=tooling_result.evidence_generated_at,
            evidence_staleness_hint=tooling_result.evidence_staleness_hint,
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
        history_messages: list[dict[str, Any]],
        user_question: str,
        mode: str,
        tool_reason: str | None,
        tooling_result: StockAnalysisToolingResult,
    ) -> str:
        model = get_model_for_agent("research_agent")
        history_block = "\n".join(
            f"{item['role']}: {item['content']}"
            for item in history_messages[-8:]
            if str(item.get("content") or "").strip()
        )
        evidence_block = self._build_evidence_prompt_block(tooling_result)
        prompt = "\n\n".join(
            [
                "You are a stock analysis workspace assistant.",
                f"Current Mode: {mode}",
                assembled_context,
                "Conversation History",
                history_block or "No previous messages.",
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
                "evidence_generated_at": None,
                "evidence_staleness_hint": None,
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
            "evidence_generated_at": str(metadata.get("evidence_generated_at") or "").strip()
            or None,
            "evidence_staleness_hint": str(
                metadata.get("evidence_staleness_hint") or ""
            ).strip()
            or None,
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


_stock_analysis_message_service: Optional[StockAnalysisMessageService] = None


def get_stock_analysis_message_service() -> StockAnalysisMessageService:
    global _stock_analysis_message_service
    if _stock_analysis_message_service is None:
        _stock_analysis_message_service = StockAnalysisMessageService()
    return _stock_analysis_message_service


def reset_stock_analysis_message_service() -> None:
    global _stock_analysis_message_service
    _stock_analysis_message_service = None
