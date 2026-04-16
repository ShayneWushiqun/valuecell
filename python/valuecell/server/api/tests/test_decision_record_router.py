from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.decision_record import create_decision_record_router


class FakeDecisionRecordService:
    def list_records(self, *, user_id: str, limit: int = 20, action: str | None = None):
        return {
            "generated_at": "2025-04-11T10:00:00Z",
            "items": [
                {
                    "record_id": 1,
                    "generated_at": "2025-04-11T10:00:00Z",
                    "record_date": "2025-04-11",
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "holding_id": 1,
                    "lifecycle_stage": "主升持有期",
                    "action": "继续持有",
                    "confidence": 66,
                    "summary": "趋势未坏。",
                    "thesis": "核心票保持承接。",
                    "evidence": ["角色为龙头"],
                    "disagreement": ["高位仍有分歧"],
                    "invalid_conditions": ["跌破承接位"],
                    "risk_controls": ["不追高"],
                    "theme_name": "AI算力",
                    "role_label": "龙头",
                    "tradeability_state": "可观察",
                    "expectation_state": "中",
                    "source": "capture",
                    "context_snapshot_json": {},
                    "outcome_status": "待复盘",
                    "review_note": None,
                }
            ],
            "count": 1,
        }

    def get_record_detail(self, *, user_id: str, record_id: int):
        return self.list_records(user_id=user_id)["items"][0]

    def capture_records(self, *, user_id: str):
        return {**self.list_records(user_id=user_id), "record_date": "2025-04-11"}

    def refresh_records(self, *, user_id: str):
        return {**self.list_records(user_id=user_id), "record_date": "2025-04-11"}


def test_decision_record_router_supports_list_detail_capture_and_refresh(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.decision_record.get_decision_record_service",
        lambda: FakeDecisionRecordService(),
    )
    app = FastAPI()
    app.include_router(create_decision_record_router(), prefix="/api/v1")
    client = TestClient(app)

    list_response = client.get("/api/v1/decision-records")
    detail_response = client.get("/api/v1/decision-records/1")
    capture_response = client.post("/api/v1/decision-records/capture")
    refresh_response = client.post("/api/v1/decision-records/refresh")

    assert list_response.status_code == 200
    assert list_response.json()["data"]["count"] == 1
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["record_id"] == 1
    assert capture_response.status_code == 200
    assert capture_response.json()["data"]["record_date"] == "2025-04-11"
    assert refresh_response.status_code == 200
