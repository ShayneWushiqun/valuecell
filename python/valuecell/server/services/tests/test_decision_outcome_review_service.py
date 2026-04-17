from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from valuecell.server.services.assets.decision_outcome_review_service import (
    DecisionOutcomeReviewService,
)


@dataclass
class FakeReviewRecord:
    id: int
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"review_id": self.id, **self.payload}


class FakeDecisionOutcomeReviewRepository:
    def __init__(self) -> None:
        self.items: dict[str, FakeReviewRecord] = {}
        self.next_id = 1

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
        records = list(self.items.values())
        if record_id is not None:
            records = [item for item in records if item.payload.get("record_id") == record_id]
        if outcome_status:
            records = [
                item for item in records if item.payload.get("outcome_status") == outcome_status
            ]
        if action:
            records = [item for item in records if item.payload.get("action") == action]
        if review_horizon_days is not None:
            records = [
                item
                for item in records
                if item.payload.get("review_horizon_days") == review_horizon_days
            ]
        return records[:limit]

    def get_review_by_id(self, *, user_id: str, review_id: int):
        for item in self.items.values():
            if item.id == review_id:
                return item
        return None

    def get_review_by_dedupe_key(self, *, user_id: str, dedupe_key: str):
        return self.items.get(dedupe_key)

    def create_review(self, payload: dict[str, Any]):
        item = FakeReviewRecord(self.next_id, dict(payload))
        self.items[str(payload["dedupe_key"])] = item
        self.next_id += 1
        return item

    def update_review(self, review_id: int, payload: dict[str, Any]):
        for key, item in self.items.items():
            if item.id == review_id:
                updated = FakeReviewRecord(review_id, {**item.payload, **payload})
                self.items[key] = updated
                return updated
        return None


class FakeDecisionRecordRepository:
    def __init__(self) -> None:
        self.updated_payloads: list[dict[str, Any]] = []

    def update_record(self, record_id: int, payload: dict[str, Any]):
        self.updated_payloads.append({"record_id": record_id, **payload})
        return None


class FakeDecisionRecordService:
    def __init__(self, records: dict[int, dict[str, Any]]) -> None:
        self.records = records

    def get_record_detail(self, *, user_id: str, record_id: int):
        return self.records.get(record_id)

    def list_records(self, *, user_id: str, limit: int = 20, action: str | None = None):
        items = list(self.records.values())
        if action:
            items = [item for item in items if item.get("action") == action]
        return {"generated_at": "2025-04-20T10:00:00Z", "items": items[:limit], "count": len(items)}


class FakeDecisionContextWindowService:
    def get_window_detail(self, *, user_id: str, window_id: int):
        return {
            "window_id": window_id,
            "support_events_json": [{"summary": "题材仍有承接"}],
            "opposing_events_json": [{"summary": "高位分歧"}],
            "risk_events_json": [{"summary": "追高风险"}],
        }

    def list_windows(self, *, user_id: str, ticker: str | None = None, limit: int = 1):
        return {
            "items": [
                {
                    "window_id": 11,
                    "support_events_json": [{"summary": "题材仍有承接"}],
                    "opposing_events_json": [],
                    "risk_events_json": [],
                }
            ]
        }


class FakeAShareDailySnapshotService:
    def get_snapshot_detail(self, *, user_id: str, snapshot_date: str):
        return {
            "market_digest": {"market_state": "震荡偏强"},
            "attention_digest": {"risk_alert_count": 1, "holding_risk_count": 2},
        }


class FakeAssetService:
    def __init__(self, price_map: dict[str, list[dict[str, Any]]]) -> None:
        self.price_map = price_map

    def get_historical_prices(
        self,
        ticker: str,
        start_date,
        end_date,
        interval: str = "1d",
        language: str | None = None,
    ):
        return {
            "success": True,
            "ticker": ticker,
            "interval": interval,
            "prices": list(self.price_map.get(ticker, [])),
            "count": len(self.price_map.get(ticker, [])),
        }


def _make_price_series(
    closes: list[float],
    *,
    start_date: str = "2025-04-01",
    high_offsets: list[float] | None = None,
    low_offsets: list[float] | None = None,
) -> list[dict[str, Any]]:
    year, month, day = (int(part) for part in start_date.split("-"))
    prices: list[dict[str, Any]] = []
    for index, close_price in enumerate(closes):
        high_offset = (high_offsets or [1.0] * len(closes))[index]
        low_offset = (low_offsets or [1.0] * len(closes))[index]
        trading_day = f"{year:04d}-{month:02d}-{day + index:02d}"
        prices.append(
            {
                "timestamp": f"{trading_day}T15:00:00+08:00",
                "price": close_price,
                "open_price": close_price,
                "high_price": close_price + high_offset,
                "low_price": max(0.01, close_price - low_offset),
                "close_price": close_price,
            }
        )
    return prices


