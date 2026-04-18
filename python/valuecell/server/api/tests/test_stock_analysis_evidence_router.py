from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.stock_analysis_evidence import (
    create_stock_analysis_evidence_router,
)


class FakeMessageService:
    async def save_temporary_evidence_as_context(
        self,
        *,
        user_id: str,
        thread_id: int,
        message_id: str,
        evidence_index: int,
        pin: bool = False,
        custom_title: str | None = None,
    ):
        del user_id, message_id, evidence_index
        return {
            "context_id": 101,
            "thread_id": thread_id,
            "user_id": "default_user",
            "context_type": "temporary_evidence_saved",
            "title": custom_title or "保存后的证据",
            "subtitle": "tooling evidence",
            "ticker_refs_json": ["SZSE:300308"],
            "theme_refs_json": [],
            "summary": "保存后的证据摘要",
            "snapshot_payload_json": {"from_temporary_evidence": True},
            "source_module": "tooling_evidence",
            "source_ref": "item_2:0",
            "staleness_hint": "可能已过时",
            "is_pinned": pin,
            "created_at": "2026-04-18T10:00:00Z",
            "updated_at": "2026-04-18T10:00:00Z",
        }


def test_stock_analysis_evidence_router_saves_evidence(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.stock_analysis_evidence.get_stock_analysis_message_service",
        lambda: FakeMessageService(),
    )
    app = FastAPI()
    app.include_router(create_stock_analysis_evidence_router(), prefix="/api/v1")
    client = TestClient(app)

    response = client.post(
        "/api/v1/stock-analysis/threads/1/messages/item_2/save-evidence",
        json={"evidence_index": 0, "pin": True, "title": "外部新闻证据"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["context_card"]["context_type"] == "temporary_evidence_saved"
    assert response.json()["data"]["context_card"]["is_pinned"] is True
