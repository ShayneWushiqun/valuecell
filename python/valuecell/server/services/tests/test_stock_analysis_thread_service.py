from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import pytest

from valuecell.server.services.assets.stock_analysis_workspace_service import (
    StockAnalysisWorkspaceService,
)


@dataclass
class FakeThreadRecord:
    id: int
    user_id: str
    title: str
    focus_type: str
    ticker_refs_json: list[str]
    theme_refs_json: list[str]
    compare_targets_json: list[dict[str, Any]]
    conversation_id: str
    archived_at: Any = None

    created_at: Any = None
    updated_at: Any = None

    def __post_init__(self) -> None:
        import datetime as dt

        self.created_at = self.created_at or dt.datetime.now(dt.UTC)
        self.updated_at = self.updated_at or dt.datetime.now(dt.UTC)

    def to_dict(self) -> dict[str, Any]:
        return {
            "thread_id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "focus_type": self.focus_type,
            "ticker_refs_json": list(self.ticker_refs_json),
            "theme_refs_json": list(self.theme_refs_json),
            "compare_targets_json": list(self.compare_targets_json),
            "conversation_id": self.conversation_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
        }


@dataclass
class FakeContextRecord:
    id: int
    thread_id: int
    user_id: str
    context_type: str
    title: str
    subtitle: str | None
    ticker_refs_json: list[str]
    theme_refs_json: list[str]
    summary: str
    snapshot_payload_json: dict[str, Any]
    source_module: str
    source_ref: str | None
    staleness_hint: str | None
    is_pinned: bool

    created_at: Any = None
    updated_at: Any = None

    def __post_init__(self) -> None:
        import datetime as dt

        self.created_at = self.created_at or dt.datetime.now(dt.UTC)
        self.updated_at = self.updated_at or dt.datetime.now(dt.UTC)

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_id": self.id,
            "thread_id": self.thread_id,
            "user_id": self.user_id,
            "context_type": self.context_type,
            "title": self.title,
            "subtitle": self.subtitle,
            "ticker_refs_json": list(self.ticker_refs_json),
            "theme_refs_json": list(self.theme_refs_json),
            "summary": self.summary,
            "snapshot_payload_json": dict(self.snapshot_payload_json),
            "source_module": self.source_module,
            "source_ref": self.source_ref,
            "staleness_hint": self.staleness_hint,
            "is_pinned": self.is_pinned,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class FakeMemoryRecord:
    id: int
    thread_id: int
    user_id: str
    title: str
    summary: str
    stance: str
    confidence: float
    time_horizon: str
    focus_tickers_json: list[str]
    focus_themes_json: list[str]
    compared_tickers_json: list[str]
    support_points_json: list[str]
    opposing_points_json: list[str]
    risk_points_json: list[str]
    key_uncertainties_json: list[str]
    invalidation_conditions_json: list[str]
    next_questions_json: list[str]
    next_data_to_check_json: list[str]
    linked_context_ids_json: list[int]
    linked_message_ids_json: list[str]
    linked_compare_targets_json: list[dict[str, Any]]
    source_snapshot_json: dict[str, Any]
    is_active: bool
    created_at: Any = None
    updated_at: Any = None

    def __post_init__(self) -> None:
        import datetime as dt

        self.created_at = self.created_at or dt.datetime.now(dt.UTC)
        self.updated_at = self.updated_at or dt.datetime.now(dt.UTC)

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.id,
            "thread_id": self.thread_id,
            "user_id": self.user_id,
            "title": self.title,
            "summary": self.summary,
            "stance": self.stance,
            "confidence": self.confidence,
            "time_horizon": self.time_horizon,
            "focus_tickers_json": list(self.focus_tickers_json),
            "focus_themes_json": list(self.focus_themes_json),
            "compared_tickers_json": list(self.compared_tickers_json),
            "support_points_json": list(self.support_points_json),
            "opposing_points_json": list(self.opposing_points_json),
            "risk_points_json": list(self.risk_points_json),
            "key_uncertainties_json": list(self.key_uncertainties_json),
            "invalidation_conditions_json": list(self.invalidation_conditions_json),
            "next_questions_json": list(self.next_questions_json),
            "next_data_to_check_json": list(self.next_data_to_check_json),
            "linked_context_ids_json": list(self.linked_context_ids_json),
            "linked_message_ids_json": list(self.linked_message_ids_json),
            "linked_compare_targets_json": list(self.linked_compare_targets_json),
            "source_snapshot_json": dict(self.source_snapshot_json),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class FakeCompressionRecord:
    id: int
    thread_id: int
    user_id: str
    conversation_id: str
    title: str
    summary: str
    current_focus: str
    covered_until_message_id: str | None
    covered_message_count: int
    source_message_ids_json: list[str]
    resolved_topics_json: list[str]
    open_questions_json: list[str]
    recent_compare_notes_json: list[str]
    recent_refresh_notes_json: list[str]
    recent_tooling_notes_json: list[str]
    recent_evidence_notes_json: list[str]
    active_memory_id: int | None
    focus_tickers_json: list[str]
    focus_themes_json: list[str]
    compared_tickers_json: list[str]
    next_questions_json: list[str]
    compression_reason: str
    is_active: bool
    created_at: Any = None
    updated_at: Any = None

    def __post_init__(self) -> None:
        import datetime as dt

        self.created_at = self.created_at or dt.datetime.now(dt.UTC)
        self.updated_at = self.updated_at or dt.datetime.now(dt.UTC)

    def to_dict(self) -> dict[str, Any]:
        return {
            "compression_id": self.id,
            "thread_id": self.thread_id,
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "title": self.title,
            "summary": self.summary,
            "current_focus": self.current_focus,
            "covered_until_message_id": self.covered_until_message_id,
            "covered_message_count": self.covered_message_count,
            "source_message_ids_json": list(self.source_message_ids_json),
            "resolved_topics_json": list(self.resolved_topics_json),
            "open_questions_json": list(self.open_questions_json),
            "recent_compare_notes_json": list(self.recent_compare_notes_json),
            "recent_refresh_notes_json": list(self.recent_refresh_notes_json),
            "recent_tooling_notes_json": list(self.recent_tooling_notes_json),
            "recent_evidence_notes_json": list(self.recent_evidence_notes_json),
            "active_memory_id": self.active_memory_id,
            "focus_tickers_json": list(self.focus_tickers_json),
            "focus_themes_json": list(self.focus_themes_json),
            "compared_tickers_json": list(self.compared_tickers_json),
            "next_questions_json": list(self.next_questions_json),
            "compression_reason": self.compression_reason,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class FakeResearchTaskRecord:
    id: int
    thread_id: int
    user_id: str
    title: str
    summary: str
    task_type: str
    status: str
    priority: str
    source_kind: str
    source_ref: str | None
    related_tickers_json: list[str]
    related_themes_json: list[str]
    related_context_ids_json: list[int]
    related_memory_id: int | None
    related_compression_id: int | None
    related_message_id: str | None
    resolution_note: str | None
    dismiss_reason: str | None
    created_at: Any = None
    updated_at: Any = None
    completed_at: Any = None
    dismissed_at: Any = None

    def __post_init__(self) -> None:
        import datetime as dt

        self.created_at = self.created_at or dt.datetime.now(dt.UTC)
        self.updated_at = self.updated_at or dt.datetime.now(dt.UTC)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.id,
            "thread_id": self.thread_id,
            "user_id": self.user_id,
            "title": self.title,
            "summary": self.summary,
            "task_type": self.task_type,
            "status": self.status,
            "priority": self.priority,
            "source_kind": self.source_kind,
            "source_ref": self.source_ref,
            "related_tickers_json": list(self.related_tickers_json),
            "related_themes_json": list(self.related_themes_json),
            "related_context_ids_json": list(self.related_context_ids_json),
            "related_memory_id": self.related_memory_id,
            "related_compression_id": self.related_compression_id,
            "related_message_id": self.related_message_id,
            "resolution_note": self.resolution_note,
            "dismiss_reason": self.dismiss_reason,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "dismissed_at": self.dismissed_at.isoformat() if self.dismissed_at else None,
        }


