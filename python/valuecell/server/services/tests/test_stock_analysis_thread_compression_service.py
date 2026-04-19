from __future__ import annotations

from typing import Any, cast

import pytest

from valuecell.core.types import BaseResponseDataPayload, NotifyResponseEvent, Role
from valuecell.server.services.assets.stock_analysis_thread_compression_service import (
    StockAnalysisThreadCompressionService,
)
from valuecell.server.services.assets.stock_analysis_workspace_service import (
    StockAnalysisWorkspaceService,
)
from valuecell.server.services.tests.test_stock_analysis_message_service import (
    FakeConversationServiceForMessages,
)
from valuecell.server.services.tests.test_stock_analysis_thread_service import (
    FakeContextRepository,
    FakeThreadCompressionRepository,
    FakeThreadMemoryRepository,
    FakeThreadRepository,
)


class FakeMemoryProxy:
    def __init__(self, active_memory: dict[str, Any] | None = None) -> None:
        self.active_memory = active_memory

    async def get_active_memory(self, *, user_id: str, thread_id: int):
        del user_id, thread_id
        return self.active_memory


async def _seed_messages(
    *,
    conversation_service: FakeConversationServiceForMessages,
    conversation_id: str,
    count: int = 6,
) -> None:
    for index in range(count):
        await conversation_service.core_conversation_service.add_item(
            role=Role.USER,
            event=NotifyResponseEvent.MESSAGE,
            conversation_id=conversation_id,
            payload=BaseResponseDataPayload(content=f"用户问题 {index}"),
            metadata={"thread_id": 1},
        )
        await conversation_service.core_conversation_service.add_item(
            role=Role.AGENT,
            event=NotifyResponseEvent.MESSAGE,
            conversation_id=conversation_id,
            payload=BaseResponseDataPayload(content=f"回答 {index}"),
            metadata={
                "thread_id": 1,
                "refresh_run_summary": "已刷新 1 张上下文卡片。" if index == count - 1 else "",
                "tool_calls_summary_json": '["补最近 5 日日线价格"]' if index == count - 1 else "[]",
                "temporary_evidence_blocks_json": (
                    '[{"title":"行情补充","summary":"补最近 5 日日线价格"}]'
                    if index == count - 1
                    else "[]"
                ),
                "compared_tickers_json": '["SZSE:300308","SHSE:603019"]'
                if index == count - 1
                else "[]",
                "missing_context_hints_json": '["latest_price_action"]'
                if index == count - 1
                else "[]",
            },
        )


@pytest.mark.asyncio
async def test_stock_analysis_thread_compression_service_capture_success() -> None:
    conversation_service = FakeConversationServiceForMessages()
    compression_repository = FakeThreadCompressionRepository()
    memory_repository = FakeThreadMemoryRepository()
    workspace_service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        stock_analysis_thread_memory_repository=cast(Any, memory_repository),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        conversation_service=cast(Any, conversation_service),
    )
    thread = await workspace_service.create_thread(
        user_id="default_user",
        title="压缩测试",
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
                "source_ref": "2",
                "role": "secondary",
                "order": 1,
            },
        ],
    )
    memory_repository.create_memory(
        {
            "thread_id": thread["thread_id"],
            "user_id": "default_user",
            "title": "当前研究记忆",
            "summary": "当前仍优先看主线。",
            "stance": "比较观察",
            "confidence": 0.62,
            "time_horizon": "短线到波段",
            "focus_tickers_json": ["SZSE:300308", "SHSE:603019"],
            "focus_themes_json": ["AI算力"],
            "compared_tickers_json": ["SZSE:300308", "SHSE:603019"],
            "support_points_json": ["主线仍清晰。"],
            "opposing_points_json": [],
            "risk_points_json": ["需防波动。"],
            "key_uncertainties_json": ["最新价格动作未确认。"],
            "invalidation_conditions_json": ["刷新后若摘要变化则失效。"],
            "next_questions_json": ["刷新后谁更优先？"],
            "next_data_to_check_json": ["最新价格动作"],
            "linked_context_ids_json": [],
            "linked_message_ids_json": [],
            "linked_compare_targets_json": thread["compare_targets_json"],
            "source_snapshot_json": {},
            "is_active": True,
        }
    )
    await _seed_messages(
        conversation_service=conversation_service,
        conversation_id=thread["conversation_id"],
    )
    service = StockAnalysisThreadCompressionService(
        stock_analysis_workspace_service=workspace_service,
        stock_analysis_thread_compression_repository=cast(Any, compression_repository),
        stock_analysis_thread_memory_service=FakeMemoryProxy(
            memory_repository.get_active_memory(
                user_id="default_user",
                thread_id=thread["thread_id"],
            ).to_dict()
        ),
        conversation_service=cast(Any, conversation_service),
    )

    result = await service.capture_compression(
        user_id="default_user",
        thread_id=thread["thread_id"],
    )
    listed = await service.list_compressions(
        user_id="default_user",
        thread_id=thread["thread_id"],
    )

    assert result is not None
    assert result["is_active"] is True
    assert result["covered_message_count"] == 12
    assert result["active_memory_id"] is not None
    assert result["recent_refresh_notes_json"]
    assert result["recent_tooling_notes_json"]
    assert result["recent_evidence_notes_json"]
    assert listed is not None
    assert listed["active_compression"] is not None
    assert listed["count"] == 1


