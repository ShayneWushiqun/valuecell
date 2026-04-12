from __future__ import annotations

from typing import Any, cast

from valuecell.server.services.assets.decision_alert_service import DecisionAlertService


class FakeEntryTimingService:
    def get_entry_timing_signals(self, user_id: str = "default_user") -> dict[str, Any]:
        return {
            "generated_at": "2025-04-10T10:00:00Z",
            "available": True,
            "items": [
                {
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "topic_name": "AI算力",
                    "action": "接近可参与窗口",
                    "confidence": 76,
                    "summary": "处于较优观察阶段，但仍需等待进一步确认。",
                    "reasons": ["与主线题材共振。"],
                    "tradeability_state": "可观察",
                    "expectation_gap_view": "预期差中性，等待更明确的交易窗口。",
                    "missing_confirmations": ["仍需等待更明确的承接或回踩确认。"],
                    "invalid_conditions": [],
                    "candidate_state": "高优先级买点",
                    "priority_score": 88,
                    "time_horizon": "1-2周",
                },
                {
                    "ticker": "SSE:600030",
                    "display_name": "中信证券",
                    "topic_name": "证券",
                    "action": "仅适合持有",
                    "confidence": 58,
                    "summary": "更适合持有观察，当前不宜主动追价。",
                    "reasons": ["当前位置偏高。"],
                    "tradeability_state": "谨慎追高",
                    "expectation_gap_view": "仍有预期差，但需要确认承接与持续性。",
                    "missing_confirmations": [],
                    "invalid_conditions": ["短线位置偏高。"],
                    "candidate_state": "候选买点",
                    "priority_score": 73,
                    "time_horizon": "1-2周",
                },
                {
                    "ticker": "SZSE:000007",
                    "display_name": "ST全新",
                    "topic_name": "ST板块",
                    "action": "暂不参与",
                    "confidence": 33,
                    "summary": "当前存在风险条件，先回避 ST板块 方向参与。",
                    "reasons": ["存在明显风险条件。"],
                    "tradeability_state": "流动性风险",
                    "expectation_gap_view": "预期差偏低，当前风险收益比不足。",
                    "missing_confirmations": [],
                    "invalid_conditions": ["疑似 ST 或高风险方向，默认回避。"],
                    "candidate_state": "暂不参与",
                    "priority_score": 29,
                    "time_horizon": "1-2周",
                },
            ],
            "count": 3,
            "empty_message": None,
        }


def test_decision_alert_service_maps_alert_types_and_sorts_by_confidence() -> None:
    service = DecisionAlertService(entry_timing_service=cast(Any, FakeEntryTimingService()))

    result = service.get_decision_alert_summary("default_user")

    assert result["available"] is True
    assert result["count"] == 3
    assert result["items"][0]["ticker"] == "SZSE:300308"
    assert result["items"][0]["alert_type"] == "买点接近"
    assert result["items"][1]["alert_type"] == "持有观察"
    assert result["items"][2]["alert_type"] == "风险回避"


def test_decision_alert_service_includes_next_action_and_reasons() -> None:
    service = DecisionAlertService(entry_timing_service=cast(Any, FakeEntryTimingService()))

    result = service.get_decision_alert_summary("default_user")

    first_item = result["items"][0]
    risk_item = result["items"][-1]

    assert "继续观察" in first_item["next_action"] or "确认" in first_item["next_action"]
    assert first_item["reasons"]
    assert risk_item["priority"] in {"high", "medium"}
    assert "回避" in risk_item["body"]
