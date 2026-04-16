from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional

from ...db.repositories.decision_record_repository import DecisionRecordRepository
from ..portfolio.holding_exit_signal_service import HoldingExitSignalService
from .ashare_daily_snapshot_service import AShareDailySnapshotService
from .holding_lifecycle_service import HoldingLifecycleService


class DecisionRecordService:
    def __init__(
        self,
        decision_record_repository: Optional[DecisionRecordRepository] = None,
        holding_lifecycle_service: Optional[HoldingLifecycleService] = None,
        holding_exit_signal_service: Optional[HoldingExitSignalService] = None,
        ashare_daily_snapshot_service: Optional[AShareDailySnapshotService] = None,
    ) -> None:
        self.decision_record_repository = (
            decision_record_repository or DecisionRecordRepository()
        )
        self.holding_lifecycle_service = (
            holding_lifecycle_service or HoldingLifecycleService()
        )
        self.holding_exit_signal_service = (
            holding_exit_signal_service or HoldingExitSignalService()
        )
        self.ashare_daily_snapshot_service = (
            ashare_daily_snapshot_service or AShareDailySnapshotService()
        )

    def list_records(
        self,
        *,
        user_id: str,
        limit: int = 20,
        action: str | None = None,
    ) -> dict[str, Any]:
        records = self.decision_record_repository.list_records(
            user_id=user_id,
            limit=limit,
            action=action,
        )
        items = [record.to_dict() for record in records]
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "items": items,
            "count": len(items),
        }

    def get_record_detail(self, *, user_id: str, record_id: int) -> dict[str, Any] | None:
        record = self.decision_record_repository.get_record_by_id(
            user_id=user_id,
            record_id=record_id,
        )
        return record.to_dict() if record else None

    def capture_records(self, *, user_id: str) -> dict[str, Any]:
        return self._upsert_records(user_id=user_id, source="capture")

    def refresh_records(self, *, user_id: str) -> dict[str, Any]:
        return self._upsert_records(user_id=user_id, source="refresh")

    def _upsert_records(self, *, user_id: str, source: str) -> dict[str, Any]:
        lifecycle_overview = self.holding_lifecycle_service.get_overview(user_id)
        exit_signal_result = self.holding_exit_signal_service.list_exit_signals(user_id)
        exit_signal_by_holding_id = {
            int(item.get("holding_id") or 0): item
            for item in list(exit_signal_result.get("items") or [])
            if int(item.get("holding_id") or 0) > 0
        }
        snapshot_context = self._load_latest_snapshot_context(user_id)
        record_date = datetime.now().astimezone().date().isoformat()
        saved_items: list[dict[str, Any]] = []
        for lifecycle_item in list(lifecycle_overview.get("items") or []):
            holding_id = int(lifecycle_item.get("holding_id") or 0)
            exit_signal = exit_signal_by_holding_id.get(holding_id)
            payload = self._build_record_payload(
                lifecycle_item=lifecycle_item,
                exit_signal=exit_signal,
                snapshot_context=snapshot_context,
                user_id=user_id,
                record_date=record_date,
                source=source,
            )
            existing = self.decision_record_repository.get_record_by_dedupe_key(
                user_id=user_id,
                dedupe_key=str(payload["dedupe_key"]),
            )
            if existing is None:
                saved = self.decision_record_repository.create_record(payload)
            else:
                saved = self.decision_record_repository.update_record(
                    int(existing.id),
                    {
                        key: value
                        for key, value in payload.items()
                        if key not in {"user_id", "dedupe_key", "record_date", "holding_id"}
                    },
                )
            saved_items.append(saved.to_dict() if saved else self._fallback_record(payload))
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "items": saved_items,
            "count": len(saved_items),
            "record_date": record_date,
        }

    def _load_latest_snapshot_context(self, user_id: str) -> dict[str, Any]:
        snapshot_list = self.ashare_daily_snapshot_service.list_snapshots(
            user_id=user_id,
            limit=1,
            include_today=True,
        )
        snapshot_item = next(iter(snapshot_list.get("items") or []), None)
        if not snapshot_item:
            return {}
        snapshot_date = str(snapshot_item.get("snapshot_date") or "")
        if not snapshot_date:
            return {}
        return self.ashare_daily_snapshot_service.get_snapshot_detail(
            user_id=user_id,
            snapshot_date=snapshot_date,
        ) or {}

    @staticmethod
    def _build_record_payload(
        *,
        lifecycle_item: dict[str, Any],
        exit_signal: dict[str, Any] | None,
        snapshot_context: dict[str, Any],
        user_id: str,
        record_date: str,
        source: str,
    ) -> dict[str, Any]:
        generated_at = datetime.now(UTC)
        decision_context = dict(((exit_signal or {}).get("context_snapshot") or {}).get("decision_context") or {})
        candidate_context = dict(decision_context.get("candidate_context") or {})
        theme_context = dict(decision_context.get("theme_context") or {})
        dedupe_key = "|".join(
            [
                user_id,
                str(lifecycle_item.get("holding_id") or 0),
                record_date,
                str(lifecycle_item.get("action") or ""),
                str(lifecycle_item.get("lifecycle_stage") or ""),
            ]
        )
        return {
            "user_id": user_id,
            "generated_at": generated_at,
            "record_date": record_date,
            "ticker": lifecycle_item.get("ticker"),
            "display_name": lifecycle_item.get("display_name") or lifecycle_item.get("ticker"),
            "holding_id": int(lifecycle_item.get("holding_id") or 0),
            "lifecycle_stage": lifecycle_item.get("lifecycle_stage"),
            "action": lifecycle_item.get("action"),
            "confidence": int(lifecycle_item.get("confidence") or 35),
            "summary": lifecycle_item.get("summary") or (exit_signal or {}).get("summary") or "保持观察。",
            "thesis": (exit_signal or {}).get("thesis") or "以持仓处理框架为主。",
            "evidence_json": list((exit_signal or {}).get("evidence") or []),
            "disagreement_json": list((exit_signal or {}).get("disagreement") or []),
            "invalid_conditions_json": list(lifecycle_item.get("invalid_conditions") or []),
            "risk_controls_json": list(lifecycle_item.get("risk_controls") or []),
            "theme_name": lifecycle_item.get("theme_name"),
            "role_label": lifecycle_item.get("role_label"),
            "tradeability_state": lifecycle_item.get("tradeability_state") or candidate_context.get("tradeability_state"),
            "expectation_state": lifecycle_item.get("expectation_state") or candidate_context.get("expectation_gap_level"),
            "source": source,
            "dedupe_key": dedupe_key,
            "context_snapshot_json": {
                "holding": {
                    "holding_id": lifecycle_item.get("holding_id"),
                    "ticker": lifecycle_item.get("ticker"),
                    "display_name": lifecycle_item.get("display_name"),
                },
                "lifecycle": {
                    "stage": lifecycle_item.get("lifecycle_stage"),
                    "action": lifecycle_item.get("action"),
                    "position_hint": lifecycle_item.get("position_hint"),
                    "observation_window": lifecycle_item.get("observation_window"),
                },
                "market_digest": snapshot_context.get("market_digest") or {},
                "attention_digest": snapshot_context.get("attention_digest") or {},
                "decision_context": {
                    "market_context": decision_context.get("market_context") or {},
                    "theme_context": theme_context,
                    "candidate_context": candidate_context,
                    "risk_context": decision_context.get("risk_context") or {},
                },
            },
            "outcome_status": "待复盘",
            "review_note": None,
        }

    @staticmethod
    def _fallback_record(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "record_id": 0,
            "generated_at": payload["generated_at"].isoformat(),
            "record_date": payload["record_date"],
            "ticker": payload["ticker"],
            "display_name": payload["display_name"],
            "holding_id": payload["holding_id"],
            "lifecycle_stage": payload["lifecycle_stage"],
            "action": payload["action"],
            "confidence": payload["confidence"],
            "summary": payload["summary"],
            "thesis": payload["thesis"],
            "evidence": list(payload["evidence_json"]),
            "disagreement": list(payload["disagreement_json"]),
            "invalid_conditions": list(payload["invalid_conditions_json"]),
            "risk_controls": list(payload["risk_controls_json"]),
            "theme_name": payload["theme_name"],
            "role_label": payload["role_label"],
            "tradeability_state": payload["tradeability_state"],
            "expectation_state": payload["expectation_state"],
            "source": payload["source"],
            "context_snapshot_json": payload["context_snapshot_json"],
            "outcome_status": payload["outcome_status"],
            "review_note": payload["review_note"],
        }


_decision_record_service: Optional[DecisionRecordService] = None


def get_decision_record_service() -> DecisionRecordService:
    global _decision_record_service
    if _decision_record_service is None:
        _decision_record_service = DecisionRecordService()
    return _decision_record_service


def reset_decision_record_service() -> None:
    global _decision_record_service
    _decision_record_service = None