class FakeThreadRepository:
    def __init__(self) -> None:
        self.items: list[FakeThreadRecord] = []
        self.next_id = 1

    def list_threads(self, *, user_id: str, include_archived: bool = False, limit: int = 100):
        result = [item for item in self.items if item.user_id == user_id]
        if not include_archived:
            result = [item for item in result if item.archived_at is None]
        return result[:limit]

    def get_thread_by_id(self, *, user_id: str, thread_id: int, include_archived: bool = False):
        for item in self.items:
            if item.user_id == user_id and item.id == thread_id:
                if item.archived_at is not None and not include_archived:
                    return None
                return item
        return None

    def create_thread(self, payload: dict[str, Any]):
        item = FakeThreadRecord(id=self.next_id, **payload)
        self.next_id += 1
        self.items.append(item)
        return item

    def update_thread(self, *, user_id: str, thread_id: int, payload: dict[str, Any]):
        item = self.get_thread_by_id(user_id=user_id, thread_id=thread_id, include_archived=True)
        if item is None:
            return None
        for key, value in payload.items():
            setattr(item, key, value)
        return item


class FakeContextRepository:
    def __init__(self) -> None:
        self.items: list[FakeContextRecord] = []
        self.next_id = 1

    def list_context_cards(self, *, user_id: str, thread_id: int):
        return [
            item
            for item in self.items
            if item.user_id == user_id and item.thread_id == thread_id
        ]

    def create_context_card(self, payload: dict[str, Any]):
        item = FakeContextRecord(id=self.next_id, **payload)
        self.next_id += 1
        self.items.append(item)
        return item

    def get_context_card_by_id(
        self,
        *,
        user_id: str,
        thread_id: int,
        context_id: int,
    ):
        for item in self.items:
            if item.user_id == user_id and item.thread_id == thread_id and item.id == context_id:
                return item
        return None

    def update_context_card(self, *, user_id: str, thread_id: int, context_id: int, payload: dict[str, Any]):
        for item in self.items:
            if item.user_id == user_id and item.thread_id == thread_id and item.id == context_id:
                for key, value in payload.items():
                    setattr(item, key, value)
                return item
        return None

    def delete_context_card(self, *, user_id: str, thread_id: int, context_id: int):
        before = len(self.items)
        self.items = [
            item
            for item in self.items
            if not (
                item.user_id == user_id and item.thread_id == thread_id and item.id == context_id
            )
        ]
        return len(self.items) != before

    def delete_context_cards_by_filter(
        self,
        *,
        user_id: str,
        thread_id: int,
        context_type: str | None = None,
        source_module: str | None = None,
        source_ref: str | None = None,
    ):
        before = len(self.items)
        kept: list[FakeContextRecord] = []
        for item in self.items:
            matched = item.user_id == user_id and item.thread_id == thread_id
            if matched and context_type and item.context_type != context_type:
                matched = False
            if matched and source_module and item.source_module != source_module:
                matched = False
            if matched and source_ref and item.source_ref != source_ref:
                matched = False
            if not matched:
                kept.append(item)
        self.items = kept
        return before - len(self.items)


