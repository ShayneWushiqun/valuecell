from __future__ import annotations

from typing import Any, cast

import pytest

from valuecell.server.services.assets.stock_analysis_research_feedback_service import (
    StockAnalysisResearchFeedbackService,
)
from valuecell.server.services.assets.stock_analysis_workspace_service import (
    StockAnalysisWorkspaceService,
)
from valuecell.server.services.tests.test_stock_analysis_thread_service import (
    FakeContextRepository,
    FakeResearchFeedbackRepository,
    FakeResearchTaskRepository,
    FakeThreadRepository,
)


class FakeMessageService:
    def __init__(self, items: list[dict[str, Any]]) -> None:
        self.items = items

    async def list_messages(self, *, user_id: str, thread_id: int):
        del user_id, thread_id
        return {
            "conversation_id": "conv-thread-1",
            "thread_id": 1,
            "items": self.items,
            "count": len(self.items),
        }


class FakeThreadMemoryProxy:
    def __init__(self, memory: dict[str, Any] | None = None) -> None:
        self.memory = memory

    async def get_memory(self, *, user_id: str, thread_id: int, memory_id: int):
        del user_id, thread_id, memory_id
        return self.memory


class FakeThreadCompressionProxy:
    def __init__(self, compression: dict[str, Any] | None = None) -> None:
        self.compression = compression

    async def get_compression(
        self,
        *,
        user_id: str,
        thread_id: int,
        compression_id: int,
    ):
        del user_id, thread_id, compression_id
        return self.compression


class FakeResearchTaskService:
    def __init__(self, task_repository: FakeResearchTaskRepository) -> None:
        self.task_repository = task_repository

    async def list_tasks(self, *, user_id: str, thread_id: int):
        return {
            "thread_id": thread_id,
            "items": [
                item.to_dict()
                for item in self.task_repository.list_tasks(
                    user_id=user_id,
                    thread_id=thread_id,
                )
            ],
        }


class FakeOutcomeReviewService:
    def __init__(self, review_batches: list[list[dict[str, Any]]]) -> None:
        self.review_batches = review_batches
        self.calls = 0

    def list_reviews(self, *, user_id: str, limit: int = 120, **kwargs):
        del user_id, limit, kwargs
        index = min(self.calls, len(self.review_batches) - 1)
        self.calls += 1
        return {
            "generated_at": "2026-04-19T10:00:00Z",
            "items": self.review_batches[index],
            "count": len(self.review_batches[index]),
        }


class FakeDecisionEffectivenessService:
    def get_summary(self, *, user_id: str) -> dict[str, Any]:
        del user_id
        return {
            "available": True,
            "overall_score": 71,
            "overall_summary": "最近回看显示 AI 算力方向总体偏正向，但节奏分化。",
            "review_count": 6,
            "recent_successes": [
                {
                    "ticker": "SZSE:300308",
                    "summary": "主线确认后继续走强。",
                    "review_date": "2026-04-19",
                }
            ],
            "recent_failures": [
                {
                    "ticker": "SHSE:603019",
                    "summary": "跟随票确认不足。",
                    "review_date": "2026-04-18",
                }
            ],
        }


class FakeRiskSizingService:
    def get_summary(self, *, user_id: str) -> dict[str, Any]:
        del user_id
        return {
            "available": True,
            "market_risk_level": "中性偏进攻",
            "suggested_total_exposure_range": "35% - 45%",
            "suggested_new_position_range": "4% - 6%",
            "suggested_add_position_range": "2% - 4%",
            "holding_risk_note": "主线可跟，但不宜满仓。",
            "entry_risk_note": "更适合聚焦核心票而非全面扩散。",
            "ticker_suggestions": [
                {
                    "ticker": "SZSE:300308",
                    "available": True,
                    "risk_level": "中",
                    "summary": "核心票可小步跟踪。",
                }
            ],
        }

    def get_ticker_summary(self, *, user_id: str, ticker: str) -> dict[str, Any]:
        del user_id
        return {
            "ticker": ticker,
            "available": True,
            "risk_level": "中",
            "summary": f"{ticker} 仍适合轻仓观察。",
        }


