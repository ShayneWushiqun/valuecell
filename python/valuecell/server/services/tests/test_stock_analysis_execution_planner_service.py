from __future__ import annotations

from valuecell.server.services.assets.stock_analysis_execution_planner_service import (
    StockAnalysisExecutionPlannerService,
)


def _routing(
    *,
    question_intent: str,
    response_strategy: str,
) -> dict[str, str]:
    return {
        "question_intent": question_intent,
        "response_strategy": response_strategy,
        "routing_reason": f"识别为 {question_intent}；因此采用 {response_strategy}",
    }


def test_stock_analysis_execution_planner_service_builds_compare_plan() -> None:
    service = StockAnalysisExecutionPlannerService()

    plan = service.build_execution_plan(
        thread={
            "compare_targets_json": [
                {"target_type": "ticker", "ref": "SZSE:300308", "label": "中际旭创"},
                {"target_type": "ticker", "ref": "SHSE:603019", "label": "中科曙光"},
            ],
            "ticker_refs_json": ["SZSE:300308", "SHSE:603019"],
            "theme_refs_json": ["AI算力"],
        },
        context_cards=[{"ticker_refs_json": ["SZSE:300308"], "theme_refs_json": []}],
        active_memory={"memory_id": 1},
        active_compression={"compression_id": 2},
        open_tasks=[
            {
                "task_id": 9,
                "title": "补充比较：中际旭创 vs 中科曙光 的优先级确认",
                "summary": "继续比较",
                "status": "open",
                "priority": "high",
                "related_tickers_json": ["SZSE:300308", "SHSE:603019"],
                "related_themes_json": [],
            }
        ],
        question_routing=_routing(
            question_intent="compare_targets",
            response_strategy="answer_with_compare_focus",
        ),
        user_message="比较一下这两只票现在谁更优先。",
    )

    assert plan.primary_compare_targets == ["中际旭创", "中科曙光"]
    assert plan.related_task_ids == [9]
    assert plan.requires_validation is True
    assert [step.step_type for step in plan.steps][:2] == [
        "inspect_context_cards",
        "inspect_compare_targets",
    ]


def test_stock_analysis_execution_planner_service_plans_refresh_and_tooling() -> None:
    service = StockAnalysisExecutionPlannerService()

    plan = service.build_execution_plan(
        thread={"compare_targets_json": [], "ticker_refs_json": ["SZSE:300308"], "theme_refs_json": []},
        context_cards=[
            {
                "context_id": 3,
                "ticker_refs_json": ["SZSE:300308"],
                "theme_refs_json": [],
                "is_stale": True,
                "refresh_recommended": True,
            }
        ],
        active_memory=None,
        active_compression=None,
        open_tasks=[],
        question_routing=_routing(
            question_intent="external_evidence_check",
            response_strategy="tooling_then_answer",
        ),
        user_message="补一下最新证据再判断。",
    )

    step_types = [step.step_type for step in plan.steps]
    assert plan.requires_refresh is True
    assert plan.requires_tooling is True
    assert "refresh_stale_contexts" in step_types
    assert "collect_internal_structured_evidence" in step_types
    assert "collect_market_price_evidence" in step_types
    assert "collect_external_evidence" in step_types


def test_stock_analysis_execution_planner_service_builds_validation_and_task_suggestions() -> None:
    service = StockAnalysisExecutionPlannerService()
    validation = service.build_validation_summary(
        question_routing=_routing(
            question_intent="challenge_conclusion",
            response_strategy="restate_and_recheck",
        ),
        active_memory={
            "support_points_json": ["基本面未恶化"],
            "opposing_points_json": ["量价配合仍不足"],
            "risk_points_json": ["旧上下文待刷新"],
            "key_uncertainties_json": ["最新价格动作未确认"],
        },
        active_compression=None,
        planner_mode="need_tooling",
        refresh_run={"refreshed_context_ids": [3]},
        previous_validation_summary={"thesis_status": "thesis_maintained"},
        related_tasks=[{"task_id": 5, "title": "重验 thesis"}],
    )
    suggestions = service.build_task_update_suggestions(
        related_tasks=[{"task_id": 5, "title": "重验 thesis"}],
        validation_summary=validation,
        requires_refresh=False,
        requires_tooling=True,
        question_routing=_routing(
            question_intent="challenge_conclusion",
            response_strategy="restate_and_recheck",
        ),
    )

    assert validation.thesis_status in {
        "thesis_maintained",
        "thesis_weakened",
        "thesis_recheck_needed",
        "thesis_improved",
    }
    assert validation.summary
    assert suggestions
    assert suggestions[0].task_id == 5
