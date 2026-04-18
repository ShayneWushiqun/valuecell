from __future__ import annotations

import json
import datetime as dt
from typing import Any, Optional

from agno.agent import Agent
from pydantic import BaseModel

from valuecell.core.types import (
    BaseResponseDataPayload,
    NotifyResponseEvent,
    Role,
)
from valuecell.server.services.conversation_service import ConversationService
from valuecell.utils.model import get_model_for_agent

from .stock_analysis_context_assembler import StockAnalysisContextAssembler
from .stock_analysis_workspace_service import (
    DEFAULT_USER_ID,
    STOCK_ANALYSIS_AGENT_NAME,
    StockAnalysisWorkspaceService,
)

MESSAGE_LIMIT = 100


class StockAnalysisMessageResult(BaseModel):
    conversation_id: str
    thread_id: int
    answer_basis: str
    used_context_ids: list[int]
    missing_context_hints: list[str]
    user_message: dict[str, Any]
    assistant_message: dict[str, Any]


class StockAnalysisMessageService:
    def __init__(
        self,
        stock_analysis_workspace_service: Optional[StockAnalysisWorkspaceService] = None,
        conversation_service: Optional[ConversationService] = None,
        context_assembler: Optional[StockAnalysisContextAssembler] = None,
    ) -> None:
        self.stock_analysis_workspace_service = (
            stock_analysis_workspace_service or StockAnalysisWorkspaceService()
        )
        self.conversation_service = conversation_service or ConversationService()
        self.context_assembler = context_assembler or StockAnalysisContextAssembler()

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

        user_item = await self.conversation_service.core_conversation_service.add_item(
            role=Role.USER,
            event=NotifyResponseEvent.MESSAGE,
            conversation_id=thread_obj.conversation_id,
            payload=BaseResponseDataPayload(content=message.strip()),
            agent_name=STOCK_ANALYSIS_AGENT_NAME,
            metadata={
                "answer_basis": "context_only",
                "thread_id": thread_id,
            },
        )

        assistant_text = await self._generate_context_only_answer(
            assembled_context=assembled["prompt_context"],
            history_messages=history_messages,
            user_question=message.strip(),
        )
        assistant_metadata = {
            "answer_basis": "context_only",
            "used_context_ids_json": json.dumps(assembled["used_context_ids"], ensure_ascii=False),
            "missing_context_hints_json": json.dumps(
                assembled["missing_context_hints"], ensure_ascii=False
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
            answer_basis="context_only",
            used_context_ids=assembled["used_context_ids"],
            missing_context_hints=assembled["missing_context_hints"],
            user_message=self._serialize_message_item(user_item),
            assistant_message=self._serialize_message_item(assistant_item),
        )

    async def _generate_context_only_answer(
        self,
        *,
        assembled_context: str,
        history_messages: list[dict[str, Any]],
        user_question: str,
    ) -> str:
        model = get_model_for_agent("research_agent")
        history_block = "\n".join(
            f"{item['role']}: {item['content']}"
            for item in history_messages[-8:]
            if str(item.get("content") or "").strip()
        )
        prompt = "\n\n".join(
            [
                "You are a stock analysis workspace assistant in context_only mode.",
                assembled_context,
                "Conversation History",
                history_block or "No previous messages.",
                "Current User Question",
                user_question,
                "Answer Requirements",
                (
                    "Answer in Chinese. Explain your reasoning briefly and concretely. "
                    "Do not claim any external data or tools. "
                    "If the context is insufficient, explicitly say what is missing. "
                    "State that the basis is the current context."
                ),
            ]
        )
        response = await Agent(model=model, markdown=True).arun(prompt)
        content = str(getattr(response, "content", "") or "").strip()
        if content:
            return content
        return "回答依据：当前上下文。当前上下文不足以支持更明确结论，请补充相关卡片后继续追问。"

    @staticmethod
    def _serialize_message_item(item: Any | None) -> dict[str, Any]:
        if item is None:
            return {
                "item_id": "",
                "role": "",
                "content": "",
                "answer_basis": "context_only",
                "used_context_ids": [],
                "missing_context_hints": [],
            }
        metadata = StockAnalysisMessageService._parse_metadata(item.metadata)
        payload = StockAnalysisMessageService._parse_payload(item.payload)
        return {
            "item_id": item.item_id,
            "role": str(item.role),
            "event": str(item.event),
            "conversation_id": item.conversation_id,
            "content": payload.get("content") or "",
            "answer_basis": metadata.get("answer_basis") or "context_only",
            "used_context_ids": StockAnalysisMessageService._parse_json_list(
                metadata.get("used_context_ids_json")
            ),
            "missing_context_hints": StockAnalysisMessageService._parse_json_list(
                metadata.get("missing_context_hints_json")
            ),
        }

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


_stock_analysis_message_service: Optional[StockAnalysisMessageService] = None


def get_stock_analysis_message_service() -> StockAnalysisMessageService:
    global _stock_analysis_message_service
    if _stock_analysis_message_service is None:
        _stock_analysis_message_service = StockAnalysisMessageService()
    return _stock_analysis_message_service


def reset_stock_analysis_message_service() -> None:
    global _stock_analysis_message_service
    _stock_analysis_message_service = None
