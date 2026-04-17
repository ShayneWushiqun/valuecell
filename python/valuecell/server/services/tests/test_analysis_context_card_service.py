from __future__ import annotations

from typing import Any, cast

import pytest

from valuecell.server.services.assets.stock_analysis_workspace_service import (
    StockAnalysisWorkspaceService,
)
from valuecell.server.services.tests.test_stock_analysis_thread_service import (
    FakeContextRepository,
    FakeConversationService,
    FakeThreadRepository,
)


@pytest.mark.asyncio
async def test_create_update_and_delete_context_card() -> None:
    service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        conversation_service=cast(Any, FakeConversationService()),
    )
    thread = await service.create_thread(
        user_id="default_user",
        title="上下文卡片测试",
        focus_type="mixed",
    )

    created = await service.create_context_card(
        user_id="default_user",
        thread_id=thread["thread_id"],
        context_type="tradingagents_run",
        title="初始摘要",
        summary="保守跟踪。",
        source_module="tradingagents_run",
        source_ref="run_ctx_1",
        is_pinned=False,
    )
    updated = await service.update_context_card(
        user_id="default_user",
        thread_id=thread["thread_id"],
        context_id=created["context_id"],
        title="更新后摘要",
        is_pinned=True,
    )
    deleted = await service.delete_context_card(
        user_id="default_user",
        thread_id=thread["thread_id"],
        context_id=created["context_id"],
    )

    assert created is not None
    assert updated is not None
    assert updated["title"] == "更新后摘要"
    assert updated["is_pinned"] is True
    assert deleted is True