def _build_anchor_message() -> dict[str, Any]:
    return {
        "item_id": "msg_assistant_1",
        "role": "agent",
        "content": "先 refresh 再 compare，结论偏向主线更强。",
        "mode": "need_tooling",
        "used_context_ids": [1, 2],
        "compared_tickers": ["SZSE:300308", "SHSE:603019"],
        "comparison_mode": True,
        "stale_context_ids": [1],
        "refresh_recommended_context_ids": [1],
        "tool_calls_summary": ["补最近 10 日日线价格", "补主题强弱雷达"],
        "temporary_evidence_blocks": [
            {"title": "行情补充", "summary": "中际旭创走势更强。"}
        ],
        "provider_attempts": [{"provider": "tushare", "status": "success"}],
        "refreshed_before_answer": True,
        "refresh_changed_contexts": [
            {"context_id": 1, "changed_fields": ["summary", "generated_at"]}
        ],
        "used_active_memory": True,
        "active_memory_id": 7,
        "used_active_compression": True,
        "active_compression_id": 9,
        "question_intent": "compare_targets",
        "response_strategy": "refresh_then_answer",
        "execution_plan_summary": "先 refresh 核心 context，再 compare 主线与跟随票。",
        "executed_steps": [
            {"step_type": "refresh_stale_contexts"},
            {"step_type": "inspect_compare_targets"},
            {"step_type": "collect_external_evidence"},
            {"step_type": "validate_thesis"},
        ],
        "related_task_ids": [1, 2],
        "validation_summary": {
            "thesis_status": "thesis_recheck_needed",
            "summary": "refresh 后主线优势更清楚，但仍需跟踪。",
        },
        "focus_tickers": ["SZSE:300308", "SHSE:603019"],
        "focus_themes": ["AI算力"],
    }


@pytest.mark.asyncio
async def test_stock_analysis_research_feedback_service_capture_feedback_links_metadata() -> None:
    feedback_repository = FakeResearchFeedbackRepository()
    task_repository = FakeResearchTaskRepository()
    workspace_service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
    )
    thread = await workspace_service.create_thread(
        user_id="default_user",
        title="研究反馈测试",
        focus_type="comparison",
        compare_targets_json=[
            {
                "target_type": "ticker",
                "ref": "SZSE:300308",
                "label": "中际旭创",
                "source_module": "manual",
                "source_ref": "watchlist:1",
            },
            {
                "target_type": "ticker",
                "ref": "SHSE:603019",
                "label": "中科曙光",
                "source_module": "manual",
                "source_ref": "watchlist:2",
            },
        ],
    )
    await workspace_service.create_context_card(
        user_id="default_user",
        thread_id=thread["thread_id"],
        context_type="ticker",
        title="中际旭创 context",
        summary="旧上下文",
        source_module="ticker",
        source_ref="watchlist:1",
        ticker_refs_json=["SZSE:300308"],
    )
    await workspace_service.create_context_card(
        user_id="default_user",
        thread_id=thread["thread_id"],
        context_type="ticker",
        title="中科曙光 context",
        summary="对比上下文",
        source_module="ticker",
        source_ref="watchlist:2",
        ticker_refs_json=["SHSE:603019"],
    )
    task_repository.create_task(
        {
            "thread_id": thread["thread_id"],
            "user_id": "default_user",
            "title": "继续跟踪主线确认",
            "summary": "等 refresh 后再确认是否继续聚焦。",
            "task_type": "thesis_validation",
            "status": "open",
            "priority": "high",
            "source_kind": "message",
            "source_ref": "msg_assistant_1",
            "related_tickers_json": ["SZSE:300308"],
            "related_themes_json": ["AI算力"],
            "related_context_ids_json": [1],
            "related_memory_id": 7,
            "related_compression_id": 9,
            "related_message_id": "msg_assistant_1",
            "resolution_note": None,
            "dismiss_reason": None,
            "completed_at": None,
            "dismissed_at": None,
        }
    )
    task_repository.create_task(
        {
            "thread_id": thread["thread_id"],
            "user_id": "default_user",
            "title": "补主题雷达",
            "summary": "确认题材强弱是否支撑结论。",
            "task_type": "tooling_check",
            "status": "completed",
            "priority": "medium",
            "source_kind": "message",
            "source_ref": "msg_assistant_1",
            "related_tickers_json": ["SHSE:603019"],
            "related_themes_json": ["AI算力"],
            "related_context_ids_json": [2],
            "related_memory_id": None,
            "related_compression_id": 9,
            "related_message_id": "msg_assistant_1",
            "resolution_note": "已处理",
            "dismiss_reason": None,
            "completed_at": None,
            "dismissed_at": None,
        }
    )
    outcome_service = FakeOutcomeReviewService(
        [
            [
                {
                    "review_id": 11,
                    "ticker": "SZSE:300308",
                    "outcome_status": "有效",
                    "outcome_score": 89,
                    "summary": "主线判断得到后续走势确认。",
                    "review_date": "2026-04-19",
                },
                {
                    "review_id": 12,
                    "ticker": "SHSE:603019",
                    "outcome_status": "部分有效",
                    "outcome_score": 62,
                    "summary": "跟随票表现一般，但未明显反证。",
                    "review_date": "2026-04-18",
                },
            ]
        ]
    )
    service = StockAnalysisResearchFeedbackService(
        stock_analysis_workspace_service=workspace_service,
        stock_analysis_research_feedback_repository=cast(
            Any, feedback_repository
        ),
        stock_analysis_message_service=cast(
            Any,
            FakeMessageService(
                [
                    {
                        "item_id": "msg_user_1",
                        "role": "user",
                        "content": "帮我比较一下。",
                    },
                    _build_anchor_message(),
                ]
            ),
        ),
        stock_analysis_research_task_service=FakeResearchTaskService(task_repository),
        stock_analysis_thread_memory_service=FakeThreadMemoryProxy(
            {
                "memory_id": 7,
                "focus_tickers_json": ["SZSE:300308", "SHSE:603019"],
                "focus_themes_json": ["AI算力"],
                "compared_tickers_json": ["SZSE:300308", "SHSE:603019"],
                "linked_context_ids_json": [1, 2],
            }
        ),
        stock_analysis_thread_compression_service=FakeThreadCompressionProxy(
            {
                "compression_id": 9,
                "focus_tickers_json": ["SZSE:300308", "SHSE:603019"],
                "focus_themes_json": ["AI算力"],
                "compared_tickers_json": ["SZSE:300308", "SHSE:603019"],
            }
        ),
        decision_outcome_review_service=cast(Any, outcome_service),
        decision_effectiveness_service=cast(
            Any, FakeDecisionEffectivenessService()
        ),
        risk_sizing_service=cast(Any, FakeRiskSizingService()),
    )

    result = await service.capture_feedback(
        user_id="default_user",
        thread_id=thread["thread_id"],
        anchor_message_id="msg_assistant_1",
        note="先看这轮研究到底有没有价值。",
    )

    assert result is not None
    assert result["anchor_message_id"] == "msg_assistant_1"
    assert result["linked_task_ids_json"] == [1, 2]
    assert result["linked_memory_id"] == 7
    assert result["linked_compression_id"] == 9
    assert result["linked_context_ids_json"] == [1, 2]
    assert result["outcome_alignment_status"] == "partially_confirmed"
    assert result["process_quality_status"] in {
        "effective",
        "mixed",
    }
    assert result["compare_helpful"] is True
    assert result["refresh_helpful"] is True
    assert result["tooling_helpful"] is True
    assert result["validation_helpful"] is True
    assert result["what_helped_json"]
    assert result["process_adjustments_json"]
    assert result["task_followup_suggestions_json"]
    assert result["linked_outcome_review_ids_json"] == [11, 12]


