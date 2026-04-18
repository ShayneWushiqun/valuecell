from __future__ import annotations

from typing import Any, cast

import pytest

from valuecell.server.services.assets.stock_analysis_compare_service import (
    StockAnalysisCompareService,
)
from valuecell.server.services.assets.stock_analysis_workspace_service import (
    StockAnalysisWorkspaceService,
)
from valuecell.server.services.tests.test_stock_analysis_thread_service import (
    FakeContextRepository,
    FakeConversationService,
    FakeThreadRepository,
)


@pytest.mark.asyncio
async def test_compare_service_lists_and_updates_compare_targets() -> None:
    workspace_service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
        conversation_service=cast(Any, FakeConversationService()),
    )
    thread = await workspace_service.create_thread(
        user_id="default_user",
        title="对比线程",
        focus_type="mixed",
    )
    service = StockAnalysisCompareService(
        stock_analysis_workspace_service=workspace_service,
    )

    updated = await service.update_compare_targets(
        user_id="default_user",
        thread_id=thread["thread_id"],
        compare_targets=[
            {
                "target_type": "ticker",
                "ref": "SZSE:000001",
                "label": "持仓票",
                "source_module": "holding",
                "source_ref": "1",
                "role": "primary",
                "order": 0,
            },
            {
                "target_type": "ticker",
                "ref": "SHSE:600519",
                "label": "机会票",
                "source_module": "opportunity",
                "source_ref": "SHSE:600519",
                "role": "secondary",
                "order": 1,
            },
        ],
    )

    assert updated is not None
    assert updated["comparison_mode"] is True
    assert updated["compared_tickers"] == ["SZSE:000001", "SHSE:600519"]
    listed = await service.list_compare_targets(
        user_id="default_user",
        thread_id=thread["thread_id"],
    )
    assert listed is not None
    assert listed["focus_type"] == "comparison"
    assert listed["compare_targets"][0]["label"] == "持仓票"