@pytest.mark.asyncio
async def test_stock_analysis_thread_compression_service_capture_fallback(
    monkeypatch,
) -> None:
    conversation_service = FakeConversationServiceForMessages()
    compression_repository = FakeThreadCompressionRepository()
    workspace_service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        conversation_service=cast(Any, conversation_service),
    )
    thread = await workspace_service.create_thread(
        user_id="default_user",
        title="fallback compression",
        focus_type="ticker",
        ticker_refs_json=["SZSE:300308"],
    )
    await _seed_messages(
        conversation_service=conversation_service,
        conversation_id=thread["conversation_id"],
        count=2,
    )
    service = StockAnalysisThreadCompressionService(
        stock_analysis_workspace_service=workspace_service,
        stock_analysis_thread_compression_repository=cast(Any, compression_repository),
        stock_analysis_thread_memory_service=FakeMemoryProxy(),
        conversation_service=cast(Any, conversation_service),
    )
    monkeypatch.setattr(
        service,
        "_build_compression_payload",
        lambda **_: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    result = await service.capture_compression(
        user_id="default_user",
        thread_id=thread["thread_id"],
    )

    assert result is not None
    assert result["summary"]
    assert result["compression_reason"] == "manual_capture:fallback"


@pytest.mark.asyncio
async def test_stock_analysis_thread_compression_service_activate_unique_active() -> None:
    conversation_service = FakeConversationServiceForMessages()
    compression_repository = FakeThreadCompressionRepository()
    workspace_service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        conversation_service=cast(Any, conversation_service),
    )
    thread = await workspace_service.create_thread(
        user_id="default_user",
        title="activate compression",
        focus_type="ticker",
        ticker_refs_json=["SZSE:300308"],
    )
    first = compression_repository.create_compression(
        {
            "thread_id": thread["thread_id"],
            "user_id": "default_user",
            "conversation_id": thread["conversation_id"],
            "title": "v1",
            "summary": "v1",
            "current_focus": "focus1",
            "covered_until_message_id": "item_2",
            "covered_message_count": 2,
            "source_message_ids_json": ["item_1", "item_2"],
            "resolved_topics_json": [],
            "open_questions_json": [],
            "recent_compare_notes_json": [],
            "recent_refresh_notes_json": [],
            "recent_tooling_notes_json": [],
            "recent_evidence_notes_json": [],
            "active_memory_id": None,
            "focus_tickers_json": ["SZSE:300308"],
            "focus_themes_json": [],
            "compared_tickers_json": [],
            "next_questions_json": [],
            "compression_reason": "manual_capture",
            "is_active": True,
        }
    )
    second = compression_repository.create_compression(
        {
            "thread_id": thread["thread_id"],
            "user_id": "default_user",
            "conversation_id": thread["conversation_id"],
            "title": "v2",
            "summary": "v2",
            "current_focus": "focus2",
            "covered_until_message_id": "item_4",
            "covered_message_count": 4,
            "source_message_ids_json": ["item_3", "item_4"],
            "resolved_topics_json": [],
            "open_questions_json": [],
            "recent_compare_notes_json": [],
            "recent_refresh_notes_json": [],
            "recent_tooling_notes_json": [],
            "recent_evidence_notes_json": [],
            "active_memory_id": None,
            "focus_tickers_json": ["SZSE:300308"],
            "focus_themes_json": [],
            "compared_tickers_json": [],
            "next_questions_json": [],
            "compression_reason": "manual_capture",
            "is_active": False,
        }
    )
    service = StockAnalysisThreadCompressionService(
        stock_analysis_workspace_service=workspace_service,
        stock_analysis_thread_compression_repository=cast(Any, compression_repository),
        stock_analysis_thread_memory_service=FakeMemoryProxy(),
        conversation_service=cast(Any, conversation_service),
    )

    result = await service.activate_compression(
        user_id="default_user",
        thread_id=thread["thread_id"],
        compression_id=int(second.id),
    )

    assert result is not None
    assert result["compression_id"] == int(second.id)
    assert compression_repository.get_compression_by_id(
        user_id="default_user",
        thread_id=thread["thread_id"],
        compression_id=int(first.id),
    ).is_active is False
    assert compression_repository.get_compression_by_id(
        user_id="default_user",
        thread_id=thread["thread_id"],
        compression_id=int(second.id),
    ).is_active is True


