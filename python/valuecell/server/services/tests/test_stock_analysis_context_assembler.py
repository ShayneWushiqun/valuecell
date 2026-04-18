from __future__ import annotations

from valuecell.server.services.assets.stock_analysis_context_assembler import (
    StockAnalysisContextAssembler,
)


def test_stock_analysis_context_assembler_builds_prompt_without_deleted_cards() -> None:
    assembler = StockAnalysisContextAssembler()

    result = assembler.assemble(
        thread={
            "thread_id": 1,
            "title": "AI 算力比较",
            "focus_type": "comparison",
            "conversation_id": "conv_test_1",
            "compare_targets_json": [
                {
                    "target_type": "ticker",
                    "ref": "SZSE:300308",
                    "label": "中军",
                    "source_module": "holding",
                    "source_ref": "1",
                    "role": "primary",
                    "order": 0,
                },
                {
                    "target_type": "ticker",
                    "ref": "SZSE:000001",
                    "label": "候选票",
                    "source_module": "opportunity",
                    "source_ref": "SZSE:000001",
                    "role": "secondary",
                    "order": 1,
                },
            ],
        },
        context_cards=[
            {
                "context_id": 10,
                "context_type": "theme",
                "title": "AI算力题材摘要",
                "subtitle": "主升",
                "summary": "主线仍清晰。",
                "ticker_refs_json": ["SZSE:300308"],
                "theme_refs_json": ["AI算力"],
                "is_pinned": True,
                "source_module": "theme",
                "freshness_label": "较新",
                "refresh_recommended": False,
                "is_stale": False,
            },
            {
                "context_id": 11,
                "context_type": "opportunity",
                "title": "平安银行机会池摘要",
                "subtitle": "候选买点",
                "summary": "等待确认。",
                "ticker_refs_json": ["SZSE:000001"],
                "theme_refs_json": ["金融"],
                "is_pinned": False,
                "source_module": "opportunity",
                "freshness_label": "建议刷新",
                "refresh_recommended": True,
                "is_stale": True,
            },
        ],
        user_question="比较中际旭创和平安银行在当前线程里的优先级。",
    )

    assert result["used_context_ids"] == [10, 11]
    assert result["comparison_mode"] is True
    assert result["compared_tickers"] == ["SZSE:300308", "SZSE:000001"]
    assert result["stale_context_ids"] == [11]
    assert "AI算力题材摘要" in result["prompt_context"]
    assert "Comparison Targets" in result["prompt_context"]
    assert "source=holding" in result["prompt_context"]
    assert "已删除卡片" not in result["prompt_context"]
    assert "比较中际旭创和平安银行" in result["prompt_context"]
