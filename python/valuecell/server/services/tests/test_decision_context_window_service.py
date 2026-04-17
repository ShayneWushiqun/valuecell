from __future__ import annotations

from typing import Any, cast

from valuecell.server.services.assets.decision_context_window_service import (
    DecisionContextWindowService,
)


class FakeWindow:
    def __init__(self, window_id: int, payload: dict[str, Any]) -> None:
        self.id = window_id
        self.payload = payload

    def to_dict(self) -> dict[str, Any]:
        return {"window_id": self.id, **self.payload}


class FakeDecisionContextWindowRepository:
    def __init__(self) -> None:
        self.items: dict[str, FakeWindow] = {}
        self.next_id = 1

    def list_windows(self, *, user_id: str, ticker: str | None = None, window_size: int | None = None, limit: int = 100):
        records = list(self.items.values())
        if ticker:
            records = [record for record in records if record.payload.get("ticker") == ticker]
        if window_size:
            records = [record for record in records if record.payload.get("window_size") == window_size]
        return records[:limit]

    def get_window_by_id(self, *, user_id: str, window_id: int):
        for item in self.items.values():
            if item.id == window_id:
                return item
        return None

    def get_window_by_dedupe_key(self, *, user_id: str, dedupe_key: str):
        return self.items.get(dedupe_key)

    def create_window(self, payload: dict[str, Any]):
        item = FakeWindow(self.next_id, dict(payload))
        self.items[str(payload["dedupe_key"])] = item
        self.next_id += 1
        return item

    def update_window(self, window_id: int, payload: dict[str, Any]):
        for key, item in self.items.items():
            if item.id == window_id:
                merged = {**item.payload, **payload}
                updated = FakeWindow(window_id, merged)
                self.items[key] = updated
                return updated
        return None


class FakeEventItem:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)


class FakeShortCycleContextEventRepository:
    def list_events(self, *, user_id: str, ticker: str | None = None, limit: int = 200):
        items = [
            FakeEventItem(
                {
                    "event_id": 1,
                    "ticker": "SZSE:300308",
                    "record_date": "2099-01-01",
                    "layer": "market",
                    "event_type": "market_state_snapshot",
                    "source": "homepage_context",
                    "direction": "bullish",
                    "importance_score": 55,
                    "summary": "市场修复。",
                    "tradeability_hint": None,
                    "payload_json": {"market_state": "震荡偏强"},
                }
            ),
            FakeEventItem(
                {
                    "event_id": 2,
                    "ticker": "SZSE:300308",
                    "record_date": "2099-01-01",
                    "layer": "theme",
                    "event_type": "theme_加强",
                    "source": "theme_radar",
                    "direction": "bullish",
                    "importance_score": 82,
                    "summary": "题材继续加强。",
                    "tradeability_hint": "优先跟踪核心票。",
                    "payload_json": {},
                }
            ),
            FakeEventItem(
                {
                    "event_id": 3,
                    "ticker": "SZSE:300308",
                    "record_date": "2099-01-01",
                    "layer": "risk_filter",
                    "event_type": "alert_near_entry",
                    "source": "decision_alerts",
                    "direction": "risk",
                    "importance_score": 68,
                    "summary": "追高风险仍在。",
                    "tradeability_hint": "先确认。",
                    "payload_json": {},
                }
            ),
        ]
        if ticker:
            items = [item for item in items if item.payload.get("ticker") == ticker]
        return items[:limit]


class FakeShortCycleContextEventService:
    def refresh_events(self, *, user_id: str, ticker: str | None = None):
        return {
            "items": [
                {"ticker": ticker or "SZSE:300308"},
            ],
            "count": 1,
        }


class FakeHoldingLifecycleService:
    def get_overview(self, user_id: str = "default_user") -> dict[str, Any]:
        return {
            "items": [
                {
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "theme_name": "AI算力",
                    "lifecycle_stage": "主升持有期",
                    "expectation_state": "中",
                    "tradeability_state": "可观察",
                    "role_label": "龙头",
                    "trend_quality": "顺势",
                }
            ]
        }


class FakeExitRiskCenterService:
    def get_overview(self, user_id: str = "default_user") -> dict[str, Any]:
        return {
            "high_priority_items": [],
            "profit_protection_items": [],
            "discipline_stop_items": [],
            "watch_items": [
                {
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "action": "继续持有",
                    "liquidity_warning": None,
                    "risk_type": "节奏转弱",
                    "theme_name": "AI算力",
                }
            ],
        }


class FakeAShareDecisionJudgeService:
    def judge(
        self,
        *,
        ticker: str,
        user_id: str = "default_user",
        enable_agent: bool = False,
        force_refresh_context: bool = False,
        user_note: str | None = None,
    ) -> dict[str, Any]:
        return {
            "action": "继续观察",
            "confidence": 54,
            "summary": "仍需继续确认。",
            "invalid_conditions": ["失效条件"],
            "risk_controls": ["风控提示"],
        }


class FakeDecisionRecordService:
    def list_records(self, *, user_id: str, limit: int = 20, action: str | None = None):
        return {
            "items": [
                {
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "theme_name": "AI算力",
                    "role_label": "龙头",
                    "expectation_state": "中",
                }
            ]
        }


def test_decision_context_window_service_builds_support_opposing_risk_windows() -> None:
    service = DecisionContextWindowService(
        decision_context_window_repository=cast(Any, FakeDecisionContextWindowRepository()),
        short_cycle_context_event_repository=cast(Any, FakeShortCycleContextEventRepository()),
        short_cycle_context_event_service=cast(Any, FakeShortCycleContextEventService()),
        holding_lifecycle_service=cast(Any, FakeHoldingLifecycleService()),
        exit_risk_center_service=cast(Any, FakeExitRiskCenterService()),
        ashare_decision_judge_service=cast(Any, FakeAShareDecisionJudgeService()),
        decision_record_service=cast(Any, FakeDecisionRecordService()),
    )

    refreshed = service.refresh_windows(user_id="default_user", ticker="SZSE:300308")
    listed = service.list_windows(user_id="default_user", ticker="SZSE:300308")

    assert refreshed["count"] == 3
    assert listed["count"] == 3
    assert listed["items"][0]["support_count"] >= 1
    assert listed["items"][0]["risk_count"] >= 1
    assert listed["items"][0]["judgement_snapshot_json"]["action"] == "继续观察"