class FakeThreadMemoryRepository:
    def __init__(self) -> None:
        self.items: list[FakeMemoryRecord] = []
        self.next_id = 1

    def list_memories(self, *, user_id: str, thread_id: int, limit: int = 100):
        result = [
            item
            for item in self.items
            if item.user_id == user_id and item.thread_id == thread_id
        ]
        result.sort(key=lambda item: (item.created_at, item.id), reverse=True)
        return result[:limit]

    def get_memory_by_id(self, *, user_id: str, thread_id: int, memory_id: int):
        for item in self.items:
            if item.user_id == user_id and item.thread_id == thread_id and item.id == memory_id:
                return item
        return None

    def get_active_memory(self, *, user_id: str, thread_id: int):
        candidates = [
            item
            for item in self.items
            if item.user_id == user_id
            and item.thread_id == thread_id
            and bool(item.is_active)
        ]
        candidates.sort(key=lambda item: (item.updated_at, item.id), reverse=True)
        return candidates[0] if candidates else None

    def create_memory(self, payload: dict[str, Any]):
        item = FakeMemoryRecord(id=self.next_id, **payload)
        self.next_id += 1
        self.items.append(item)
        return item

    def update_memory(
        self,
        *,
        user_id: str,
        thread_id: int,
        memory_id: int,
        payload: dict[str, Any],
    ):
        item = self.get_memory_by_id(
            user_id=user_id,
            thread_id=thread_id,
            memory_id=memory_id,
        )
        if item is None:
            return None
        for key, value in payload.items():
            setattr(item, key, value)
        return item

    def deactivate_thread_memories(
        self,
        *,
        user_id: str,
        thread_id: int,
        exclude_memory_id: int | None = None,
    ) -> int:
        count = 0
        for item in self.items:
            if item.user_id != user_id or item.thread_id != thread_id:
                continue
            if exclude_memory_id is not None and item.id == exclude_memory_id:
                continue
            if item.is_active:
                item.is_active = False
                count += 1
        return count


