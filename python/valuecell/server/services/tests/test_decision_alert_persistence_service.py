from __future__ import annotations

from typing import Any, cast

from valuecell.server.services.assets.decision_alert_persistence_service import (
    DecisionAlertPersistenceService,
)


class FakeAlertRecord:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.id = payload.get("id")

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)


class FakeDecisionAlertService:
    def __init__(self) -> None:
        self.build_calls = 0

    def build_decision_alerts(self, user_id: str = "default_user") -> list[dict[str, Any]]:
        self.build_calls += 1
        return [
            {
                "ticker": "SZSE:300308",
                "display_name": "中际旭创",
                "topic_name": "AI算力",
                "alert_type": "买点接近",
                "priority": "high",
                "title": "中际旭创 接近可参与窗口",
                "body": "中际旭创 当前更接近可参与窗口，但仍需确认。",
                "next_action": "继续观察承接、量价与回踩确认。",
                "action": "接近可参与窗口",
                "confidence": 76,
                "source": "entry_timing_signals",
                "reasons": ["当前信号更接近可参与窗口，但仍需确认。"],
            },
            {
                "ticker": "SZSE:000007",
                "display_name": "ST全新",
                "topic_name": "ST板块",
                "alert_type": "风险回避",
                "priority": "medium",
                "title": "ST全新 当前应风险回避",
                "body": "ST全新 当前存在风险条件，先回避 ST板块 方向。",
                "next_action": "先回避，重点关注：疑似 ST 或高风险方向，默认回避。",
                "action": "暂不参与",
                "confidence": 33,
                "source": "entry_timing_signals",
                "reasons": ["存在明确风险条件，应优先风险回避。"],
            },
        ]

    def build_summary_payload(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "generated_at": "2025-04-10T10:10:00Z",
            "available": bool(items),
            "items": items,
            "count": len(items),
            "empty_message": None if items else "暂无可用提醒摘要",
        }


class FakeDecisionAlertRepository:
    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []
        self.next_id = 1

    def get_active_alert_by_dedupe_key(self, *, user_id: str, dedupe_key: str):
        for item in self.items:
            if (
                item["user_id"] == user_id
                and item["dedupe_key"] == dedupe_key
                and item.get("dismissed_at") is None
            ):
                return FakeAlertRecord(item)
        return None

    def create_alert(self, payload: dict[str, Any]):
        item = {
            **payload,
            "id": self.next_id,
            "read_at": None,
            "dismissed_at": None,
            "created_at": "2025-04-10T10:00:00Z",
            "updated_at": "2025-04-10T10:00:00Z",
            "reasons": list(payload.get("reasons_json") or []),
        }
        self.next_id += 1
        self.items.append(item)
        return FakeAlertRecord(item)

    def update_alert(self, alert_id: int, payload: dict[str, Any]):
        for index, item in enumerate(self.items):
            if item["id"] == alert_id:
                updated = {
                    **item,
                    **payload,
                    "reasons": list(payload.get("reasons_json") or item.get("reasons") or []),
                }
                self.items[index] = updated
                return FakeAlertRecord(updated)
        return None

    def list_alerts(self, *, user_id: str, status: str = "all", alert_type: str | None = None, limit: int = 50):
        items = [item for item in self.items if item["user_id"] == user_id]
        if status == "dismissed":
            items = [item for item in items if item.get("dismissed_at") is not None]
        elif status == "active":
            items = [item for item in items if item.get("dismissed_at") is None]
        else:
            if status == "unread":
                items = [item for item in items if item.get("dismissed_at") is None]
                items = [item for item in items if item.get("read_at") is None]
            elif status == "read":
                items = [item for item in items if item.get("dismissed_at") is None]
                items = [item for item in items if item.get("read_at") is not None]
        if alert_type:
            items = [item for item in items if item.get("alert_type") == alert_type]
        return [FakeAlertRecord(item) for item in items[:limit]]

    def count_alerts(self, *, user_id: str, status: str = "all", alert_type: str | None = None) -> int:
        return len(
            self.list_alerts(
                user_id=user_id,
                status=status,
                alert_type=alert_type,
                limit=999,
            )
        )

    def mark_alert_read(self, *, alert_id: int, user_id: str):
        return self.update_alert(alert_id, {"read_at": "2025-04-10T10:30:00Z"})

    def mark_all_read(self, *, user_id: str) -> int:
        updated_count = 0
        for item in self.items:
            if item["user_id"] == user_id and item.get("dismissed_at") is None and item.get("read_at") is None:
                item["read_at"] = "2025-04-10T10:30:00Z"
                updated_count += 1
        return updated_count

    def dismiss_alert(self, *, alert_id: int, user_id: str):
        return self.update_alert(alert_id, {"dismissed_at": "2025-04-10T10:40:00Z"})


def test_decision_alert_persistence_service_refreshes_and_dedupes_alerts() -> None:
    repository = FakeDecisionAlertRepository()
    alert_service = FakeDecisionAlertService()
    service = DecisionAlertPersistenceService(
        decision_alert_service=cast(Any, alert_service),
        decision_alert_repository=cast(Any, repository),
    )

    first_refresh = service.refresh_alerts(user_id="default_user")
    second_refresh = service.refresh_alerts(user_id="default_user")

    assert first_refresh["count"] == 2
    assert second_refresh["count"] == 2
    assert len(repository.items) == 2
    assert alert_service.build_calls == 2


def test_decision_alert_persistence_service_supports_read_and_dismiss() -> None:
    repository = FakeDecisionAlertRepository()
    service = DecisionAlertPersistenceService(
        decision_alert_service=cast(Any, FakeDecisionAlertService()),
        decision_alert_repository=cast(Any, repository),
    )

    service.refresh_alerts(user_id="default_user")
    mark_read_result = service.mark_alert_read(user_id="default_user", alert_id=1)
    dismiss_result = service.dismiss_alert(user_id="default_user", alert_id=2)
    list_result = service.list_alerts(user_id="default_user", status="active", limit=50)
    dismissed_result = service.list_alerts(
        user_id="default_user",
        status="dismissed",
        limit=50,
    )

    assert mark_read_result is not None
    assert mark_read_result["read_at"] is not None
    assert dismiss_result is not None
    assert dismiss_result["dismissed_at"] is not None
    assert list_result["count"] == 1
    assert dismissed_result["count"] == 1


def test_decision_alert_summary_is_read_only_and_uses_existing_active_alerts() -> None:
    repository = FakeDecisionAlertRepository()
    alert_service = FakeDecisionAlertService()
    service = DecisionAlertPersistenceService(
        decision_alert_service=cast(Any, alert_service),
        decision_alert_repository=cast(Any, repository),
    )

    summary_before_refresh = service.get_decision_alert_summary(user_id="default_user")

    assert summary_before_refresh["available"] is False
    assert summary_before_refresh["count"] == 0
    assert alert_service.build_calls == 0

    service.refresh_alerts(user_id="default_user")
    summary_after_refresh = service.get_decision_alert_summary(user_id="default_user")

    assert summary_after_refresh["available"] is True
    assert summary_after_refresh["count"] == 2
    assert alert_service.build_calls == 1
