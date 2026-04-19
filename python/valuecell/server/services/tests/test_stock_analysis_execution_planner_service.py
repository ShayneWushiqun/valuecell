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
        adaptive_planning={
            "planning_profile": "compare_first",
            "preferred_evidence_order": [
                "explicit_context",
                "compare_targets",
                "internal_structured",
                "market_price",
                "validation",
            ],
            "prefer_compare_first": True,
            "planning_adjustments": ["最近 compare 路径更有效。"],
            "adjustment_reasoning": "feedback-aware planning 让 compare 前置。",
        },
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
        adaptive_planning={
            "planning_profile": "refresh_first",
            "preferred_evidence_order": [
                "explicit_context",
                "refresh",
                "internal_structured",
                "market_price",
                "external_confirmation",
                "validation",
            ],
            "prefer_refresh_first": True,
            "prefer_external_confirmation": True,
            "planning_adjustments": ["先 refresh 再补证据。"],
            "adjustment_reasoning": "stale context 较多，refresh-first 更稳。",
        },
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
        evidence_conflict_summary={
            "conflict_level": "high",
            "supporting_evidence": ["显式卡片仍支持主线。"],
            "opposing_evidence": ["外部确认与价格动作相互冲突。"],
            "risk_evidence": ["当前先不宜强化结论。"],
            "resolution_suggestion": "优先 refresh 后再判断。",
            "should_weaken_thesis": True,
            "should_recheck_before_concluding": True,
        },
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
    assert validation.evidence_conflict_level == "high"
    assert validation.resolution_suggestion == "优先 refresh 后再判断。"


def test_stock_analysis_execution_planner_service_builds_conflict_summary() -> None:
    service = StockAnalysisExecutionPlannerService()
    conflict = service.build_evidence_conflict_summary(
        adaptive_planning={"planning_profile": "balanced"},
        tooling_result=type(
            "FakeToolingResult",
            (),
            {
                "temporary_evidence_blocks": [
                    {"title": "内部结构", "summary": "主线仍有支撑，走势加强。"},
                    {"title": "外部确认", "summary": "消息面转弱，短线分歧加大。"},
                    {"title": "风险提示", "summary": "波动风险仍在。"},
                ]
            },
        )(),
        active_memory={
            "support_points_json": ["原 thesis 仍有一条支持点"],
            "opposing_points_json": ["已有一条反对点"],
            "risk_points_json": ["高波动"],
        },
    )

    assert conflict.conflict_level in {"medium", "high"}
    assert conflict.supporting_evidence
    assert conflict.opposing_evidence
    assert conflict.resolution_suggestion
