from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional

from ...db.repositories.decision_alert_repository import DecisionAlertRepository
from .decision_alert_service import DecisionAlertService


class DecisionAlertPersistenceService:
    def __init__(
        self,
        decision_alert_service: Optional[DecisionAlertService] = None,
        decision_alert_repository: Optional[DecisionAlertRepository] = None,
    ) -> None:
        self.decision_alert_service = decision_alert_service or DecisionAlertService()
        self.decision_alert_repository = decision_alert_repository or DecisionAlertRepository()

    def get_decision_alert_summary(self, user_id: str = "default_user") -> dict[str, Any]:
        self.refresh_alerts(user_id=user_id)
        items = self._serialize_alerts(
            self.decision_alert_repository.list_alerts(
                user_id=user_id,
                status="active",
                limit=20,
            )
        )
        return self.decision_alert_service.build_summary_payload(items)

    def list_alerts(
        self,
        *,
        user_id: str,
        status: str = "all",
        alert_type: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        alerts = self.decision_alert_repository.list_alerts(
            user_id=user_id,
            status=status,
            alert_type=alert_type,
            limit=limit,
        )
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "unread_count": self.decision_alert_repository.count_alerts(
                user_id=user_id,
                status="unread",
            ),
            "items": self._serialize_alerts(alerts),
            "count": len(alerts),
        }

    def refresh_alerts(self, user_id: str = "default_user") -> dict[str, Any]:
        alerts = self.decision_alert_service.build_decision_alerts(user_id=user_id)
        persisted_items: list[dict[str, Any]] = []
        for alert in alerts:
            persisted_items.append(self._upsert_alert(user_id=user_id, alert=alert))
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "unread_count": self.decision_alert_repository.count_alerts(
                user_id=user_id,
                status="unread",
            ),
            "items": persisted_items,
            "count": len(persisted_items),
        }

    def mark_alert_read(self, *, user_id: str, alert_id: int) -> dict[str, Any] | None:
        alert = self.decision_alert_repository.mark_alert_read(
            alert_id=alert_id,
            user_id=user_id,
        )
        return alert.to_dict() if alert else None

    def mark_all_read(self, *, user_id: str) -> dict[str, Any]:
        updated_count = self.decision_alert_repository.mark_all_read(user_id=user_id)
        return {
            "updated_count": updated_count,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    def dismiss_alert(self, *, user_id: str, alert_id: int) -> dict[str, Any] | None:
        alert = self.decision_alert_repository.dismiss_alert(
            alert_id=alert_id,
            user_id=user_id,
        )
        return alert.to_dict() if alert else None

    def _upsert_alert(self, *, user_id: str, alert: dict[str, Any]) -> dict[str, Any]:
        dedupe_key = self._build_dedupe_key(user_id=user_id, alert=alert)
        payload = {
            "user_id": user_id,
            "ticker": alert.get("ticker"),
            "display_name": alert.get("display_name"),
            "topic_name": alert.get("topic_name"),
            "alert_type": alert.get("alert_type"),
            "priority": alert.get("priority"),
            "title": alert.get("title"),
            "body": alert.get("body"),
            "next_action": alert.get("next_action"),
            "action": alert.get("action"),
            "confidence": int(alert.get("confidence") or 0),
            "source": alert.get("source"),
            "reasons_json": list(alert.get("reasons") or []),
            "payload_json": {
                "summary": alert.get("body"),
                "action": alert.get("action"),
                "confidence": int(alert.get("confidence") or 0),
                "topic_name": alert.get("topic_name"),
            },
            "dedupe_key": dedupe_key,
        }
        existing = self.decision_alert_repository.get_active_alert_by_dedupe_key(
            user_id=user_id,
            dedupe_key=dedupe_key,
        )
        if existing is None:
            created = self.decision_alert_repository.create_alert(payload)
            return created.to_dict() if created else {**alert, "dedupe_key": dedupe_key}

        updated = self.decision_alert_repository.update_alert(
            int(existing.id),
            {
                "display_name": payload["display_name"],
                "topic_name": payload["topic_name"],
                "priority": payload["priority"],
                "title": payload["title"],
                "body": payload["body"],
                "next_action": payload["next_action"],
                "confidence": payload["confidence"],
                "source": payload["source"],
                "reasons_json": payload["reasons_json"],
                "payload_json": payload["payload_json"],
                "updated_at": datetime.now(UTC),
            },
        )
        return updated.to_dict() if updated else {**alert, "dedupe_key": dedupe_key}

    @staticmethod
    def _build_dedupe_key(*, user_id: str, alert: dict[str, Any]) -> str:
        trade_day = datetime.now(UTC).date().isoformat()
        return "|".join(
            [
                user_id,
                str(alert.get("ticker") or ""),
                str(alert.get("alert_type") or ""),
                str(alert.get("action") or ""),
                trade_day,
            ]
        )

    @staticmethod
    def _serialize_alerts(alerts: list[Any]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for alert in alerts:
            if hasattr(alert, "to_dict"):
                result.append(alert.to_dict())
            elif isinstance(alert, dict):
                result.append(alert)
        return result


_decision_alert_persistence_service: Optional[DecisionAlertPersistenceService] = None


def get_decision_alert_persistence_service() -> DecisionAlertPersistenceService:
    global _decision_alert_persistence_service
    if _decision_alert_persistence_service is None:
        _decision_alert_persistence_service = DecisionAlertPersistenceService()
    return _decision_alert_persistence_service


def reset_decision_alert_persistence_service() -> None:
    global _decision_alert_persistence_service
    _decision_alert_persistence_service = None