def _make_record(record_id: int, *, action: str, ticker: str, record_date: str = "2025-04-01") -> dict[str, Any]:
    return {
        "record_id": record_id,
        "ticker": ticker,
        "display_name": ticker,
        "action": action,
        "lifecycle_stage": "主升持有期",
        "summary": "原始判断摘要",
        "context_snapshot_json": {},
        "context_window_id": 11,
        "linked_event_ids_json": [101, 102],
        "record_date": record_date,
    }


def test_decision_outcome_review_service_generates_valid_hold_review() -> None:
    repository = FakeDecisionOutcomeReviewRepository()
    record_repository = FakeDecisionRecordRepository()
    service = DecisionOutcomeReviewService(
        decision_outcome_review_repository=cast(Any, repository),
        decision_record_repository=cast(Any, record_repository),
        decision_record_service=cast(
            Any,
            FakeDecisionRecordService(
                {
                    1: _make_record(
                        1,
                        action="继续持有",
                        ticker="SZSE:300308",
                    )
                }
            ),
        ),
        decision_context_window_service=cast(Any, FakeDecisionContextWindowService()),
        ashare_daily_snapshot_service=cast(Any, FakeAShareDailySnapshotService()),
        asset_service=cast(
            Any,
            FakeAssetService(
                {
                    "SZSE:300308": _make_price_series(
                        [100, 101, 103, 104, 106, 105],
                        high_offsets=[1, 1, 2, 2, 2, 1],
                        low_offsets=[1, 1, 1, 1, 1, 1],
                    )
                }
            ),
        ),
    )

    review = service.capture_review(
        user_id="default_user",
        record_id=1,
        review_horizon_days=5,
        review_date="2025-04-10",
    )

    assert review is not None
    assert review["outcome_status"] == "有效"
    assert review["available"] is True
    assert review["linked_context_window_id"] == 11
    assert review["linked_event_ids_json"] == [101, 102]
    assert record_repository.updated_payloads[-1]["outcome_status"] == "有效"


def test_decision_outcome_review_service_returns_insufficient_when_prices_are_missing() -> None:
    service = DecisionOutcomeReviewService(
        decision_outcome_review_repository=cast(Any, FakeDecisionOutcomeReviewRepository()),
        decision_record_repository=cast(Any, FakeDecisionRecordRepository()),
        decision_record_service=cast(
            Any,
            FakeDecisionRecordService(
                {
                    2: _make_record(
                        2,
                        action="继续持有",
                        ticker="SZSE:000001",
                    )
                }
            ),
        ),
        decision_context_window_service=cast(Any, FakeDecisionContextWindowService()),
        ashare_daily_snapshot_service=cast(Any, FakeAShareDailySnapshotService()),
        asset_service=cast(
            Any,
            FakeAssetService(
                {
                    "SZSE:000001": _make_price_series([100, 101])[:1],
                }
            ),
        ),
    )

    review = service.capture_review(
        user_id="default_user",
        record_id=2,
        review_horizon_days=5,
        review_date="2025-05-10",
    )

    assert review is not None
    assert review["outcome_status"] == "数据不足"
    assert review["available"] is False
    assert review["empty_message"] is not None


def test_decision_outcome_review_service_splits_hold_valid_and_invalid() -> None:
    records = {
        1: _make_record(1, action="继续持有", ticker="SZSE:300308"),
        2: _make_record(2, action="继续持有", ticker="SZSE:300750"),
    }
    service = DecisionOutcomeReviewService(
        decision_outcome_review_repository=cast(Any, FakeDecisionOutcomeReviewRepository()),
        decision_record_repository=cast(Any, FakeDecisionRecordRepository()),
        decision_record_service=cast(Any, FakeDecisionRecordService(records)),
        decision_context_window_service=cast(Any, FakeDecisionContextWindowService()),
        ashare_daily_snapshot_service=cast(Any, FakeAShareDailySnapshotService()),
        asset_service=cast(
            Any,
            FakeAssetService(
                {
                    "SZSE:300308": _make_price_series([100, 101, 103, 104, 106, 105]),
                    "SZSE:300750": _make_price_series(
                        [100, 99, 96, 94, 93, 92],
                        high_offsets=[1, 1, 1, 1, 1, 1],
                        low_offsets=[2, 2, 2, 2, 2, 2],
                    ),
                }
            ),
        ),
    )

    valid_review = service.capture_review(
        user_id="default_user",
        record_id=1,
        review_horizon_days=5,
        review_date="2025-04-10",
    )
    invalid_review = service.capture_review(
        user_id="default_user",
        record_id=2,
        review_horizon_days=5,
        review_date="2025-04-10",
    )

    assert valid_review is not None and valid_review["outcome_status"] == "有效"
    assert invalid_review is not None and invalid_review["outcome_status"] == "失效"


