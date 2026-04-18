from __future__ import annotations

from valuecell.server.services.assets.stock_analysis_tool_planner import (
    CONTEXT_ONLY_MODE,
    NEED_TOOLING_MODE,
    USER_FORCED_TOOLING_MODE,
    StockAnalysisToolPlanner,
)


def test_stock_analysis_tool_planner_keeps_context_only_for_summary_question() -> None:
    planner = StockAnalysisToolPlanner()

    result = planner.plan(
        thread={"focus_type": "ticker"},
        context_cards=[
            {
                "context_type": "holding",
                "ticker_refs_json": ["SZSE:300308"],
                "theme_refs_json": ["AI算力"],
            }
        ],
        conversation_history=[],
        user_message="请总结当前上下文里这张卡片的核心判断。",
        force_tooling=False,
        ticker_refs=["SZSE:300308"],
        theme_refs=["AI算力"],
    )

    assert result.mode == CONTEXT_ONLY_MODE
    assert result.tool_layers_to_use == []


def test_stock_analysis_tool_planner_force_tooling_enters_user_forced_mode() -> None:
    planner = StockAnalysisToolPlanner()

    result = planner.plan(
        thread={"focus_type": "ticker"},
        context_cards=[{"context_type": "ticker"}],
        conversation_history=[],
        user_message="补数据后再回答。",
        force_tooling=True,
        ticker_refs=["SZSE:300308"],
        theme_refs=[],
    )

    assert result.mode == USER_FORCED_TOOLING_MODE
    assert result.tool_reason is not None
    assert result.tool_layers_to_use


def test_stock_analysis_tool_planner_detects_missing_latest_price_context() -> None:
    planner = StockAnalysisToolPlanner()

    result = planner.plan(
        thread={"focus_type": "ticker"},
        context_cards=[{"context_type": "ticker"}],
        conversation_history=[],
        user_message="结合最近价格走势再判断这只票。",
        force_tooling=False,
        ticker_refs=["SZSE:300308"],
        theme_refs=[],
    )

    assert result.mode == NEED_TOOLING_MODE
    assert "latest_price_action" in result.missing_context_hints
