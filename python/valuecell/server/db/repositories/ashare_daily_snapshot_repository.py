from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..connection import get_database_manager
from ..models.ashare_daily_snapshot import AShareDailySnapshot


class AShareDailySnapshotRepository:
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session

    def _get_session(self) -> Session:
        if self.db_session:
            return self.db_session
        return get_database_manager().get_session()

    def get_snapshot_by_date(
        self,
        *,
        user_id: str,
        snapshot_date: str,
    ) -> AShareDailySnapshot | None:
        session = self._get_session()
        try:
            snapshot = (
                session.query(AShareDailySnapshot)
                .filter(
                    AShareDailySnapshot.user_id == user_id,
                    AShareDailySnapshot.snapshot_date == snapshot_date,
                )
                .first()
            )
            if snapshot:
                session.expunge(snapshot)
            return snapshot
        finally:
            if not self.db_session:
                session.close()

    def create_snapshot(self, payload: dict[str, Any]) -> AShareDailySnapshot | None:
        session = self._get_session()
        try:
            snapshot = AShareDailySnapshot(**payload)
            session.add(snapshot)
            session.commit()
            session.refresh(snapshot)
            session.expunge(snapshot)
            return snapshot
        except Exception:
            session.rollback()
            return None
        finally:
            if not self.db_session:
                session.close()

    def update_snapshot(
        self,
        snapshot_id: int,
        payload: dict[str, Any],
    ) -> AShareDailySnapshot | None:
        session = self._get_session()
        try:
            snapshot = (
                session.query(AShareDailySnapshot)
                .filter(AShareDailySnapshot.id == snapshot_id)
                .first()
            )
            if not snapshot:
                return None
            for key, value in payload.items():
                setattr(snapshot, key, value)
            session.commit()
            session.refresh(snapshot)
            session.expunge(snapshot)
            return snapshot
        except Exception:
            session.rollback()
            return None
        finally:
            if not self.db_session:
                session.close()

    def list_snapshots(
        self,
        *,
        user_id: str,
        limit: int = 20,
        include_today: bool = True,
        today_date: str | None = None,
    ) -> list[AShareDailySnapshot]:
        session = self._get_session()
        try:
            query = session.query(AShareDailySnapshot).filter(
                AShareDailySnapshot.user_id == user_id
            )
            if not include_today and today_date:
                query = query.filter(AShareDailySnapshot.snapshot_date != today_date)
            items = (
                query.order_by(desc(AShareDailySnapshot.snapshot_date))
                .limit(limit)
                .all()
            )
            for item in items:
                session.expunge(item)
            return items
        finally:
            if not self.db_session:
                session.close()
