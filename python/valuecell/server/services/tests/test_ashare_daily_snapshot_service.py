from __future__ import annotations

from typing import Any, cast

from valuecell.server.services.assets.ashare_daily_snapshot_service import (
    AShareDailySnapshotService,
)


class FakeSnapshotRecord:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.id = payload.get("id")

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)


class FakeWorkbenchService:
    def __init__(self) -> None:
        self.overview_calls = 0

    def get_overview(self, user_id: str = "default_user") -> dict[str, Any]:
        self.overview_calls += 1
        return {
            "generated_at": "2025-04-10T10:55:00+00:00",
            "available": True,
            "empty_message": None,
            "market_digest": {
                "market_state": "震荡偏强",
                "emotion_stage": "主升分歧",
                "temperature_score": 68,
                "action_rhythm": "先看风险，再看持仓，再看机会。",
                "summary": "指数震荡，主线保持活跃。",
            },
            "attention_digest": {
                "unread_alert_count": 3,
                "risk_alert_count": 1,
                "near_entry_count": 2,
                "holding_risk_count": 2,
                "holding_profit_protection_count": 1,
            },
            "top_alerts": [
                {
                    "id": 1,
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "alert_type": "风险回避",
                    "priority": "high",
                    "title": "中际旭创 当前应风险回避",
                    "body": "先回避高波动。",
                    "next_action": "先观察。",
                }
            ],
            "top_opportunities": [
                {
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "topic_name": "AI算力",
                    "action": "接近可参与窗口",
                    "candidate_state": "高优先级买点",
                    "tradeability_state": "可观察",
                    "priority_score": 88,
                }
            ],
            "top_holdings_to_handle": [
                {
                    "holding_id": 1,
                    "ticker": "SZSE:300308",
                    "asset_name": "中际旭创",
                    "action": "纪律止损",
                    "confidence": 70,
                    "summary": "优先收缩风险。",
                    "profit_protection_view": "先控制回撤。",
                }
            ],
            "top_holdings_stable": [
                {
                    "holding_id": 2,
                    "ticker": "SZSE:000001",
                    "asset_name": "平安银行",
                    "action": "继续持有",
                    "confidence": 58,
                    "summary": "逻辑未坏。",
                    "profit_protection_view": "继续跟踪利润变化。",
                }
            ],
            "today_action_queue": [
                {
                    "title": "先看风险回避提醒",
                    "reason": "风险优先。",
                    "target_path": "/home/alerts",
                },
                {
                    "title": "再看需要处理的持仓",
                    "reason": "已有持仓优先。",
                    "target_path": "/home",
                },
            ],
        }


class FakeSnapshotRepository:
    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []
        self.next_id = 1

    def list_snapshots(
        self,
        *,
        user_id: str,
        limit: int = 20,
        include_today: bool = True,
        today_date: str | None = None,
    ):
        items = [item for item in self.items if item["user_id"] == user_id]
        if not include_today and today_date:
            items = [item for item in items if item["snapshot_date"] != today_date]
        items = sorted(items, key=lambda item: item["snapshot_date"], reverse=True)
        return [FakeSnapshotRecord(item) for item in items[:limit]]

    def get_snapshot_by_date(self, *, user_id: str, snapshot_date: str):
        for item in self.items:
            if item["user_id"] == user_id and item["snapshot_date"] == snapshot_date:
                return FakeSnapshotRecord(item)
        return None

    def create_snapshot(self, payload: dict[str, Any]):
        item = {
            **payload,
            "id": self.next_id,
            "created_at": "2025-04-10T10:56:00Z",
            "updated_at": "2025-04-10T10:56:00Z",
        }
        self.next_id += 1
        self.items.append(item)
        return FakeSnapshotRecord(item)

    def update_snapshot(self, snapshot_id: int, payload: dict[str, Any]):
        for index, item in enumerate(self.items):
            if item["id"] == snapshot_id:
                updated = {
                    **item,
                    **payload,
                    "updated_at": "2025-04-10T10:57:00Z",
                }
                self.items[index] = updated
                return FakeSnapshotRecord(updated)
        return None


def test_ashare_daily_snapshot_service_refreshes_and_upserts_today_snapshot() -> None:
    workbench_service = FakeWorkbenchService()
    repository = FakeSnapshotRepository()
    service = AShareDailySnapshotService(
        workbench_service=cast(Any, workbench_service),
        snapshot_repository=cast(Any, repository),
    )

    first_result = service.refresh_today_snapshot(user_id="default_user")
    second_result = service.refresh_today_snapshot(user_id="default_user")

    assert first_result["created_or_updated"] == "created"
    assert second_result["created_or_updated"] == "updated"
    assert len(repository.items) == 1
    assert workbench_service.overview_calls == 2


def test_ashare_daily_snapshot_service_lists_and_reads_snapshot_detail() -> None:
    workbench_service = FakeWorkbenchService()
    repository = FakeSnapshotRepository()
    service = AShareDailySnapshotService(
        workbench_service=cast(Any, workbench_service),
        snapshot_repository=cast(Any, repository),
    )

    refresh_result = service.refresh_today_snapshot(user_id="default_user")
    snapshot_date = refresh_result["snapshot_date"]
    list_result = service.list_snapshots(user_id="default_user", limit=20, include_today=True)
    detail_result = service.get_snapshot_detail(
        user_id="default_user",
        snapshot_date=snapshot_date,
    )

    assert list_result["count"] == 1
    assert list_result["items"][0]["brief_action_queue"][0] == "先看风险回避提醒"
    assert detail_result is not None
    assert detail_result["market_digest"]["market_state"] == "震荡偏强"
    assert detail_result["top_opportunities"][0]["ticker"] == "SZSE:300308"
