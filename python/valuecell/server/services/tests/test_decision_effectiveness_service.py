from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, cast

from valuecell.server.services.assets.decision_effectiveness_service import (
    DecisionEffectivenessService,
)


@dataclass
class FakeReviewRecord:
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)


class FakeDecisionOutcomeReviewRepository:
    def __init__(self, items: list[dict[str, Any]]) -> None:
        self.items = [FakeReviewRecord(item) for item in items]

    def list_reviews(self, *, user_id: str, limit: int = 50, **_: Any):
        return self.items[:limit]


class FakeDecisionRecordService:
    def __init__(self, items: list[dict[str, Any]]) -> None:
        self.items = items

    def list_records(self, *, user_id: str, limit: int = 20, action: str | None = None):
        result = list(self.items)
        if action:
            result = [item for item in result if item.get("action") == action]
        return {
            "generated_at": "2025-04-20T10:00:00Z",
            "items": result[:limit],
            "count": len(result),
        }


def _make_review(
    record_id: int,
    *,
    ticker: str,
    action: str,
    outcome_status: str,
    outcome_score: int,
    review_date: str | None = None,
    summary: str | None = None,
) -> dict[str, Any]:
    normalized_review_date = review_date or (date.today() - timedelta(days=2)).isoformat()
    return {
        "review_id": record_id,
        "record_id": record_id,
        "ticker": ticker,
        "display_name": ticker,
        "action": action,
        "lifecycle_stage": "主升持有期",
        "record_date": "2025-04-01",
        "review_date": normalized_review_date,
        "review_horizon_days": 10,
        "available": True,
        "outcome_status": outcome_status,
        "outcome_score": outcome_score,
        "summary": summary or f"{ticker} {outcome_status}",
    }


def _make_record(
    record_id: int,
    *,
    ticker: str,
    role_label: str,
    theme_name: str | None,
) -> dict[str, Any]:
    return {
        "record_id": record_id,
        "ticker": ticker,
        "display_name": ticker,
        "action": "继续持有",
        "role_label": role_label,
        "theme_name": theme_name,
    }


def test_decision_effectiveness_service_builds_summary_from_recent_reviews() -> None:
    service = DecisionEffectivenessService(
        decision_outcome_review_repository=cast(
            Any,
            FakeDecisionOutcomeReviewRepository(
                [
                    _make_review(
                        1,
                        ticker="SZSE:300308",
                        action="继续持有",
                        outcome_status="有效",
                        outcome_score=86,
                        summary="继续持有效果较稳。",
                    ),
                    _make_review(
                        2,
                        ticker="SZSE:002594",
                        action="纪律止损",
                        outcome_status="失效",
                        outcome_score=24,
                        summary="止损偏早。",
                    ),
                    _make_review(
                        3,
                        ticker="SZSE:000001",
                        action="持有观察",
                        outcome_status="部分有效",
                        outcome_score=62,
                        summary="观察节奏基本合理。",
                    ),
                    _make_review(
                        4,
                        ticker="SZSE:688256",
                        action="保护利润",
                        outcome_status="仍在观察",
                        outcome_score=45,
                        summary="窗口尚未走完。",
                    ),
                ]
            ),
        ),
        decision_record_service=cast(
            Any,
            FakeDecisionRecordService(
                [
                    _make_record(
                        1,
                        ticker="SZSE:300308",
                        role_label="龙头",
                        theme_name="AI算力",
                    ),
                    _make_record(
                        2,
                        ticker="SZSE:002594",
                        role_label="中军",
                        theme_name="新能源车",
                    ),
                    _make_record(
                        3,
                        ticker="SZSE:000001",
                        role_label="其他",
                        theme_name="金融",
                    ),
                    _make_record(
                        4,
                        ticker="SZSE:688256",
                        role_label="跟风",
                        theme_name="",
                    ),
                ]
            ),
        ),
    )

    result = service.get_summary(user_id="default_user")

    assert result["available"] is True
    assert result["review_count"] == 4
    assert result["effective_count"] == 1
    assert result["partially_effective_count"] == 1
    assert result["failed_count"] == 1
    assert result["observing_count"] == 1
    assert result["overall_score"] > 0
    assert "最近 40 天共回看 4 条判断" in result["overall_summary"]
    assert result["action_breakdown"][0]["label"] == "继续持有"
    assert result["role_breakdown"][0]["label"] == "龙头"
    assert result["theme_breakdown"][0]["label"] == "AI算力"
    assert result["recent_successes"][0]["ticker"] == "SZSE:300308"
    assert result["recent_failures"][0]["ticker"] == "SZSE:002594"


def test_decision_effectiveness_service_returns_empty_summary_without_recent_reviews() -> None:
    service = DecisionEffectivenessService(
        decision_outcome_review_repository=cast(
            Any,
            FakeDecisionOutcomeReviewRepository(
                [
                    _make_review(
                        5,
                        ticker="SZSE:300750",
                        action="继续持有",
                        outcome_status="有效",
                        outcome_score=82,
                        review_date=(date.today() - timedelta(days=400)).isoformat(),
                    )
                ]
            ),
        ),
        decision_record_service=cast(Any, FakeDecisionRecordService([])),
    )

    result = service.get_summary(user_id="default_user")

    assert result["available"] is False
    assert result["review_count"] == 0
    assert result["empty_message"] is not None
    assert result["recent_successes"] == []
