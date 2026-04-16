from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

from valuecell.server.services.assets.decision_record_service import DecisionRecordService


@dataclass
class FakeRecord:
    id: int
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"record_id": self.id, **self.payload}


class FakeDecisionRecordRepository:
    def __init__(self) -> None:
        self.records: dict[str, FakeRecord] = {}
        self.next_id = 1

    def get_record_by_dedupe_key(self, *, user_id: str, dedupe_key: str):
        return self.records.get(dedupe_key)

    def create_record(self, payload: dict[str, Any]):
        record = FakeRecord(self.next_id, self._serialize_payload(payload))
        self.records[str(payload["dedupe_key"])] = record
        self.next_id += 1
        return record

    def update_record(self, record_id: int, payload: dict[str, Any]):
        for key, record in self.records.items():
            if record.id == record_id:
                merged = {**record.payload, **self._serialize_payload(payload)}
                updated = FakeRecord(record_id, merged)
                self.records[key] = updated
                return updated
        return None

    def list_records(self, *, user_id: str, limit: int = 20, action: str | None = None):
        records = list(self.records.values())
        if action:
            records = [record for record in records if record.payload.get("action") == action]
        return records[:limit]

    def get_record_by_id(self, *, user_id: str, record_id: int):
        for record in self.records.values():
            if record.id == record_id:
                return record
        return None

    @staticmethod
    def _serialize_payload(payload: dict[str, Any]) -> dict[str, Any]:
        result = dict(payload)
        generated_at = result.get("generated_at")
        if isinstance(generated_at, datetime):
            result["generated_at"] = generated_at.isoformat()
        result["evidence"] = list(result.pop("evidence_json", []))
        result["disagreement"] = list(result.pop("disagreement_json", []))
        result["invalid_conditions"] = list(result.pop("invalid_conditions_json", []))
        result["risk_controls"] = list(result.pop("risk_controls_json", []))
        return result


class FakeHoldingLifecycleService:
    def get_overview(self, user_id: str = "default_user") -> dict[str, Any]:
        return {
            "generated_at": "2025-04-11T10:00:00Z",
            "items": [
                {
                    "holding_id": 1,
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "lifecycle_stage": "主升持有期",
                    "action": "继续持有",
                    "confidence": 66,
                    "summary": "趋势未坏。",
                    "theme_name": "AI算力",
                    "role_label": "龙头",
                    "tradeability_state": "可观察",
                    "expectation_state": "中",
                    "position_hint": "继续跟踪。",
                    "observation_window": "未来 3-5 个交易日。",
                    "invalid_conditions": ["跌破承接位"],
                    "risk_controls": ["不追高"],
                }
            ],
        }


class FakeHoldingExitSignalService:
    def list_exit_signals(self, user_id: str = "default_user") -> dict[str, Any]:
        return {
            "items": [
                {
                    "holding_id": 1,
                    "ticker": "SZSE:300308",
                    "summary": "趋势未坏。",
                    "thesis": "核心票保持承接。",
                    "evidence": ["角色为龙头"],
                    "disagreement": ["高位仍有分歧"],
                    "context_snapshot": {
                        "decision_context": {
                            "theme_context": {"topic_name": "AI算力", "role_label": "龙头"},
                            "candidate_context": {"tradeability_state": "可观察", "expectation_gap_level": "中"},
                            "risk_context": {"items": []},
                        }
                    },
                }
            ]
        }


class FakeAShareDailySnapshotService:
    def list_snapshots(self, *, user_id: str, limit: int = 20, include_today: bool = True):
        return {
            "items": [{"snapshot_date": "2025-04-11"}],
            "count": 1,
            "generated_at": "2025-04-11T10:00:00Z",
        }

    def get_snapshot_detail(self, *, user_id: str, snapshot_date: str):
        return {
            "market_digest": {"market_state": "震荡偏强"},
            "attention_digest": {"holding_risk_count": 1},
        }


def test_decision_record_service_upserts_daily_records() -> None:
    repository = FakeDecisionRecordRepository()
    service = DecisionRecordService(
        decision_record_repository=cast(Any, repository),
        holding_lifecycle_service=cast(Any, FakeHoldingLifecycleService()),
        holding_exit_signal_service=cast(Any, FakeHoldingExitSignalService()),
        ashare_daily_snapshot_service=cast(Any, FakeAShareDailySnapshotService()),
    )

    first = service.capture_records(user_id="default_user")
    second = service.refresh_records(user_id="default_user")
    listed = service.list_records(user_id="default_user", limit=10)
    detail = service.get_record_detail(user_id="default_user", record_id=1)

    assert first["count"] == 1
    assert second["count"] == 1
    assert listed["count"] == 1
    assert detail is not None
    assert detail["lifecycle_stage"] == "主升持有期"
    assert detail["context_snapshot_json"]["market_digest"]["market_state"] == "震荡偏强"
