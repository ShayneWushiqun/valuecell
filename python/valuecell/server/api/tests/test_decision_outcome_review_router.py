from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.decision_outcome_review import (
    create_decision_outcome_review_router,
)


class FakeDecisionOutcomeReviewService:
    def __init__(self) -> None:
        self.capture_calls = 0
        self.refresh_calls = 0

    @staticmethod
    def _item() -> dict:
        return {
            "review_id": 1,
            "record_id": 11,
            "ticker": "SZSE:300308",
            "display_name": "中际旭创",
            "action": "继续持有",
            "lifecycle_stage": "主升持有期",
            "record_date": "2025-04-01",
            "review_date": "2025-04-10",
            "review_horizon_days": 5,
            "available": True,
            "outcome_status": "有效",
            "outcome_score": 82,
            "price_change_pct": 5.0,
            "max_favorable_excursion_pct": 7.0,
            "max_adverse_excursion_pct": -2.0,
            "entry_reference_price": 100.0,
            "exit_reference_price": 105.0,
            "summary": "继续持有在 5 日回看中判定为有效。",
            "what_happened": "走势继续延续。",
            "what_was_right": "延续性仍在。",
            "what_was_wrong": "暂无明显失配。",
            "followup_view": "继续结合新的时间窗复核。",
            "risk_after_signal": "最大回撤可控。",
            "context_consistency": "支持证据更多。",
            "linked_context_window_id": 11,
            "linked_event_ids_json": [101, 102],
            "empty_message": None,
        }

    def list_reviews(
        self,
        *,
        user_id: str,
        record_id: int | None = None,
        outcome_status: str | None = None,
        action: str | None = None,
        review_horizon_days: int | None = None,
        limit: int = 50,
    ):
        return {
            "generated_at": "2025-04-10T10:00:00Z",
            "items": [self._item()],
            "count": 1,
        }

    def get_review_detail(self, *, user_id: str, review_id: int):
        return self._item() if review_id == 1 else None

    def capture_review(
        self,
        *,
        user_id: str,
        record_id: int,
        review_horizon_days: int,
        review_date: str | None = None,
    ):
        self.capture_calls += 1
        if record_id == 999:
            return None
        item = self._item()
        item["record_id"] = record_id
        item["review_horizon_days"] = review_horizon_days
        item["review_date"] = review_date or item["review_date"]
        return item

    def refresh_reviews(
        self,
        *,
        user_id: str,
        review_horizon_days_list: list[int] | None = None,
        lookback_days: int = 60,
        limit_records: int = 30,
        review_date: str | None = None,
    ):
        self.refresh_calls += 1
        return self.list_reviews(user_id=user_id)


def test_decision_outcome_review_router_keeps_get_read_only_and_post_writes(monkeypatch) -> None:
    service = FakeDecisionOutcomeReviewService()
    monkeypatch.setattr(
        "valuecell.server.api.routers.decision_outcome_review.get_decision_outcome_review_service",
        lambda: service,
    )
    app = FastAPI()
    app.include_router(create_decision_outcome_review_router(), prefix="/api/v1")
    client = TestClient(app)

    list_response = client.get("/api/v1/decision-outcome-reviews")
    detail_response = client.get("/api/v1/decision-outcome-reviews/1")

    assert list_response.status_code == 200
    assert detail_response.status_code == 200
    assert service.capture_calls == 0
    assert service.refresh_calls == 0

    capture_response = client.post(
        "/api/v1/decision-outcome-reviews/capture",
        json={"record_id": 11, "review_horizon_days": 5, "review_date": "2025-04-10"},
    )
    refresh_response = client.post(
        "/api/v1/decision-outcome-reviews/refresh",
        json={"review_horizon_days_list": [5, 10], "lookback_days": 30, "limit_records": 20},
    )

    assert capture_response.status_code == 200
    assert refresh_response.status_code == 200
    assert service.capture_calls == 1
    assert service.refresh_calls == 1


def test_decision_outcome_review_router_returns_404_when_record_or_review_is_missing(
    monkeypatch,
) -> None:
    service = FakeDecisionOutcomeReviewService()
    monkeypatch.setattr(
        "valuecell.server.api.routers.decision_outcome_review.get_decision_outcome_review_service",
        lambda: service,
    )
    app = FastAPI()
    app.include_router(create_decision_outcome_review_router(), prefix="/api/v1")
    client = TestClient(app)

    missing_detail = client.get("/api/v1/decision-outcome-reviews/99")
    missing_capture = client.post(
        "/api/v1/decision-outcome-reviews/capture",
        json={"record_id": 999, "review_horizon_days": 5},
    )

    assert missing_detail.status_code == 404
    assert missing_capture.status_code == 404
