from __future__ import annotations

from typing import Any

import pytest

from valuecell.server.api.schemas.stock_analysis_adaptive_planning import (
    StockAnalysisAdaptivePlanningData,
)
from valuecell.server.services.assets.stock_analysis_overview_service import (
    StockAnalysisOverviewService,
)


class FakeWorkspaceService:
    async def list_threads(self, *, user_id: str):
        del user_id
        return {
            "items": [
                {
                    "thread_id": 1,
                    "title": "AI算力主线",
                    "focus_type": "comparison",
                    "updated_at": "2026-04-19T10:00:00Z",
                    "compare_targets_json": [{"ref": "SZSE:300308"}, {"ref": "SHSE:603019"}],
                },
                {
                    "thread_id": 2,
                    "title": "机器人支线",
                    "focus_type": "ticker",
                    "updated_at": "2026-04-19T09:30:00Z",
                    "compare_targets_json": [],
                },
            ],
            "count": 2,
        }

    async def list_context_cards(self, *, user_id: str, thread_id: int):
        del user_id
        if thread_id == 1:
            return {
                "items": [
                    {"context_id": 1, "is_stale": True, "refresh_recommended": True},
                    {"context_id": 2, "is_stale": False, "refresh_recommended": False},
                ]
            }
        return {
            "items": [
                {"context_id": 3, "is_stale": False, "refresh_recommended": False}
            ]
        }


class FakeResearchTaskService:
    async def list_tasks(self, *, user_id: str, thread_id: int):
        del user_id
        if thread_id == 1:
            return {
                "thread_id": 1,
                "items": [
                    {
                        "task_id": 11,
                        "title": "先 refresh 再确认",
                        "summary": "当前需要先刷新上下文。",
                        "priority": "high",
                        "status": "open",
                        "task_type": "refresh_needed",
                    }
                ],
            }
        return {
            "thread_id": 2,
            "items": [
                {
                    "task_id": 21,
                    "title": "继续跟踪机器人",
                    "summary": "低优先级观察任务。",
                    "priority": "low",
                    "status": "open",
                    "task_type": "next_question",
                }
            ],
        }


class FakeThreadMemoryService:
    async def list_memories(self, *, user_id: str, thread_id: int):
        del user_id
        return {
            "thread_id": thread_id,
            "active_memory": {"memory_id": thread_id} if thread_id == 2 else None,
            "items": [],
            "count": 0,
        }


class FakeThreadCompressionService:
    async def list_compressions(self, *, user_id: str, thread_id: int):
        del user_id
        return {
            "thread_id": thread_id,
            "active_compression": {"compression_id": thread_id} if thread_id == 2 else None,
            "items": [],
            "count": 0,
            "compression_recommended": thread_id == 1,
        }


class FakeResearchFeedbackService:
    async def list_feedbacks(self, *, user_id: str, thread_id: int):
        del user_id
        if thread_id == 1:
            latest = {
                "feedback_id": 101,
                "outcome_alignment_status": "unclear",
                "process_quality_status": "under_evidenced",
            }
            return {
                "thread_id": 1,
                "items": [latest],
                "latest_feedback": latest,
                "count": 1,
            }
        latest = {
            "feedback_id": 201,
            "outcome_alignment_status": "confirmed",
            "process_quality_status": "effective",
        }
        return {
            "thread_id": 2,
            "items": [latest],
            "latest_feedback": latest,
            "count": 1,
        }


class FakeAdaptivePlanningService:
    def build_adaptive_planning(self, *, thread_id: int, **kwargs):
        del kwargs
        if thread_id == 1:
            return StockAnalysisAdaptivePlanningData(
                planning_profile="refresh_first",
                preferred_evidence_order=[
                    "explicit_context",
                    "refresh",
                    "internal_structured",
                ],
            )
        return StockAnalysisAdaptivePlanningData(
            planning_profile="compare_first",
            preferred_evidence_order=[
                "explicit_context",
                "compare_targets",
                "validation",
            ],
        )


class FakeMessageService:
    async def list_messages(self, *, user_id: str, thread_id: int):
        del user_id
        if thread_id == 1:
            return {
                "thread_id": 1,
                "items": [
                    {
                        "item_id": "msg_a",
                        "role": "assistant",
                        "adaptive_planning_profile": "refresh_first",
                        "validation_summary": {"thesis_status": "thesis_recheck_needed"},
                        "evidence_conflict_summary": {
                            "conflict_level": "high",
                            "provider_conflicts": [
                                "external_confirmation 与内部结构化/价格证据存在分歧。"
                            ],
                            "provider_support_map": {
                                "internal_structured": ["内部结构: 主线仍有支撑。"]
                            },
                            "provider_opposing_map": {
                                "external_confirmation": ["外部确认: 消息面转弱。"]
                            },
                        },
                    }
                ],
            }
        return {
            "thread_id": 2,
            "items": [
                {
                    "item_id": "msg_b",
                    "role": "assistant",
                    "adaptive_planning_profile": "compare_first",
                    "validation_summary": {"thesis_status": "thesis_improved"},
                    "evidence_conflict_summary": {"conflict_level": "low"},
                }
            ],
        }


class FakeCompareService:
    async def list_compare_targets(self, *, user_id: str, thread_id: int):
        del user_id
        if thread_id == 1:
            return {
                "thread_id": 1,
                "compare_targets": [{"ref": "SZSE:300308"}, {"ref": "SHSE:603019"}],
            }
        return {"thread_id": 2, "compare_targets": []}


@pytest.mark.asyncio
async def test_stock_analysis_overview_service_builds_overview_and_action_queue() -> None:
    service = StockAnalysisOverviewService(
        stock_analysis_workspace_service=FakeWorkspaceService(),
        stock_analysis_research_task_service=FakeResearchTaskService(),
        stock_analysis_thread_memory_service=FakeThreadMemoryService(),
        stock_analysis_thread_compression_service=FakeThreadCompressionService(),
        stock_analysis_research_feedback_service=FakeResearchFeedbackService(),
        stock_analysis_adaptive_planning_service=FakeAdaptivePlanningService(),
        stock_analysis_message_service=FakeMessageService(),
        stock_analysis_compare_service=FakeCompareService(),
    )

    result = await service.get_overview(user_id="default_user")

    assert result["available"] is True
    assert len(result["thread_overview_items"]) == 2
    assert result["high_conflict_threads"][0]["thread_id"] == 1
    assert result["refresh_needed_threads"][0]["thread_id"] == 1
    assert result["high_priority_tasks"][0]["task_id"] == 11
    assert result["action_queue"]
    assert result["research_quality_summary"]["effective_count"] == 1
    assert result["research_quality_summary"]["under_evidenced_count"] == 1
    assert result["planning_profile_summary"]["refresh_first_count"] == 1
    assert result["planning_profile_summary"]["compare_first_count"] == 1
    assert result["recent_feedback_summary"]["high_conflict_thread_count"] == 1
    assert result["recent_feedback_summary"]["effective_thread_count"] == 1
    first_thread = result["thread_overview_items"][0]
    assert first_thread["thread_health_status"] in {
        "high_conflict",
        "needs_refresh",
    }
    assert first_thread["thread_health_score"] <= 70
    assert first_thread["next_best_action"] in {
        "review_high_conflict",
        "refresh_thread",
    }
