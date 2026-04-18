from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, cast

import pytest

from valuecell.core.types import NotifyResponseEvent, Role
from valuecell.server.services.assets.stock_analysis_message_service import (
    StockAnalysisMessageService,
)
from valuecell.server.services.assets.stock_analysis_workspace_service import (
    StockAnalysisWorkspaceService,
)
from valuecell.server.services.tests.test_stock_analysis_thread_service import (
    FakeContextRepository,
    FakeConversationService,
    FakeThreadRepository,
)


@dataclass
class FakeConversationItem:
    item_id: str
    role: str
    event: str
    conversation_id: str
    payload: str
    metadata: str


class FakeCoreConversationService:
    def __init__(self) -> None:
        self.items_by_conversation: dict[str, list[FakeConversationItem]] = {}
        self.next_id = 1

    async def add_item(
        self,
        *,
        role: str,
        event: str,
        conversation_id: str,
        payload: Any,
        agent_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FakeConversationItem:
        payload_json = payload.model_dump_json() if hasattr(payload, "model_dump_json") else json.dumps(payload)
        item = FakeConversationItem(
            item_id=f"item_{self.next_id}",
            role=role,
            event=event,
            conversation_id=conversation_id,
            payload=payload_json,
            metadata=json.dumps(metadata or {}, ensure_ascii=False),
        )
        self.next_id += 1
        self.items_by_conversation.setdefault(conversation_id, []).append(item)
        return item

    async def get_conversation_items(self, *, conversation_id: str, limit: int = 100):
        return self.items_by_conversation.get(conversation_id, [])[-limit:]


class FakeConversationServiceForMessages(FakeConversationService):
    def __init__(self) -> None:
        super().__init__()
        self.core_conversation_service = FakeCoreConversationService()


async def _fake_answer(*, assembled_context: str, history_messages, user_question: str) -> str:
    return "回答依据：当前上下文。当前先看已挂载卡片。"


@pytest.mark.asyncio
async def test_stock_analysis_message_service_reads_thread_conversation_and_persists_history(
    monkeypatch,
) -> None:
    conversation_service = FakeConversationServiceForMessages()
    workspace_service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        conversation_service=cast(Any, conversation_service),
    )
    thread = await workspace_service.create_thread(
        user_id="default_user",
        title="消息测试",
        focus_type="ticker",
        ticker_refs_json=["SZSE:300308"],
    )
    await workspace_service.create_context_card(
        user_id="default_user",
        thread_id=thread["thread_id"],
        context_type="ticker",
        title="中际旭创基础观察卡",
        summary="仅基于当前上下文回答。",
        source_module="ticker",
        source_ref="SZSE:300308",
    )
    service = StockAnalysisMessageService(
        stock_analysis_workspace_service=workspace_service,
        conversation_service=cast(Any, conversation_service),
    )
    monkeypatch.setattr(
        service,
        "_generate_context_only_answer",
        _fake_answer,
    )

    result = await service.send_message(
        user_id="default_user",
        thread_id=thread["thread_id"],
        message="请基于当前上下文评价中际旭创。",
    )
    history = await service.list_messages(
        user_id="default_user",
        thread_id=thread["thread_id"],
    )

    assert result is not None
    assert result.conversation_id == thread["conversation_id"]
    assert result.answer_basis == "context_only"
    assert history is not None
    assert history["count"] == 2
    assert history["items"][0]["role"] in {str(Role.USER), "user"}
    assert history["items"][1]["answer_basis"] == "context_only"


@pytest.mark.asyncio
async def test_stock_analysis_message_service_keeps_context_only_without_external_tooling(
    monkeypatch,
) -> None:
    conversation_service = FakeConversationServiceForMessages()
    workspace_service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        conversation_service=cast(Any, conversation_service),
    )
    thread = await workspace_service.create_thread(
        user_id="default_user",
        title="context only",
        focus_type="mixed",
    )
    service = StockAnalysisMessageService(
        stock_analysis_workspace_service=workspace_service,
        conversation_service=cast(Any, conversation_service),
    )

    called = {"count": 0}

    async def fake_answer(*, assembled_context: str, history_messages, user_question: str) -> str:
        called["count"] += 1
        return "回答依据：当前上下文。缺少更多卡片。"

    monkeypatch.setattr(service, "_generate_context_only_answer", fake_answer)

    result = await service.send_message(
        user_id="default_user",
        thread_id=thread["thread_id"],
        message="在没有更多数据时该怎么理解？",
    )

    assert called["count"] == 1
    assert result is not None
    assert result.answer_basis == "context_only"


@pytest.mark.asyncio
async def test_stock_analysis_message_service_switches_history_by_thread(monkeypatch) -> None:
    conversation_service = FakeConversationServiceForMessages()
    workspace_service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        conversation_service=cast(Any, conversation_service),
    )
    thread_a = await workspace_service.create_thread(
        user_id="default_user",
        title="线程 A",
        focus_type="ticker",
        ticker_refs_json=["SZSE:300308"],
    )
    thread_b = await workspace_service.create_thread(
        user_id="default_user",
        title="线程 B",
        focus_type="ticker",
        ticker_refs_json=["SZSE:000001"],
    )
    service = StockAnalysisMessageService(
        stock_analysis_workspace_service=workspace_service,
        conversation_service=cast(Any, conversation_service),
    )
    monkeypatch.setattr(
        service,
        "_generate_context_only_answer",
        _fake_answer,
    )

    await service.send_message(
        user_id="default_user",
        thread_id=thread_a["thread_id"],
        message="线程 A 问题",
    )
    await service.send_message(
        user_id="default_user",
        thread_id=thread_b["thread_id"],
        message="线程 B 问题",
    )
    history_a = await service.list_messages(
        user_id="default_user",
        thread_id=thread_a["thread_id"],
    )
    history_b = await service.list_messages(
        user_id="default_user",
        thread_id=thread_b["thread_id"],
    )

    assert history_a is not None and history_b is not None
    assert history_a["conversation_id"] != history_b["conversation_id"]
    assert "线程 A 问题" in history_a["items"][0]["content"]
    assert "线程 B 问题" in history_b["items"][0]["content"]
