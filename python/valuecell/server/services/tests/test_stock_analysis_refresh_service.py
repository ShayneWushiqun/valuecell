from __future__ import annotations

from typing import Any, cast

import pytest

from valuecell.server.services.assets.stock_analysis_refresh_service import (
    StockAnalysisRefreshService,
)
from valuecell.server.services.assets.stock_analysis_workspace_service import (
    TEMPORARY_EVIDENCE_SAVED_CONTEXT_TYPE,
    StockAnalysisWorkspaceService,
)
from valuecell.server.services.tests.test_stock_analysis_thread_service import (
    FakeContextRepository,
    FakeConversationService,
    FakeThreadRepository,
)


@pytest.mark.asyncio
async def test_refresh_stale_contexts_only_refreshes_stale_or_recommended_items() -> None:
    workspace_service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        conversation_service=cast(Any, FakeConversationService()),
    )
    thread = await workspace_service.create_thread(
        user_id="default_user",
        title="刷新线程",
        focus_type="ticker",
        ticker_refs_json=["SZSE:300308"],
    )
    stale_card = await workspace_service.create_context_card(
        user_id="default_user",
        thread_id=thread["thread_id"],
        context_type="ticker",
        title="旧 ticker 卡",
        summary="旧摘要",
        ticker_refs_json=["SZSE:300308"],
        snapshot_payload_json={"generated_at": "2026-04-10T09:00:00+00:00"},
        source_module="ticker",
        source_ref="SZSE:300308",
    )
    fresh_card = await workspace_service.create_context_card(
        user_id="default_user",
        thread_id=thread["thread_id"],
        context_type="theme",
        title="较新主题卡",
        summary="较新摘要",
        theme_refs_json=["AI算力"],
        snapshot_payload_json={"generated_at": "2026-04-18T09:00:00+00:00"},
        source_module="theme",
        source_ref="AI",
    )
    assert stale_card is not None and fresh_card is not None

    service = StockAnalysisRefreshService(workspace_service)
    result = await service.refresh_stale_contexts(
        user_id="default_user",
        thread_id=thread["thread_id"],
    )

    assert result is not None
    assert result["refreshed_count"] == 1
    assert result["failed_count"] == 0
    assert result["skipped_count"] == 0
    assert result["refreshed_context_ids"] == [stale_card["context_id"]]
    assert all(item["context_id"] != fresh_card["context_id"] for item in result["items"])


@pytest.mark.asyncio
async def test_refresh_stale_contexts_skips_unsupported_cards_with_summary() -> None:
    workspace_service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        conversation_service=cast(Any, FakeConversationService()),
    )
    thread = await workspace_service.create_thread(
        user_id="default_user",
        title="刷新线程",
        focus_type="mixed",
    )
    card = await workspace_service.create_context_card(
        user_id="default_user",
        thread_id=thread["thread_id"],
        context_type=TEMPORARY_EVIDENCE_SAVED_CONTEXT_TYPE,
        title="保存的临时证据",
        summary="不支持直接刷新",
        snapshot_payload_json={"generated_at": "2026-04-10T09:00:00+00:00"},
        source_module="tooling_evidence",
        source_ref="msg:1",
    )
    assert card is not None

    service = StockAnalysisRefreshService(workspace_service)
    result = await service.refresh_stale_contexts(
        user_id="default_user",
        thread_id=thread["thread_id"],
        context_ids=[card["context_id"]],
        include_supported_only=True,
    )

    assert result is not None
    assert result["refreshed_count"] == 0
    assert result["skipped_count"] == 1
    assert "不支持直接刷新" in result["items"][0]["reason"]