@pytest.mark.asyncio
async def test_stock_analysis_research_feedback_service_refresh_creates_new_version() -> None:
    feedback_repository = FakeResearchFeedbackRepository()
    workspace_service = StockAnalysisWorkspaceService(
        stock_analysis_thread_repository=cast(Any, FakeThreadRepository()),
        analysis_context_card_repository=cast(Any, FakeContextRepository()),
    )
    thread = await workspace_service.create_thread(
        user_id="default_user",
        title="研究反馈 refresh",
        focus_type="ticker",
        ticker_refs_json=["SZSE:300308"],
    )
    outcome_service = FakeOutcomeReviewService(
        [
            [],
            [
                {
                    "review_id": 18,
                    "ticker": "SZSE:300308",
                    "outcome_status": "有效",
                    "outcome_score": 92,
                    "summary": "后续走势确认了 refresh 后的判断。",
                    "review_date": "2026-04-19",
                }
            ],
        ]
    )
    service = StockAnalysisResearchFeedbackService(
        stock_analysis_workspace_service=workspace_service,
        stock_analysis_research_feedback_repository=cast(
            Any, feedback_repository
        ),
        stock_analysis_message_service=cast(
            Any, FakeMessageService([_build_anchor_message()])
        ),
        stock_analysis_research_task_service=FakeResearchTaskService(
            FakeResearchTaskRepository()
        ),
        stock_analysis_thread_memory_service=FakeThreadMemoryProxy(None),
        stock_analysis_thread_compression_service=FakeThreadCompressionProxy(None),
        decision_outcome_review_service=cast(Any, outcome_service),
        decision_effectiveness_service=cast(
            Any, FakeDecisionEffectivenessService()
        ),
        risk_sizing_service=cast(Any, FakeRiskSizingService()),
    )

    captured = await service.capture_feedback(
        user_id="default_user",
        thread_id=thread["thread_id"],
        anchor_message_id="msg_assistant_1",
    )
    refreshed = await service.refresh_feedback(
        user_id="default_user",
        thread_id=thread["thread_id"],
        feedback_id=1,
        note="刷新后重新读取最新 outcome。",
    )
    listed = await service.list_feedbacks(
        user_id="default_user",
        thread_id=thread["thread_id"],
    )

    assert captured is not None
    assert captured["outcome_alignment_status"] == "unclear"
    assert refreshed is not None
    assert refreshed["feedback_id"] != captured["feedback_id"]
    assert refreshed["anchor_message_id"] == captured["anchor_message_id"]
    assert refreshed["version"] == 2
    assert refreshed["linked_outcome_review_ids_json"] == [18]
    assert listed is not None
    assert listed["count"] == 2
    assert listed["latest_feedback"]["feedback_id"] == refreshed["feedback_id"]
