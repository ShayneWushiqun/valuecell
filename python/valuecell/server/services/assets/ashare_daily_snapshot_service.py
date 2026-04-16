from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from ...db.repositories.ashare_daily_snapshot_repository import (
    AShareDailySnapshotRepository,
)
from .ashare_daily_workbench_service import AShareDailyWorkbenchService


class AShareDailySnapshotService:
    def __init__(
        self,
        workbench_service: Optional[AShareDailyWorkbenchService] = None,
        snapshot_repository: Optional[AShareDailySnapshotRepository] = None,
    ) -> None:
        self.workbench_service = workbench_service or AShareDailyWorkbenchService()
        self.snapshot_repository = snapshot_repository or AShareDailySnapshotRepository()

    def list_snapshots(
        self,
        *,
        user_id: str,
        limit: int = 20,
        include_today: bool = True,
    ) -> dict[str, Any]:
        today_date = self._today_snapshot_date()
        snapshots = self.snapshot_repository.list_snapshots(
            user_id=user_id,
            limit=limit,
            include_today=include_today,
            today_date=today_date,
        )
        items = [
            self._build_snapshot_list_item(
                self._normalize_snapshot_data(snapshot.to_dict())
            )
            for snapshot in snapshots
        ]
        return {
            "generated_at": datetime.now().astimezone().isoformat(),
            "count": len(items),
            "items": items,
        }

    def get_snapshot_detail(
        self,
        *,
        user_id: str,
        snapshot_date: str,
    ) -> dict[str, Any] | None:
        snapshot = self.snapshot_repository.get_snapshot_by_date(
            user_id=user_id,
            snapshot_date=snapshot_date,
        )
        if snapshot is None:
            return None
        snapshot_data = self._normalize_snapshot_data(snapshot.to_dict())
        return {
            "snapshot_date": snapshot_data["snapshot_date"],
            "generated_at": snapshot_data["generated_at"],
            "market_digest": snapshot_data["market_digest"],
            "attention_digest": snapshot_data["attention_digest"],
            "top_alerts": snapshot_data["top_alerts"],
            "top_opportunities": snapshot_data["top_opportunities"],
            "top_holdings_to_handle": snapshot_data["top_holdings_to_handle"],
            "top_holdings_stable": snapshot_data["top_holdings_stable"],
            "today_action_queue": snapshot_data["today_action_queue"],
            "metadata": snapshot_data["metadata"],
        }

    def refresh_today_snapshot(self, *, user_id: str) -> dict[str, Any]:
        workbench_overview = self.workbench_service.get_overview(user_id=user_id)
        snapshot_date = self._today_snapshot_date()
        payload = {
            "user_id": user_id,
            "snapshot_date": snapshot_date,
            "generated_at": datetime.fromisoformat(
                str(workbench_overview["generated_at"]).replace("Z", "+00:00")
            ),
            "market_digest_json": workbench_overview.get("market_digest") or {},
            "attention_digest_json": workbench_overview.get("attention_digest") or {},
            "top_alerts_json": list(workbench_overview.get("top_alerts") or [])[:5],
            "top_opportunities_json": list(workbench_overview.get("top_opportunities") or [])[:5],
            "top_holdings_to_handle_json": list(
                workbench_overview.get("top_holdings_to_handle") or []
            )[:5],
            "top_holdings_stable_json": list(
                workbench_overview.get("top_holdings_stable") or []
            )[:3],
            "today_action_queue_json": list(workbench_overview.get("today_action_queue") or []),
            "metadata_json": {
                "available": bool(workbench_overview.get("available")),
                "empty_message": workbench_overview.get("empty_message"),
                "top_opportunity_count": len(workbench_overview.get("top_opportunities") or []),
                "top_holding_action_count": len(
                    workbench_overview.get("top_holdings_to_handle") or []
                ),
            },
        }
        existing = self.snapshot_repository.get_snapshot_by_date(
            user_id=user_id,
            snapshot_date=snapshot_date,
        )
        created_or_updated = "created"
        if existing is None:
            saved = self.snapshot_repository.create_snapshot(payload)
        else:
            created_or_updated = "updated"
            saved = self.snapshot_repository.update_snapshot(int(existing.id), payload)

        snapshot_detail = (
            self._normalize_snapshot_data(saved.to_dict())
            if saved
            else self.get_snapshot_detail(
                user_id=user_id,
                snapshot_date=snapshot_date,
            )
        )
        list_item = self._build_snapshot_list_item(snapshot_detail or {})
        return {
            "generated_at": datetime.now().astimezone().isoformat(),
            "snapshot_date": snapshot_date,
            "created_or_updated": created_or_updated,
            "summary": self._build_refresh_summary(list_item),
            "snapshot": {
                "snapshot_date": (snapshot_detail or {}).get("snapshot_date", snapshot_date),
                "generated_at": (snapshot_detail or {}).get("generated_at"),
                "market_digest": (snapshot_detail or {}).get("market_digest", {}),
                "attention_digest": (snapshot_detail or {}).get("attention_digest", {}),
                "top_alerts": (snapshot_detail or {}).get("top_alerts", []),
                "top_opportunities": (snapshot_detail or {}).get("top_opportunities", []),
                "top_holdings_to_handle": (snapshot_detail or {}).get("top_holdings_to_handle", []),
                "top_holdings_stable": (snapshot_detail or {}).get("top_holdings_stable", []),
                "today_action_queue": (snapshot_detail or {}).get("today_action_queue", []),
                "metadata": (snapshot_detail or {}).get("metadata", {}),
            },
        }

    @staticmethod
    def _build_snapshot_list_item(snapshot: dict[str, Any]) -> dict[str, Any]:
        action_queue = list(snapshot.get("today_action_queue") or [])
        return {
            "snapshot_date": snapshot.get("snapshot_date"),
            "generated_at": snapshot.get("generated_at"),
            "market_digest": snapshot.get("market_digest") or {},
            "attention_digest": snapshot.get("attention_digest") or {},
            "brief_action_queue": [
                str(item.get("title") or "")
                for item in action_queue[:2]
                if str(item.get("title") or "")
            ],
            "top_opportunity_count": int(
                (snapshot.get("metadata") or {}).get("top_opportunity_count")
                or len(snapshot.get("top_opportunities") or [])
            ),
            "top_holding_action_count": int(
                (snapshot.get("metadata") or {}).get("top_holding_action_count")
                or len(snapshot.get("top_holdings_to_handle") or [])
            ),
        }

    @staticmethod
    def _build_refresh_summary(snapshot_item: dict[str, Any]) -> str:
        attention_digest = snapshot_item.get("attention_digest") or {}
        market_digest = snapshot_item.get("market_digest") or {}
        return (
            f"已记录 {snapshot_item.get('snapshot_date')} 快照："
            f"{market_digest.get('market_state') or '市场待观察'}，"
            f"风险回避 {attention_digest.get('risk_alert_count') or 0} 条，"
            f"接近可参与窗口 {attention_digest.get('near_entry_count') or 0} 条，"
            f"需要处理的持仓 {attention_digest.get('holding_risk_count') or 0} 个。"
        )

    @staticmethod
    def _today_snapshot_date() -> str:
        return datetime.now().astimezone().date().isoformat()

    @staticmethod
    def _normalize_snapshot_data(snapshot: dict[str, Any]) -> dict[str, Any]:
        return {
            "snapshot_date": snapshot.get("snapshot_date"),
            "generated_at": snapshot.get("generated_at"),
            "market_digest": snapshot.get("market_digest")
            or snapshot.get("market_digest_json")
            or {},
            "attention_digest": snapshot.get("attention_digest")
            or snapshot.get("attention_digest_json")
            or {},
            "top_alerts": snapshot.get("top_alerts") or snapshot.get("top_alerts_json") or [],
            "top_opportunities": snapshot.get("top_opportunities")
            or snapshot.get("top_opportunities_json")
            or [],
            "top_holdings_to_handle": snapshot.get("top_holdings_to_handle")
            or snapshot.get("top_holdings_to_handle_json")
            or [],
            "top_holdings_stable": snapshot.get("top_holdings_stable")
            or snapshot.get("top_holdings_stable_json")
            or [],
            "today_action_queue": snapshot.get("today_action_queue")
            or snapshot.get("today_action_queue_json")
            or [],
            "metadata": snapshot.get("metadata") or snapshot.get("metadata_json") or {},
        }


_ashare_daily_snapshot_service: Optional[AShareDailySnapshotService] = None


def get_ashare_daily_snapshot_service() -> AShareDailySnapshotService:
    global _ashare_daily_snapshot_service
    if _ashare_daily_snapshot_service is None:
        _ashare_daily_snapshot_service = AShareDailySnapshotService()
    return _ashare_daily_snapshot_service


def reset_ashare_daily_snapshot_service() -> None:
    global _ashare_daily_snapshot_service
    _ashare_daily_snapshot_service = None
