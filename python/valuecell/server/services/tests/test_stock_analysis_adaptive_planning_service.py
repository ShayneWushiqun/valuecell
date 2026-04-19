from __future__ import annotations

from typing import Any, cast

from valuecell.server.services.assets.stock_analysis_adaptive_planning_service import (
    StockAnalysisAdaptivePlanningService,
)
from valuecell.server.services.tests.test_stock_analysis_thread_service import (
    FakeResearchFeedbackRepository,
)


def test_stock_analysis_adaptive_planning_service_prefers_compare_when_feedback_supports_it() -> None:
    repository = FakeResearchFeedbackRepository()
    repository.create_feedback(
        {
            "thread_id": 1,
            "user_id": "default_user",
            "anchor_message_id": "msg_1",
            "title": "feedback 1",
            "anchor_question_intent": "compare_targets",
            "anchor_response_strategy": "answer_with_compare_focus",
            "anchor_mode": "context_only",
            "anchor_plan_summary": "",
            "anchor_validation_status": "thesis_maintained",
            "linked_task_ids_json": [3],
            "linked_context_ids_json": [1],
            "linked_memory_id": None,
            "linked_compression_id": None,
            "linked_compare_targets_json": [{"ref": "SZSE:300308"}, {"ref": "SHSE:603019"}],
            "linked_tickers_json": ["SZSE:300308", "SHSE:603019"],
            "linked_themes_json": [],
            "linked_outcome_review_ids_json": [],
            "linked_effectiveness_snapshot_json": {},
            "linked_risk_sizing_snapshot_json": {},
            "outcome_alignment_status": "confirmed",
            "process_quality_status": "effective",
            "compare_helpful": True,
            "refresh_helpful": False,
            "tooling_helpful": False,
            "validation_helpful": True,
            "what_helped_json": [],
            "what_hurt_json": [],
            "process_adjustments_json": [],
            "task_followup_suggestions_json": [],
            "summary": "",
            "detail_note": None,
        }
    )
    repository.create_feedback(
        {
            "thread_id": 1,
            "user_id": "default_user",
            "anchor_message_id": "msg_2",
            "title": "feedback 2",
            "anchor_question_intent": "compare_targets",
            "anchor_response_strategy": "answer_with_compare_focus",
            "anchor_mode": "need_tooling",
            "anchor_plan_summary": "",
            "anchor_validation_status": "thesis_improved",
            "linked_task_ids_json": [],
            "linked_context_ids_json": [],
            "linked_memory_id": None,
            "linked_compression_id": None,
            "linked_compare_targets_json": [{"ref": "SZSE:300308"}, {"ref": "SHSE:603019"}],
            "linked_tickers_json": ["SZSE:300308", "SHSE:603019"],
            "linked_themes_json": [],
            "linked_outcome_review_ids_json": [],
            "linked_effectiveness_snapshot_json": {},
            "linked_risk_sizing_snapshot_json": {},
            "outcome_alignment_status": "partially_confirmed",
            "process_quality_status": "effective",
            "compare_helpful": True,
            "refresh_helpful": False,
            "tooling_helpful": False,
            "validation_helpful": False,
            "what_helped_json": [],
            "what_hurt_json": [],
            "process_adjustments_json": [],
            "task_followup_suggestions_json": [],
            "summary": "",
            "detail_note": None,
        }
    )
    service = StockAnalysisAdaptivePlanningService(
        stock_analysis_research_feedback_repository=cast(Any, repository)
    )

    result = service.build_adaptive_planning(
        user_id="default_user",
        thread_id=1,
        thread={"compare_targets_json": [{"ref": "SZSE:300308"}, {"ref": "SHSE:603019"}]},
        context_cards=[],
        active_memory=None,
        active_compression=None,
        open_tasks=[
            {
                "task_id": 3,
                "task_type": "compare_followup",
                "priority": "high",
            }
        ],
        question_routing={"question_intent": "compare_targets"},
    )

    assert result.planning_profile == "compare_first"
    assert result.prefer_compare_first is True
    assert result.preferred_first_action == "compare_targets"
    assert result.preferred_evidence_order[:3] == [
        "explicit_context",
        "compare_targets",
        "internal_structured",
    ]


def test_stock_analysis_adaptive_planning_service_prefers_refresh_and_avoids_over_research() -> None:
    repository = FakeResearchFeedbackRepository()
    for index in range(3):
        repository.create_feedback(
            {
                "thread_id": 2,
                "user_id": "default_user",
                "anchor_message_id": f"msg_{index}",
                "title": "feedback",
                "anchor_question_intent": "update_thesis",
                "anchor_response_strategy": "restate_and_recheck",
                "anchor_mode": "need_tooling",
                "anchor_plan_summary": "",
                "anchor_validation_status": "thesis_recheck_needed",
                "linked_task_ids_json": [],
                "linked_context_ids_json": [],
                "linked_memory_id": None,
                "linked_compression_id": None,
                "linked_compare_targets_json": [],
                "linked_tickers_json": ["SZSE:300308"],
                "linked_themes_json": [],
                "linked_outcome_review_ids_json": [],
                "linked_effectiveness_snapshot_json": {},
                "linked_risk_sizing_snapshot_json": {},
                "outcome_alignment_status": "unclear",
                "process_quality_status": "over_researched",
                "compare_helpful": False,
                "refresh_helpful": True,
                "tooling_helpful": False,
                "validation_helpful": True,
                "what_helped_json": [],
                "what_hurt_json": [],
                "process_adjustments_json": [],
                "task_followup_suggestions_json": [],
                "summary": "",
                "detail_note": None,
            }
        )
    service = StockAnalysisAdaptivePlanningService(
        stock_analysis_research_feedback_repository=cast(Any, repository)
    )

    result = service.build_adaptive_planning(
        user_id="default_user",
        thread_id=2,
        thread={"compare_targets_json": []},
        context_cards=[{"is_stale": True, "refresh_recommended": True}],
        active_memory={"memory_id": 1},
        active_compression={"compression_id": 2},
        open_tasks=[{"task_id": 4, "task_type": "refresh_needed", "priority": "high"}],
        question_routing={"question_intent": "update_thesis"},
    )

    assert result.prefer_refresh_first is True
    assert result.avoid_over_research is True
    assert result.planning_profile in {"refresh_first", "lightweight_research"}
    assert "refresh" in result.preferred_evidence_order
    assert result.confidence_hint
