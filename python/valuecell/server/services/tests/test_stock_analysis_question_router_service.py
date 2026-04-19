from __future__ import annotations

from valuecell.server.services.assets.stock_analysis_question_router_service import (
    StockAnalysisQuestionRouterService,
)


def test_stock_analysis_question_router_service_detects_compare_focus() -> None:
    service = StockAnalysisQuestionRouterService()

    result = service.route_question(
        thread={
            "compare_targets_json": [
                {"target_type": "ticker", "ref": "SZSE:300308", "label": "中际旭创"},
                {"target_type": "ticker", "ref": "SHSE:603019", "label": "中科曙光"},
            ]
        },
        context_cards=[],
        active_memory=None,
        active_compression=None,
        conversation_history=[],
        user_message="比较一下这两只票当前谁更优先。",
    )

    assert result.question_intent == "compare_targets"
    assert result.response_strategy == "answer_with_compare_focus"
    assert result.should_focus_compare_targets is True
    assert result.suggested_task_titles


def test_stock_analysis_question_router_service_detects_refresh_gap() -> None:
    service = StockAnalysisQuestionRouterService()

    result = service.route_question(
        thread={"compare_targets_json": []},
        context_cards=[
            {"title": "主题摘要", "is_stale": True, "refresh_recommended": True},
        ],
        active_memory={"memory_id": 1, "next_questions_json": ["刷新后结论是否变化？"]},
        active_compression=None,
        conversation_history=[],
        user_message="这个结论是不是已经过期了，要不要刷新再看？",
    )

    assert result.question_intent == "refresh_state_check"
    assert result.response_strategy == "refresh_then_answer"
    assert "stale" in result.routing_reason or "刷新" in result.routing_reason


def test_stock_analysis_question_router_service_detects_next_step_and_memory_revisit() -> None:
    service = StockAnalysisQuestionRouterService()

    result = service.route_question(
        thread={"compare_targets_json": []},
        context_cards=[],
        active_memory={
            "memory_id": 2,
            "next_questions_json": ["下一步先确认最新价格动作"],
        },
        active_compression={
            "compression_id": 4,
            "open_questions_json": ["谁才是当前比较主线？"],
        },
        conversation_history=[],
        user_message="接下来这一条线程还要研究什么？",
    )

    assert result.question_intent == "define_next_step"
    assert result.response_strategy == "suggest_research_tasks"
    assert result.should_revisit_active_memory is True
    assert result.should_revisit_active_compression is True
    assert result.followup_candidates


def test_stock_analysis_question_router_service_mentions_selected_task() -> None:
    service = StockAnalysisQuestionRouterService()

    result = service.route_question(
        thread={"compare_targets_json": []},
        context_cards=[],
        active_memory=None,
        active_compression=None,
        open_tasks=[
            {"task_id": 8, "title": "刷新后重看当前结论", "status": "open"},
        ],
        selected_task={
            "task_id": 8,
            "title": "刷新后重看当前结论",
            "summary": "旧上下文待刷新",
        },
        conversation_history=[],
        user_message="围绕这个任务继续研究。",
    )

    assert "锚定任务" in result.routing_reason
    assert "刷新后重看当前结论" in result.recommended_next_action
