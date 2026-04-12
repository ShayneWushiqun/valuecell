from __future__ import annotations

from typing import Any, cast

from valuecell.server.services.assets.entry_timing_service import EntryTimingService


class FakeOpportunityPoolService:
    def get_opportunity_candidates(self, user_id: str = "default_user") -> dict[str, Any]:
        return {
            "generated_at": "2025-04-10T09:30:00Z",
            "available": True,
            "items": [
                {
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "topic_name": "AI算力",
                    "candidate_state": "高优先级买点",
                    "priority_score": 88,
                    "tradeability_state": "可观察",
                    "expectation_gap_level": "中",
                    "role_label": "龙头",
                    "trend_quality": "顺势",
                    "reasons": ["与主线题材共振。"],
                    "missing_confirmations": ["仍需等待更明确的承接或回踩确认。"],
                    "invalid_conditions": [],
                    "time_horizon": "1-2周",
                },
                {
                    "ticker": "SSE:600030",
                    "display_name": "中信证券",
                    "topic_name": "证券",
                    "candidate_state": "候选买点",
                    "priority_score": 73,
                    "tradeability_state": "谨慎追高",
                    "expectation_gap_level": "高",
                    "role_label": "中军",
                    "trend_quality": "顺势",
                    "reasons": ["当前位置偏高。"],
                    "missing_confirmations": [],
                    "invalid_conditions": [],
                    "time_horizon": "1-2周",
                },
                {
                    "ticker": "SZSE:000007",
                    "display_name": "ST全新",
                    "topic_name": "ST板块",
                    "candidate_state": "暂不参与",
                    "priority_score": 29,
                    "tradeability_state": "流动性风险",
                    "expectation_gap_level": "低",
                    "role_label": "跟风",
                    "trend_quality": "走弱",
                    "reasons": ["存在明显风险条件。"],
                    "missing_confirmations": [],
                    "invalid_conditions": ["疑似 ST 或高风险方向，默认回避。"],
                    "time_horizon": "1-2周",
                },
            ],
            "count": 3,
            "empty_message": None,
        }


def test_entry_timing_service_uses_conservative_actions() -> None:
    service = EntryTimingService(
        opportunity_pool_service=cast(Any, FakeOpportunityPoolService())
    )

    result = service.get_entry_timing_signals("default_user")

    assert result["available"] is True
    assert result["count"] == 3
    high_priority = next(item for item in result["items"] if item["ticker"] == "SZSE:300308")
    chase_item = next(item for item in result["items"] if item["ticker"] == "SSE:600030")
    risk_item = next(item for item in result["items"] if item["ticker"] == "SZSE:000007")

    assert high_priority["action"] == "接近可参与窗口"
    assert chase_item["action"] == "等待回踩确认"
    assert risk_item["action"] == "暂不参与"
    assert risk_item["confidence"] < high_priority["confidence"]


def test_entry_timing_service_lowers_confidence_for_low_expectation_gap() -> None:
    service = EntryTimingService(
        opportunity_pool_service=cast(Any, FakeOpportunityPoolService())
    )

    result = service.get_entry_timing_signals("default_user")

    risk_item = next(item for item in result["items"] if item["ticker"] == "SZSE:000007")

    assert "风险收益比不足" in risk_item["expectation_gap_view"]
    assert any("风险收益比不足" in reason for reason in risk_item["reasons"])
