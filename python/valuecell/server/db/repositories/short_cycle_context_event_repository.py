from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..connection import get_database_manager
from ..models.short_cycle_context_event import ShortCycleContextEvent


class ShortCycleContextEventRepository:
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session

    def _get_session(self) -> Session:
        if self.db_session:
            return self.db_session
        return get_database_manager().get_session()

    def list_events(
        self,
        *,
        user_id: str,
        ticker: str | None = None,
        limit: int = 200,
    ) -> list[ShortCycleContextEvent]:
        session = self._get_session()
        try:
            query = session.query(ShortCycleContextEvent).filter(
                ShortCycleContextEvent.user_id == user_id,
            )
            if ticker:
                query = query.filter(ShortCycleContextEvent.ticker == ticker)
            items = (
                query.order_by(
                    desc(ShortCycleContextEvent.record_date),
                    desc(ShortCycleContextEvent.importance_score),
                    desc(ShortCycleContextEvent.updated_at),
                )
                .limit(limit)
                .all()
            )
            for item in items:
                session.expunge(item)
            return items
        finally:
            if not self.db_session:
                session.close()

    def get_event_by_id(self, *, user_id: str, event_id: int) -> ShortCycleContextEvent | None:
        session = self._get_session()
        try:
            event = (
                session.query(ShortCycleContextEvent)
                .filter(
                    ShortCycleContextEvent.user_id == user_id,
                    ShortCycleContextEvent.id == event_id,
                )
                .first()
            )
            if event:
                session.expunge(event)
            return event
        finally:
            if not self.db_session:
                session.close()

    def get_event_by_dedupe_key(
        self,
        *,
        user_id: str,
        dedupe_key: str,
    ) -> ShortCycleContextEvent | None:
        session = self._get_session()
        try:
            event = (
                session.query(ShortCycleContextEvent)
                .filter(
                    ShortCycleContextEvent.user_id == user_id,
                    ShortCycleContextEvent.dedupe_key == dedupe_key,
                )
                .order_by(desc(ShortCycleContextEvent.updated_at))
                .first()
            )
            if event:
                session.expunge(event)
            return event
        finally:
            if not self.db_session:
                session.close()

    def create_event(self, payload: dict[str, Any]) -> ShortCycleContextEvent | None:
        session = self._get_session()
        try:
            event = ShortCycleContextEvent(**payload)
            session.add(event)
            session.commit()
            session.refresh(event)
            session.expunge(event)
            return event
        except Exception:
            session.rollback()
            return None
        finally:
            if not self.db_session:
                session.close()

    def update_event(self, event_id: int, payload: dict[str, Any]) -> ShortCycleContextEvent | None:
        session = self._get_session()
        try:
            event = (
                session.query(ShortCycleContextEvent)
                .filter(ShortCycleContextEvent.id == event_id)
                .first()
            )
            if not event:
                return None
            for key, value in payload.items():
                setattr(event, key, value)
            session.commit()
            session.refresh(event)
            session.expunge(event)
            return event
        except Exception:
            session.rollback()
            return None
        finally:
            if not self.db_session:
                session.close()
