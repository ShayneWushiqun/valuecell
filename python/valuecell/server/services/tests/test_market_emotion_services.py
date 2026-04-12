from __future__ import annotations

from typing import Any, cast

from valuecell.server.services.assets.emotion_cycle_service import (
    EmotionCycleService,
)
from valuecell.server.services.assets.market_pulse_service import (
    MarketPulseService,
)


class FakeShortCycleDataService:
    def __init__(self):
        self.market_by_date = {
            "20250408": self._market_payload(28, 11, 9, 2, 6, 5),
            "20250409": self._market_payload(42, 7, 5, 3, 10, 18),
            "20250410": self._market_payload(78, 2, 3, 5, 12, 24),
        }

    def get_market_pulse_data(self, trade_date=None):
        key = str(trade_date or "20250410").replace("-", "")
        payload = self.market_by_date.get(key, self.market_by_date["20250410"])
        return {
            "success": True,
            "trade_date": key,
            "data": payload,
        }

    def get_market_pulse_window_data(self, start_date, end_date, max_points=7):
        items = [
            self.get_market_pulse_data("20250408"),
            self.get_market_pulse_data("20250409"),
            self.get_market_pulse_data("20250410"),
        ]
        return {
            "success": True,
            "scope": "market_pulse_window",
            "items": items[-max_points:],
        }

    @staticmethod
    def _market_payload(
        up_limit: int,
        down_limit: int,
        broken_limit: int,
        highest_board: int,
        active_board_count: int,
        hot_count: int,
    ):
        limit_rows = [{"limit": "涨停"}] * up_limit + [{"limit": "跌停"}] * down_limit
        limit_rows.extend([{"limit": "炸板"}] * broken_limit)
        kpl_rows = [
            {"high_days": highest_board, "reason_type": f"方向{i}"}
            for i in range(active_board_count)
        ]
        hot_rows = [{"ticker": f"SZSE:{i:06d}"} for i in range(hot_count)]
        return {
            "daily_info": {
                "count": 1,
                "columns": ["trade_date", "up_limit", "down_limit", "broken_limit"],
                "rows": [
                    {
                        "trade_date": "20250410",
                        "up_limit": up_limit,
                        "down_limit": down_limit,
                        "broken_limit": broken_limit,
                    }
                ],
            },
            "limit_list_d": {
                "count": len(limit_rows),
                "columns": ["limit"],
                "rows": limit_rows,
            },
            "kpl_list": {
                "count": len(kpl_rows),
                "columns": ["high_days", "reason_type"],
                "rows": kpl_rows,
            },
            "ths_hot": {
                "count": len(hot_rows),
                "columns": ["ticker"],
                "rows": hot_rows,
            },
        }


class CountingMarketPulseService(MarketPulseService):
    def __init__(self, short_cycle_data_service: FakeShortCycleDataService) -> None:
        super().__init__(short_cycle_data_service=cast(Any, short_cycle_data_service))
        self.snapshot_calls = 0

    def get_market_pulse_snapshot(self, trade_date=None):
        self.snapshot_calls += 1
        return super().get_market_pulse_snapshot(trade_date)


def test_emotion_cycle_service_penalizes_extreme_weak_day() -> None:
    snapshot = {
        "metrics": {
            "up_limit_count": 28,
            "down_limit_count": 70,
            "broken_limit_count": 0,
            "active_board_count": 36,
            "strongest_board_height": 0,
        },
        "market_state": "轮动",
    }

    stage_score = EmotionCycleService._calculate_stage_score(snapshot)
    cycle_stage = EmotionCycleService._resolve_cycle_stage(snapshot, stage_score)

    assert stage_score <= 20
    assert cycle_stage == "冰点"


def test_market_pulse_service_returns_structured_snapshot() -> None:
    service = MarketPulseService(
        short_cycle_data_service=cast(Any, FakeShortCycleDataService())
    )

    result = service.get_market_pulse_snapshot("20250410")

    assert result["success"] is True
    data = result["data"]
    assert data["market_state"] == "进攻"
    assert data["confidence"] in {"中", "高"}
    assert data["metrics"]["up_limit_count"] == 78
    assert data["signals_json"]


def test_emotion_cycle_service_returns_snapshot_stage() -> None:
    short_cycle_service = FakeShortCycleDataService()
    market_pulse_service = MarketPulseService(
        short_cycle_data_service=cast(Any, short_cycle_service)
    )
    service = EmotionCycleService(
        market_pulse_service=market_pulse_service,
        short_cycle_data_service=cast(Any, short_cycle_service),
    )

    result = service.get_emotion_cycle_snapshot("20250410")

    assert result["success"] is True
    assert result["data"]["cycle_stage"] in {"主升发酵", "高潮一致"}
    assert result["data"]["stage_score"] >= 60


def test_emotion_cycle_service_returns_timeline_with_turning_points() -> None:
    short_cycle_service = FakeShortCycleDataService()
    market_pulse_service = MarketPulseService(
        short_cycle_data_service=cast(Any, short_cycle_service)
    )
    service = EmotionCycleService(
        market_pulse_service=market_pulse_service,
        short_cycle_data_service=cast(Any, short_cycle_service),
    )

    result = service.get_emotion_cycle_timeline(end_date="2025-04-10", window_days=3)

    assert result["success"] is True
    data = result["data"]
    assert data["window_days"] == 3
    assert len(data["stage_points_json"]) == 3
    assert data["trend_direction"] in {"上行", "横向", "下行"}
    assert isinstance(data["turning_points_json"], list)
    assert data["stage_points_json"][0]["stage_score"] < data["stage_points_json"][-1]["stage_score"]
    assert data["stage_points_json"][0]["up_limit_count"] == 28
    assert data["stage_points_json"][0]["down_limit_count"] == 11
    assert data["stage_points_json"][0]["broken_limit_count"] == 9
    assert data["stage_points_json"][0]["highest_board"] == 2
    assert data["stage_points_json"][0]["action_hint"]


def test_emotion_cycle_service_reuses_window_item_data_when_complete() -> None:
    short_cycle_service = FakeShortCycleDataService()
    market_pulse_service = CountingMarketPulseService(short_cycle_service)
    service = EmotionCycleService(
        market_pulse_service=market_pulse_service,
        short_cycle_data_service=cast(Any, short_cycle_service),
    )

    result = service.get_emotion_cycle_timeline(end_date="2025-04-10", window_days=3)

    assert result["success"] is True
    assert market_pulse_service.snapshot_calls == 0
