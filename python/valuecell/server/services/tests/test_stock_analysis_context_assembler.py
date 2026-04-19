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
        active_memory={
            "memory_id": 8,
            "version": 2,
            "title": "当前研究记忆",
            "updated_at": "2026-04-19T10:00:00Z",
            "stance": "比较观察",
            "confidence": 0.6,
            "time_horizon": "短线到波段",
            "summary": "当前以显式上下文比较两只票的优先级。",
            "support_points_json": ["主线仍清晰。"],
            "opposing_points_json": ["候选票承接待确认。"],
            "risk_points_json": ["旧卡片需刷新。"],
            "key_uncertainties_json": ["最新价格动作尚未确认。"],
            "invalidation_conditions_json": ["刷新后若摘要变化则失效。"],
            "next_questions_json": ["刷新后谁更优先？"],
            "next_data_to_check_json": ["最新价格动作"],
        },
        active_compression={
            "compression_id": 5,
            "version": 2,
            "title": "当前对话压缩",
            "updated_at": "2026-04-19T10:10:00Z",
            "current_focus": "继续比较谁更优先",
            "covered_until_message_id": "item_12",
            "covered_message_count": 12,
            "summary": "较早历史对话已压缩。",
            "resolved_topics_json": ["早期比较结论已讨论。"],
            "open_questions_json": ["最新承接谁更强？"],
            "recent_compare_notes_json": ["最近比较了两只票。"],
            "recent_refresh_notes_json": ["已刷新 1 张上下文卡片。"],
            "recent_tooling_notes_json": ["补了价格动作。"],
            "recent_evidence_notes_json": ["行情补充：补最近 5 日日线。"],
        },
        recent_raw_messages=[
            {"item_id": "item_13", "role": "user", "content": "最近承接谁更强？"},
            {"item_id": "item_14", "role": "assistant", "content": "先看中军强度。"},
        ],
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
    assert result["used_active_memory"] is True
    assert result["used_active_compression"] is True
    assert result["recent_raw_message_count"] == 2
    assert result["compared_tickers"] == ["SZSE:300308", "SZSE:000001"]
    assert result["stale_context_ids"] == [11]
    assert "AI算力题材摘要" in result["prompt_context"]
    assert "Compare Targets" in result["prompt_context"]
    assert "Current Context Refresh Status" in result["prompt_context"]
    assert "Thread Active Research Memory" in result["prompt_context"]
    assert "Thread Active Conversation Compression" in result["prompt_context"]
    assert "Recent Raw Messages" in result["prompt_context"]
    assert "Memory ID: 8" in result["prompt_context"]
    assert "Compression ID: 5" in result["prompt_context"]
    assert "item_13" in result["prompt_context"]
    assert "source=holding" in result["prompt_context"]
    assert "已删除卡片" not in result["prompt_context"]
    assert "比较中际旭创和平安银行" in result["prompt_context"]
