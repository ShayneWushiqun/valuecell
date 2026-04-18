from __future__ import annotations

from typing import Any, cast

import pytest

from valuecell.core.types import BaseResponseDataPayload, NotifyResponseEvent, Role
from valuecell.server.services.assets.stock_analysis_thread_memory_service import (
    StockAnalysisThreadMemoryService,
)
from valuecell.server.services.assets.stock_analysis_workspace_service import (
    StockAnalysisWorkspaceService,
)
from valuecell.server.services.tests.test_stock_analysis_message_service import (
    FakeConversationServiceForMessages,
)
from valuecell.server.services.tests.test_stock_analysis_thread_service import (
    FakeContextRepository,
    FakeThreadMemoryRepository,
    FakeThreadRepository,
)


async def _seed_thread_with_messages(
    *,
    conversation_service: FakeConversationServiceForMessages,
    conversation_id: str,
) -> None:
    await conversation_service.core_conversation_service.add_item(
        role=Role.USER,
        event=NotifyResponseEvent.MESSAGE,
        conversation_id=conversation_id,
        payload=BaseResponseDataPayload(content="比较这两只票谁更优先。"),
        metadata={"thread_id": 1},
    )
    await conversation_service.core_conversation_service.add_item(
        role=Role.AGENT,
        event=NotifyResponseEvent.MESSAGE,
        conversation_id=conversation_id,
        payload=BaseResponseDataPayload(content="当前先看主线强度与上下文刷新状态。"),
        metadata={
            "missing_context_hints_json": '["latest_price_action"]',
            "refresh_run_summary": "已刷新 1 张上下文卡片。",
            "temporary_evidence_blocks_json": '[{"title":"行情补充"}]',
            "thread_id": 1,
        },
    )


@pytest.mark.asyncio
async def test_stock_analysis_thread_memory_service_capture_success() -> None:
    conversation_service = FakeConversationServiceForMessages()
    memory_repository = FakeThreadMemoryRepository()
    workspace_service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        stock_analysis_thread_memory_repository=cast(Any, memory_repository),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        conversation_service=cast(Any, conversation_service),
    )
    thread = await workspace_service.create_thread(
        user_id="default_user",
        title="AI 算力对比",
        focus_type="comparison",
        compare_targets_json=[
            {
                "target_type": "ticker",
                "ref": "SZSE:300308",
                "label": "中军",
                "source_module": "holding",
                "source_ref": "1",
                "role": "primary",
                "order": 0,
            },
            {
                "target_type": "ticker",
                "ref": "SHSE:603019",
                "label": "候选",
                "source_module": "opportunity",
                "source_ref": "SHSE:603019",
                "role": "secondary",
                "order": 1,
            },
        ],
    )
    await workspace_service.create_context_card(
        user_id="default_user",
        thread_id=thread["thread_id"],
        context_type="ticker",
        title="中军卡片",
        summary="当前仍是主线核心。",
        ticker_refs_json=["SZSE:300308"],
        source_module="ticker",
        source_ref="SZSE:300308",
        is_pinned=True,
    )
    await workspace_service.create_context_card(
        user_id="default_user",
        thread_id=thread["thread_id"],
        context_type="ticker",
        title="候选卡片",
        summary="承接仍待确认。",
        ticker_refs_json=["SHSE:603019"],
        snapshot_payload_json={"generated_at": "2026-04-10T09:00:00+00:00"},
        source_module="ticker",
        source_ref="SHSE:603019",
    )
    await _seed_thread_with_messages(
        conversation_service=conversation_service,
        conversation_id=thread["conversation_id"],
    )
    service = StockAnalysisThreadMemoryService(
        stock_analysis_workspace_service=workspace_service,
        stock_analysis_thread_memory_repository=cast(Any, memory_repository),
        conversation_service=cast(Any, conversation_service),
    )

    result = await service.capture_memory(
        user_id="default_user",
        thread_id=thread["thread_id"],
    )
    memory_list = await service.list_memories(
        user_id="default_user",
        thread_id=thread["thread_id"],
    )

    assert result is not None
    assert result["is_active"] is True
    assert result["compared_tickers_json"] == ["SZSE:300308", "SHSE:603019"]
    assert result["linked_context_count"] == 2
    assert result["compare_target_count"] == 2
    assert result["summary"]
    assert memory_list is not None
    assert memory_list["active_memory"] is not None
    assert memory_list["count"] == 1