class FakeThreadCompressionRepository:
    def __init__(self) -> None:
        self.items: list[FakeCompressionRecord] = []
        self.next_id = 1

    def list_compressions(self, *, user_id: str, thread_id: int, limit: int = 100):
        result = [
            item
            for item in self.items
            if item.user_id == user_id and item.thread_id == thread_id
        ]
        result.sort(key=lambda item: (item.created_at, item.id), reverse=True)
        return result[:limit]

    def get_compression_by_id(
        self,
        *,
        user_id: str,
        thread_id: int,
        compression_id: int,
    ):
        for item in self.items:
            if (
                item.user_id == user_id
                and item.thread_id == thread_id
                and item.id == compression_id
            ):
                return item
        return None

    def get_active_compression(self, *, user_id: str, thread_id: int):
        candidates = [
            item
            for item in self.items
            if item.user_id == user_id
            and item.thread_id == thread_id
            and bool(item.is_active)
        ]
        candidates.sort(key=lambda item: (item.updated_at, item.id), reverse=True)
        return candidates[0] if candidates else None

    def create_compression(self, payload: dict[str, Any]):
        item = FakeCompressionRecord(id=self.next_id, **payload)
        self.next_id += 1
        self.items.append(item)
        return item

    def update_compression(
        self,
        *,
        user_id: str,
        thread_id: int,
        compression_id: int,
        payload: dict[str, Any],
    ):
        item = self.get_compression_by_id(
            user_id=user_id,
            thread_id=thread_id,
            compression_id=compression_id,
        )
        if item is None:
            return None
        for key, value in payload.items():
            setattr(item, key, value)
        return item

    def deactivate_thread_compressions(
        self,
        *,
        user_id: str,
        thread_id: int,
        exclude_compression_id: int | None = None,
    ) -> int:
        count = 0
        for item in self.items:
            if item.user_id != user_id or item.thread_id != thread_id:
                continue
            if exclude_compression_id is not None and item.id == exclude_compression_id:
                continue
            if item.is_active:
                item.is_active = False
                count += 1
        return count


class FakeResearchTaskRepository:
    def __init__(self) -> None:
        self.items: list[FakeResearchTaskRecord] = []
        self.next_id = 1

    def list_tasks(
        self,
        *,
        user_id: str,
        thread_id: int,
        status: str | None = None,
        limit: int = 200,
    ):
        result = [
            item
            for item in self.items
            if item.user_id == user_id and item.thread_id == thread_id
        ]
        if status:
            result = [item for item in result if item.status == status]
        result.sort(key=lambda item: (item.updated_at, item.id), reverse=True)
        return result[:limit]

    def get_task_by_id(self, *, user_id: str, thread_id: int, task_id: int):
        for item in self.items:
            if item.user_id == user_id and item.thread_id == thread_id and item.id == task_id:
                return item
        return None

    def create_task(self, payload: dict[str, Any]):
        item = FakeResearchTaskRecord(id=self.next_id, **payload)
        self.next_id += 1
        self.items.append(item)
        return item

    def update_task(
        self,
        *,
        user_id: str,
        thread_id: int,
        task_id: int,
        payload: dict[str, Any],
    ):
        item = self.get_task_by_id(
            user_id=user_id,
            thread_id=thread_id,
            task_id=task_id,
        )
        if item is None:
            return None
        for key, value in payload.items():
            setattr(item, key, value)
        return item