def test_decision_outcome_review_service_splits_stop_valid_and_invalid() -> None:
    records = {
        3: _make_record(3, action="纪律止损", ticker="SZSE:002594"),
        4: _make_record(4, action="纪律止损", ticker="SZSE:688256"),
    }
    service = DecisionOutcomeReviewService(
        decision_outcome_review_repository=cast(Any, FakeDecisionOutcomeReviewRepository()),
        decision_record_repository=cast(Any, FakeDecisionRecordRepository()),
        decision_record_service=cast(Any, FakeDecisionRecordService(records)),
        decision_context_window_service=cast(Any, FakeDecisionContextWindowService()),
        ashare_daily_snapshot_service=cast(Any, FakeAShareDailySnapshotService()),
        asset_service=cast(
            Any,
            FakeAssetService(
                {
                    "SZSE:002594": _make_price_series(
                        [100, 97, 95, 93, 92, 90],
                        high_offsets=[1, 1, 1, 1, 1, 1],
                        low_offsets=[1, 1, 1, 1, 1, 1],
                    ),
                    "SZSE:688256": _make_price_series(
                        [100, 103, 105, 107, 109, 110],
                        high_offsets=[1, 1, 1, 1, 1, 1],
                        low_offsets=[1, 1, 1, 1, 1, 1],
                    ),
                }
            ),
        ),
    )

    valid_review = service.capture_review(
        user_id="default_user",
        record_id=3,
        review_horizon_days=5,
        review_date="2025-04-10",
    )
    invalid_review = service.capture_review(
        user_id="default_user",
        record_id=4,
        review_horizon_days=5,
        review_date="2025-04-10",
    )

    assert valid_review is not None and valid_review["outcome_status"] == "有效"
    assert invalid_review is not None and invalid_review["outcome_status"] == "失效"


def test_decision_outcome_review_service_protect_profit_is_not_only_about_missing_upside() -> None:
    service = DecisionOutcomeReviewService(
        decision_outcome_review_repository=cast(Any, FakeDecisionOutcomeReviewRepository()),
        decision_record_repository=cast(Any, FakeDecisionRecordRepository()),
        decision_record_service=cast(
            Any,
            FakeDecisionRecordService(
                {
                    5: _make_record(
                        5,
                        action="保护利润",
                        ticker="SZSE:000858",
                    )
                }
            ),
        ),
        decision_context_window_service=cast(Any, FakeDecisionContextWindowService()),
        ashare_daily_snapshot_service=cast(Any, FakeAShareDailySnapshotService()),
        asset_service=cast(
            Any,
            FakeAssetService(
                {
                    "SZSE:000858": _make_price_series(
                        [100, 104, 102, 98, 96, 102],
                        high_offsets=[1, 2, 1, 1, 1, 1],
                        low_offsets=[1, 1, 2, 3, 2, 1],
                    )
                }
            ),
        ),
    )

    review = service.capture_review(
        user_id="default_user",
        record_id=5,
        review_horizon_days=5,
        review_date="2025-04-10",
    )

    assert review is not None
    assert review["outcome_status"] == "有效"
    assert review["price_change_pct"] > 0


def test_decision_outcome_review_service_capture_updates_existing_review_instead_of_inserting() -> None:
    repository = FakeDecisionOutcomeReviewRepository()
    asset_service = FakeAssetService(
        {"SZSE:601899": _make_price_series([100, 101, 102, 103, 104, 105])}
    )
    service = DecisionOutcomeReviewService(
        decision_outcome_review_repository=cast(Any, repository),
        decision_record_repository=cast(Any, FakeDecisionRecordRepository()),
        decision_record_service=cast(
            Any,
            FakeDecisionRecordService(
                {
                    6: _make_record(
                        6,
                        action="继续持有",
                        ticker="SZSE:601899",
                    )
                }
            ),
        ),
        decision_context_window_service=cast(Any, FakeDecisionContextWindowService()),
        ashare_daily_snapshot_service=cast(Any, FakeAShareDailySnapshotService()),
        asset_service=cast(Any, asset_service),
    )

    first_review = service.capture_review(
        user_id="default_user",
        record_id=6,
        review_horizon_days=5,
        review_date="2025-04-10",
    )
    asset_service.price_map["SZSE:601899"] = _make_price_series([100, 99, 97, 96, 95, 94])
    second_review = service.capture_review(
        user_id="default_user",
        record_id=6,
        review_horizon_days=5,
        review_date="2025-04-10",
    )

    assert first_review is not None
    assert second_review is not None
    assert len(repository.items) == 1
    assert second_review["review_id"] == first_review["review_id"]
    assert second_review["outcome_status"] == "失效"