@pytest.mark.asyncio
async def test_stock_analysis_thread_memory_service_falls_back_when_synthesis_fails(
    monkeypatch,
) -> None:
    conversation_service = FakeConversationServiceForMessages()
    memory_repository = FakeThreadMemoryRepository()
    workspace_service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        stock_analysis_thread_memory_repository=cast(Any, memory_repository),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        conversation_service=cast(Any, conversation_service),
    )
    thread = await workspace_service.create_thread(
        user_id="default_user",
        title="fallback 测试",
        focus_type="ticker",
        ticker_refs_json=["SZSE:300308"],
    )
    await _seed_thread_with_messages(
        conversation_service=conversation_service,
        conversation_id=thread["conversation_id"],
    )
    service = StockAnalysisThreadMemoryService(
        stock_analysis_workspace_service=workspace_service,
        stock_analysis_thread_memory_repository=cast(Any, memory_repository),
        conversation_service=cast(Any, conversation_service),
    )
    monkeypatch.setattr(
        service,
        "_build_memory_payload",
        lambda **_: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    result = await service.capture_memory(
        user_id="default_user",
        thread_id=thread["thread_id"],
    )

    assert result is not None
    assert result["summary"]
    assert result["source_snapshot_json"]["reason"] == "capture:fallback"


@pytest.mark.asyncio
async def test_stock_analysis_thread_memory_service_activate_keeps_only_one_active() -> None:
    conversation_service = FakeConversationServiceForMessages()
    memory_repository = FakeThreadMemoryRepository()
    workspace_service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        stock_analysis_thread_memory_repository=cast(Any, memory_repository),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        conversation_service=cast(Any, conversation_service),
    )
    thread = await workspace_service.create_thread(
        user_id="default_user",
        title="激活测试",
        focus_type="ticker",
        ticker_refs_json=["SZSE:300308"],
    )
    service = StockAnalysisThreadMemoryService(
        stock_analysis_workspace_service=workspace_service,
        stock_analysis_thread_memory_repository=cast(Any, memory_repository),
        conversation_service=cast(Any, conversation_service),
    )
    first = memory_repository.create_memory(
        {
            "thread_id": thread["thread_id"],
            "user_id": "default_user",
            "title": "v1",
            "summary": "v1",
            "stance": "继续观察",
            "confidence": 0.4,
            "time_horizon": "短线",
            "focus_tickers_json": ["SZSE:300308"],
            "focus_themes_json": [],
            "compared_tickers_json": [],
            "support_points_json": ["a"],
            "opposing_points_json": [],
            "risk_points_json": [],
            "key_uncertainties_json": [],
            "invalidation_conditions_json": [],
            "next_questions_json": [],
            "next_data_to_check_json": [],
            "linked_context_ids_json": [],
            "linked_message_ids_json": [],
            "linked_compare_targets_json": [],
            "source_snapshot_json": {},
            "is_active": True,
        }
    )
    second = memory_repository.create_memory(
        {
            "thread_id": thread["thread_id"],
            "user_id": "default_user",
            "title": "v2",
            "summary": "v2",
            "stance": "继续观察",
            "confidence": 0.5,
            "time_horizon": "短线",
            "focus_tickers_json": ["SZSE:300308"],
            "focus_themes_json": [],
            "compared_tickers_json": [],
            "support_points_json": ["b"],
            "opposing_points_json": [],
            "risk_points_json": [],
            "key_uncertainties_json": [],
            "invalidation_conditions_json": [],
            "next_questions_json": [],
            "next_data_to_check_json": [],
            "linked_context_ids_json": [],
            "linked_message_ids_json": [],
            "linked_compare_targets_json": [],
            "source_snapshot_json": {},
            "is_active": False,
        }
    )

    result = await service.activate_memory(
        user_id="default_user",
        thread_id=thread["thread_id"],
        memory_id=int(second.id),
    )

    assert result is not None
    assert result["memory_id"] == int(second.id)
    assert memory_repository.get_memory_by_id(
        user_id="default_user",
        thread_id=thread["thread_id"],
        memory_id=int(first.id),
    ).is_active is False
    assert memory_repository.get_memory_by_id(
        user_id="default_user",
        thread_id=thread["thread_id"],
        memory_id=int(second.id),
    ).is_active is True


@pytest.mark.asyncio
async def test_stock_analysis_thread_memory_service_refresh_creates_new_active_version() -> None:
    conversation_service = FakeConversationServiceForMessages()
    memory_repository = FakeThreadMemoryRepository()
    workspace_service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        stock_analysis_thread_memory_repository=cast(Any, memory_repository),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        conversation_service=cast(Any, conversation_service),
    )
    thread = await workspace_service.create_thread(
        user_id="default_user",
        title="刷新记忆",
        focus_type="ticker",
        ticker_refs_json=["SZSE:300308"],
    )
    await workspace_service.create_context_card(
        user_id="default_user",
        thread_id=thread["thread_id"],
        context_type="ticker",
        title="基础卡片",
        summary="仍需等待确认。",
        ticker_refs_json=["SZSE:300308"],
        source_module="ticker",
        source_ref="SZSE:300308",
    )
    await _seed_thread_with_messages(
        conversation_service=conversation_service,
        conversation_id=thread["conversation_id"],
    )
    service = StockAnalysisThreadMemoryService(
        stock_analysis_workspace_service=workspace_service,
        stock_analysis_thread_memory_repository=cast(Any, memory_repository),
        conversation_service=cast(Any, conversation_service),
    )
    first = await service.capture_memory(
        user_id="default_user",
        thread_id=thread["thread_id"],
    )

    refreshed = await service.refresh_memory(
        user_id="default_user",
        thread_id=thread["thread_id"],
        memory_id=int(first["memory_id"]),
    )
    memory_list = await service.list_memories(
        user_id="default_user",
        thread_id=thread["thread_id"],
    )

    assert refreshed is not None
    assert refreshed["memory_id"] != first["memory_id"]
    assert refreshed["is_active"] is True
    assert memory_list is not None
    assert memory_list["count"] == 2
    assert memory_list["active_memory"]["memory_id"] == refreshed["memory_id"]
