from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..connection import get_database_manager
from ..models.decision_record import DecisionRecord


class DecisionRecordRepository:
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session

    def _get_session(self) -> Session:
        if self.db_session:
            return self.db_session
        return get_database_manager().get_session()

    def get_record_by_id(self, *, user_id: str, record_id: int) -> DecisionRecord | None:
        session = self._get_session()
        try:
            record = (
                session.query(DecisionRecord)
                .filter(DecisionRecord.user_id == user_id, DecisionRecord.id == record_id)
                .first()
            )
            if record:
                session.expunge(record)
            return record
        finally:
            if not self.db_session:
                session.close()

    def get_record_by_dedupe_key(
        self,
        *,
        user_id: str,
        dedupe_key: str,
    ) -> DecisionRecord | None:
        session = self._get_session()
        try:
            record = (
                session.query(DecisionRecord)
                .filter(
                    DecisionRecord.user_id == user_id,
                    DecisionRecord.dedupe_key == dedupe_key,
                )
                .order_by(desc(DecisionRecord.updated_at))
                .first()
            )
            if record:
                session.expunge(record)
            return record
        finally:
            if not self.db_session:
                session.close()

    def list_records(
        self,
        *,
        user_id: str,
        limit: int = 20,
        action: str | None = None,
    ) -> list[DecisionRecord]:
        session = self._get_session()
        try:
            query = session.query(DecisionRecord).filter(DecisionRecord.user_id == user_id)
            if action:
                query = query.filter(DecisionRecord.action == action)
            items = (
                query.order_by(
                    desc(DecisionRecord.record_date),
                    desc(DecisionRecord.updated_at),
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

    def create_record(self, payload: dict[str, Any]) -> DecisionRecord | None:
        session = self._get_session()
        try:
            record = DecisionRecord(**payload)
            session.add(record)
            session.commit()
            session.refresh(record)
            session.expunge(record)
            return record
        except Exception:
            session.rollback()
            return None
        finally:
            if not self.db_session:
                session.close()

    def update_record(self, record_id: int, payload: dict[str, Any]) -> DecisionRecord | None:
        session = self._get_session()
        try:
            record = session.query(DecisionRecord).filter(DecisionRecord.id == record_id).first()
            if not record:
                return None
            for key, value in payload.items():
                setattr(record, key, value)
            session.commit()
            session.refresh(record)
            session.expunge(record)
            return record
        except Exception:
            session.rollback()
            return None
        finally:
            if not self.db_session:
                session.close()