@pytest.mark.asyncio
async def test_stock_analysis_thread_compression_service_refresh_creates_new_active_version() -> None:
    conversation_service = FakeConversationServiceForMessages()
    compression_repository = FakeThreadCompressionRepository()
    workspace_service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        conversation_service=cast(Any, conversation_service),
    )
    thread = await workspace_service.create_thread(
        user_id="default_user",
        title="refresh compression",
        focus_type="ticker",
        ticker_refs_json=["SZSE:300308"],
    )
    await _seed_messages(
        conversation_service=conversation_service,
        conversation_id=thread["conversation_id"],
        count=3,
    )
    service = StockAnalysisThreadCompressionService(
        stock_analysis_workspace_service=workspace_service,
        stock_analysis_thread_compression_repository=cast(Any, compression_repository),
        stock_analysis_thread_memory_service=FakeMemoryProxy(),
        conversation_service=cast(Any, conversation_service),
    )
    first = await service.capture_compression(
        user_id="default_user",
        thread_id=thread["thread_id"],
    )

    refreshed = await service.refresh_compression(
        user_id="default_user",
        thread_id=thread["thread_id"],
        compression_id=int(first["compression_id"]),
    )
    listed = await service.list_compressions(
        user_id="default_user",
        thread_id=thread["thread_id"],
    )

    assert refreshed is not None
    assert refreshed["compression_id"] != first["compression_id"]
    assert refreshed["is_active"] is True
    assert listed is not None
    assert listed["count"] == 2
    assert listed["active_compression"]["compression_id"] == refreshed["compression_id"]


@pytest.mark.asyncio
async def test_stock_analysis_thread_compression_service_recommendation_and_recent_raw_messages() -> None:
    conversation_service = FakeConversationServiceForMessages()
    compression_repository = FakeThreadCompressionRepository()
    workspace_service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        conversation_service=cast(Any, conversation_service),
    )
    thread = await workspace_service.create_thread(
        user_id="default_user",
        title="recommend compression",
        focus_type="ticker",
        ticker_refs_json=["SZSE:300308"],
    )
    await _seed_messages(
        conversation_service=conversation_service,
        conversation_id=thread["conversation_id"],
        count=11,
    )
    service = StockAnalysisThreadCompressionService(
        stock_analysis_workspace_service=workspace_service,
        stock_analysis_thread_compression_repository=cast(Any, compression_repository),
        stock_analysis_thread_memory_service=FakeMemoryProxy(),
        conversation_service=cast(Any, conversation_service),
    )

    state = await service.get_prompt_context_state(
        user_id="default_user",
        thread_id=thread["thread_id"],
    )

    assert state["compression_recommended"] is True
    assert state["uncompressed_message_count"] == 22
    assert state["recent_raw_message_count"] == 8
    assert len(state["recent_raw_messages"]) == 8
