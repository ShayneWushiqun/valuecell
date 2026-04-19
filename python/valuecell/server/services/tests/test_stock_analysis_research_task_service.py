from __future__ import annotations

from typing import Any, cast

import pytest

from valuecell.core.types import BaseResponseDataPayload, NotifyResponseEvent, Role
from valuecell.server.services.assets.stock_analysis_research_task_service import (
    StockAnalysisResearchTaskService,
)
from valuecell.server.services.assets.stock_analysis_workspace_service import (
    StockAnalysisWorkspaceService,
)
from valuecell.server.services.tests.test_stock_analysis_message_service import (
    FakeConversationServiceForMessages,
)
from valuecell.server.services.tests.test_stock_analysis_thread_service import (
    FakeContextRepository,
    FakeResearchTaskRepository,
    FakeThreadRepository,
)


class FakeMemoryProxy:
    def __init__(self, active_memory: dict[str, Any] | None = None) -> None:
        self.active_memory = active_memory

    async def get_active_memory(self, *, user_id: str, thread_id: int):
        del user_id, thread_id
        return self.active_memory


class FakeCompressionProxy:
    def __init__(
        self,
        active_compression: dict[str, Any] | None = None,
        *,
        compression_recommended: bool = False,
    ) -> None:
        self.active_compression = active_compression
        self.compression_recommended = compression_recommended

    async def get_active_compression(self, *, user_id: str, thread_id: int):
        del user_id, thread_id
        return self.active_compression

    async def get_prompt_context_state(self, *, user_id: str, thread_id: int, recent_limit: int = 8):
        del user_id, thread_id, recent_limit
        return {
            "active_compression": self.active_compression,
            "recent_raw_messages": [],
            "recent_raw_message_count": 0,
            "compression_recommended": self.compression_recommended,
            "compression_reason": "最近变化较多" if self.compression_recommended else None,
            "uncompressed_message_count": 10 if self.compression_recommended else 0,
            "estimated_history_size": 1200,
            "active_compression_stale": self.compression_recommended,
        }


async def _seed_message(
    *,
    conversation_service: FakeConversationServiceForMessages,
    conversation_id: str,
    role: str,
    content: str,
    metadata: dict[str, Any],
) -> None:
    await conversation_service.core_conversation_service.add_item(
        role=role,
        event=NotifyResponseEvent.MESSAGE,
        conversation_id=conversation_id,
        payload=BaseResponseDataPayload(content=content),
        metadata=metadata,
    )


