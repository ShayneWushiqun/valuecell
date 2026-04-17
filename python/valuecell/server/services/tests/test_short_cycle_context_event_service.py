from __future__ import annotations

from typing import Any, cast

from valuecell.server.services.assets.short_cycle_context_event_service import (
    ShortCycleContextEventService,
)


class FakeEvent:
    def __init__(self, event_id: int, payload: dict[str, Any]) -> None:
        self.id = event_id
        self.payload = payload

    def to_dict(self) -> dict[str, Any]:
        return {"event_id": self.id, **self.payload}


class FakeShortCycleContextEventRepository:
    def __init__(self) -> None:
        self.items: dict[str, FakeEvent] = {}
        self.next_id = 1

    def list_events(self, *, user_id: str, ticker: str | None = None, limit: int = 200):
        records = list(self.items.values())
        if ticker:
            records = [record for record in records if record.payload.get("ticker") == ticker]
        return records[:limit]

    def get_event_by_id(self, *, user_id: str, event_id: int):
        for item in self.items.values():
            if item.id == event_id:
                return item
        return None

    def get_event_by_dedupe_key(self, *, user_id: str, dedupe_key: str):
        return self.items.get(dedupe_key)

    def create_event(self, payload: dict[str, Any]):
        serialized = self._serialize(payload)
        item = FakeEvent(self.next_id, serialized)
        self.items[str(payload["dedupe_key"])] = item
        self.next_id += 1
        return item

    def update_event(self, event_id: int, payload: dict[str, Any]):
        for key, item in self.items.items():
            if item.id == event_id:
                merged = {**item.payload, **self._serialize(payload)}
                updated = FakeEvent(event_id, merged)
                self.items[key] = updated
                return updated
        return None

    @staticmethod
    def _serialize(payload: dict[str, Any]) -> dict[str, Any]:
        result = dict(payload)
        result["occurred_at"] = payload["occurred_at"].isoformat()
        result["ingested_at"] = payload["ingested_at"].isoformat()
        return result


class FakeHoldingLifecycleService:
    def get_overview(self, user_id: str = "default_user") -> dict[str, Any]:
        return {
            "items": [
                {
                    "holding_id": 1,
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "theme_name": "AI算力",
                    "lifecycle_stage": "主升持有期",
                    "action": "继续持有",
                    "summary": "趋势未坏。",
                    "confidence": 66,
                    "role_label": "龙头",
                    "trend_quality": "顺势",
                    "tradeability_state": "可观察",
                    "invalid_conditions": ["跌破承接位"],
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
                    "holding_id": 1,
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "action": "继续持有",
                    "summary": "继续观察。",
                    "thesis": "趋势未坏。",
                    "confidence": 52,
                    "risk_type": "节奏转弱",
                    "risk_controls": ["不追高"],
                    "liquidity_warning": None,
                    "expected_exit_plan": "继续跟踪。",
                    "theme_name": "AI算力",
                    "role_label": "龙头",
                }
            ],
        }


class FakeDecisionRecordService:
    def list_records(self, *, user_id: str, limit: int = 20, action: str | None = None):
        return {
            "items": [
                {
                    "record_id": 10,
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "action": "继续持有",
                    "lifecycle_stage": "主升持有期",
                    "summary": "已有记录。",
                    "confidence": 63,
                    "theme_name": "AI算力",
                }
            ]
        }


class FakeOpportunityPoolService:
    def get_opportunity_candidates(self, user_id: str = "default_user") -> dict[str, Any]:
        return {
            "items": [
                {
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "topic_name": "AI算力",
                    "candidate_state": "高优先级买点",
                    "priority_score": 84,
                    "tradeability_state": "可观察",
                    "expectation_gap_level": "中",
                    "action_hint": "值得继续观察。",
                }
            ]
        }


class FakeThemeRadarService:
    def get_overview(self, user_id: str = "default_user") -> dict[str, Any]:
        return {
            "items": [
                {
                    "theme_name": "AI算力",
                    "theme_state": "加强",
                    "score": 88,
                    "participation_hint": "优先跟踪核心票。",
                    "observation_summary": "AI算力当前继续加强。",
                    "watchlist_resonance_count": 1,
                    "opportunity_resonance_count": 1,
                }
            ]
        }


class FakeWatchlistCenterService:
    def get_overview(self, user_id: str = "default_user") -> dict[str, Any]:
        return {
            "items": [
                {
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "theme_name": "AI算力",
                    "tradeability_state": "可观察",
                    "reason": "与主线共振。",
                    "quick_note": "观察优先级更高。",
                    "observation_priority": "高",
                    "linked_candidate_state": "高优先级买点",
                    "linked_judge_action": "接近可参与窗口",
                    "has_theme_resonance": True,
                    "has_opportunity_link": True,
                }
            ]
        }


class FakeDecisionAlertPersistenceService:
    def list_alerts(
        self,
        *,
        user_id: str,
        status: str = "all",
        alert_type: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        return {
            "items": [
                {
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "title": "接近观察窗口",
                    "alert_type": "near_entry",
                    "priority": "medium",
                    "action": "接近可参与窗口",
                    "confidence": 65,
                    "next_action": "继续确认。",
                }
            ]
        }


class FakeHomepageContextService:
    def get_homepage_context(self, user_id: str = "default_user") -> dict[str, Any]:
        return {
            "market_overview": {
                "market_state": "震荡偏强",
                "summary": "市场情绪仍在修复。",
            },
            "emotion_cycle": {"cycle_stage": "修复期", "temperature_score": 62},
        }


def test_short_cycle_context_event_service_builds_normalized_events() -> None:
    repository = FakeShortCycleContextEventRepository()
    service = ShortCycleContextEventService(
        short_cycle_context_event_repository=cast(Any, repository),
        holding_lifecycle_service=cast(Any, FakeHoldingLifecycleService()),
        exit_risk_center_service=cast(Any, FakeExitRiskCenterService()),
        decision_record_service=cast(Any, FakeDecisionRecordService()),
        opportunity_pool_service=cast(Any, FakeOpportunityPoolService()),
        theme_radar_service=cast(Any, FakeThemeRadarService()),
        watchlist_center_service=cast(Any, FakeWatchlistCenterService()),
        decision_alert_persistence_service=cast(Any, FakeDecisionAlertPersistenceService()),
        homepage_context_service=cast(Any, FakeHomepageContextService()),
    )

    refreshed = service.refresh_events(user_id="default_user")
    listed = service.list_events(user_id="default_user", ticker="SZSE:300308", limit=50)

    assert refreshed["count"] >= 5
    assert listed["count"] >= 5
    assert any(item["layer"] == "market" for item in listed["items"])
    assert any(item["layer"] == "theme" for item in listed["items"])
    assert any(item["source"] == "decision_records" for item in listed["items"])