class FakeConversationManager:
    def __init__(self) -> None:
        self.items: dict[str, Any] = {}

    async def create_conversation(
        self,
        user_id: str,
        title: str | None = None,
        conversation_id: str | None = None,
        agent_name: str | None = None,
    ):
        import datetime as dt

        conversation = type(
            "Conversation",
            (),
            {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "title": title,
                "agent_name": agent_name,
                "updated_at": dt.datetime.now(dt.UTC),
            },
        )()
        self.items[conversation_id] = conversation
        return conversation

    async def get_conversation(self, conversation_id: str):
        return self.items.get(conversation_id)

    async def update_conversation(self, conversation) -> None:
        self.items[conversation.conversation_id] = conversation

    async def delete_conversation(self, conversation_id: str) -> bool:
        self.items.pop(conversation_id, None)
        return True

    async def deactivate_conversation(self, conversation_id: str) -> bool:
        conversation = self.items.get(conversation_id)
        if conversation is None:
            return False
        conversation.status = "inactive"
        return True


class FakeConversationService:
    def __init__(self) -> None:
        self.conversation_manager = FakeConversationManager()


@pytest.mark.asyncio
async def test_create_thread_generates_conversation_id() -> None:
    service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        conversation_service=cast(Any, FakeConversationService()),
    )

    result = await service.create_thread(
        user_id="default_user",
        title="AI 算力跟踪",
        focus_type="ticker",
        ticker_refs_json=["SZSE:300308"],
    )

    assert result["thread_id"] == 1
    assert result["conversation_id"].startswith("conv-")


@pytest.mark.asyncio
async def test_duplicate_thread_creates_new_thread_and_conversation_and_copies_contexts() -> None:
    thread_repo = FakeThreadRepository()
    context_repo = FakeContextRepository()
    service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, thread_repo),
        analysis_context_card_repository=cast(Any, context_repo),
        conversation_service=cast(Any, FakeConversationService()),
    )
    source = await service.create_thread(
        user_id="default_user",
        title="中际旭创跟踪",
        focus_type="tradingagents_followup",
        ticker_refs_json=["SZSE:300308"],
    )
    await service.create_context_card(
        user_id="default_user",
        thread_id=source["thread_id"],
        context_type="tradingagents_run",
        title="中际旭创 TradingAgents 分析摘要",
        summary="先看承接和利润保护。",
        source_module="tradingagents_run",
        source_ref="run_1",
        is_pinned=True,
    )

    duplicated = await service.duplicate_thread(
        user_id="default_user",
        thread_id=source["thread_id"],
    )

    assert duplicated is not None
    assert duplicated["thread"]["thread_id"] != source["thread_id"]
    assert duplicated["thread"]["conversation_id"] != source["conversation_id"]
    assert len(duplicated["contexts"]) == 1


@pytest.mark.asyncio
async def test_delete_thread_is_soft_delete() -> None:
    thread_repo = FakeThreadRepository()
    service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, thread_repo),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        conversation_service=cast(Any, FakeConversationService()),
    )
    created = await service.create_thread(
        user_id="default_user",
        title="软删除验证",
        focus_type="mixed",
    )

    deleted = await service.delete_thread(
        user_id="default_user",
        thread_id=created["thread_id"],
    )

    assert deleted is not None
    assert deleted["archived_at"] is not None
    assert thread_repo.get_thread_by_id(
        user_id="default_user",
        thread_id=created["thread_id"],
        include_archived=True,
    ) is not None