@pytest.mark.asyncio
async def test_stock_analysis_research_task_service_generates_tasks_and_dedupes() -> None:
    conversation_service = FakeConversationServiceForMessages()
    repository = FakeResearchTaskRepository()
    workspace_service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        conversation_service=cast(Any, conversation_service),
    )
    thread = await workspace_service.create_thread(
        user_id="default_user",
        title="研究任务生成",
        focus_type="comparison",
        compare_targets_json=[
            {
                "target_type": "ticker",
                "ref": "SZSE:300308",
                "label": "中际旭创",
                "source_module": "manual",
            },
            {
                "target_type": "ticker",
                "ref": "SHSE:603019",
                "label": "中科曙光",
                "source_module": "manual",
            },
        ],
    )
    await workspace_service.create_context_card(
        user_id="default_user",
        thread_id=thread["thread_id"],
        context_type="ticker",
        title="旧的比较卡",
        summary="需要刷新",
        source_module="ticker",
        source_ref="SZSE:300308",
    )
    workspace_service.analysis_context_card_repository.update_context_card(
        user_id="default_user",
        thread_id=thread["thread_id"],
        context_id=1,
        payload={"snapshot_payload_json": {"freshness_days": 7}},
    )
    await _seed_message(
        conversation_service=conversation_service,
        conversation_id=thread["conversation_id"],
        role=Role.AGENT,
        content="最近需要重验比较主线。",
        metadata={
            "question_intent": "challenge_conclusion",
            "response_strategy": "restate_and_recheck",
            "routing_reason": "识别为 challenge_conclusion；因此采用 restate_and_recheck",
            "recommended_next_action": "先重述 thesis 再复核",
            "suggested_task_titles_json": '["重验当前 thesis 与关键反例"]',
            "compared_tickers_json": '["SZSE:300308","SHSE:603019"]',
            "refresh_recommended_context_ids_json": "[1]",
            "tool_calls_summary_json": '["补最近 5 日日线价格"]',
            "temporary_evidence_blocks_json": '[{"title":"行情补充","summary":"补最近 5 日日线价格"}]',
        },
    )
    service = StockAnalysisResearchTaskService(
        stock_analysis_workspace_service=workspace_service,
        stock_analysis_research_task_repository=cast(Any, repository),
        stock_analysis_thread_memory_service=FakeMemoryProxy(
            {
                "memory_id": 3,
                "focus_tickers_json": ["SZSE:300308", "SHSE:603019"],
                "focus_themes_json": ["AI算力"],
                "linked_context_ids_json": [1],
                "key_uncertainties_json": ["最新价格动作还没核对"],
                "next_questions_json": ["这两只票谁更值得继续跟踪？"],
                "risk_points_json": ["对比对象节奏可能不同步"],
            }
        ),
        stock_analysis_thread_compression_service=FakeCompressionProxy(
            {
                "compression_id": 5,
                "focus_tickers_json": ["SZSE:300308", "SHSE:603019"],
                "focus_themes_json": ["AI算力"],
                "open_questions_json": ["刷新后谁才是主线？"],
                "recent_tooling_notes_json": ["补最近 5 日日线价格"],
                "recent_evidence_notes_json": ["行情补充：补最近 5 日日线价格"],
                "recent_compare_notes_json": ["当前 compare targets：中际旭创 / 中科曙光"],
            },
            compression_recommended=True,
        ),
        conversation_service=cast(Any, conversation_service),
    )

    first = await service.generate_tasks(user_id="default_user", thread_id=thread["thread_id"])
    second = await service.generate_tasks(user_id="default_user", thread_id=thread["thread_id"])
    listed = await service.list_tasks(user_id="default_user", thread_id=thread["thread_id"])

    assert first is not None
    assert first["created_count"] >= 4
    assert second is not None
    assert second["updated_count"] >= 1
    assert listed is not None
    assert listed["open_count"] >= 4
    assert listed["high_priority_open_count"] >= 1
    assert listed["has_actionable_gap"] is True


@pytest.mark.asyncio
async def test_stock_analysis_research_task_service_complete_reopen_and_dismiss() -> None:
    repository = FakeResearchTaskRepository()
    workspace_service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
    )
    thread = await workspace_service.create_thread(
        user_id="default_user",
        title="状态流转",
        focus_type="mixed",
    )
    repository.create_task(
        {
            "thread_id": thread["thread_id"],
            "user_id": "default_user",
            "title": "先完成这个任务",
            "summary": "状态流转测试",
            "task_type": "next_question",
            "status": "open",
            "priority": "medium",
            "source_kind": "manual",
            "source_ref": None,
            "related_tickers_json": [],
            "related_themes_json": [],
            "related_context_ids_json": [],
            "related_memory_id": None,
            "related_compression_id": None,
            "related_message_id": None,
            "resolution_note": None,
            "dismiss_reason": None,
            "completed_at": None,
            "dismissed_at": None,
        }
    )
    service = StockAnalysisResearchTaskService(
        stock_analysis_workspace_service=workspace_service,
        stock_analysis_research_task_repository=cast(Any, repository),
    )

    completed = await service.complete_task(
        user_id="default_user",
        thread_id=thread["thread_id"],
        task_id=1,
        note="已处理",
    )
    reopened = await service.reopen_task(
        user_id="default_user",
        thread_id=thread["thread_id"],
        task_id=1,
    )
    dismissed = await service.dismiss_task(
        user_id="default_user",
        thread_id=thread["thread_id"],
        task_id=1,
        note="当前不需要",
    )

    assert completed is not None
    assert completed["status"] == "completed"
    assert completed["resolution_note"] == "已处理"
    assert reopened is not None
    assert reopened["status"] == "open"
    assert dismissed is not None
    assert dismissed["status"] == "dismissed"
    assert dismissed["dismiss_reason"] == "当前不需要"
