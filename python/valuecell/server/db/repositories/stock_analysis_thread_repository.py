from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..connection import get_database_manager
from ..models.stock_analysis_thread import StockAnalysisThread


class StockAnalysisThreadRepository:
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session

    def _get_session(self) -> Session:
        if self.db_session:
            return self.db_session
        return get_database_manager().get_session()

    def list_threads(
        self,
        *,
        user_id: str,
        include_archived: bool = False,
        limit: int = 100,
    ) -> list[StockAnalysisThread]:
        session = self._get_session()
        try:
            query = session.query(StockAnalysisThread).filter(
                StockAnalysisThread.user_id == user_id
            )
            if not include_archived:
                query = query.filter(StockAnalysisThread.archived_at.is_(None))
            items = (
                query.order_by(desc(StockAnalysisThread.updated_at))
                .limit(limit)
                .all()
            )
            for item in items:
                session.expunge(item)
            return items
        finally:
            if not self.db_session:
                session.close()

    def get_thread_by_id(
        self,
        *,
        user_id: str,
        thread_id: int,
        include_archived: bool = False,
    ) -> StockAnalysisThread | None:
        session = self._get_session()
        try:
            query = session.query(StockAnalysisThread).filter(
                StockAnalysisThread.user_id == user_id,
                StockAnalysisThread.id == thread_id,
            )
            if not include_archived:
                query = query.filter(StockAnalysisThread.archived_at.is_(None))
            item = query.first()
            if item:
                session.expunge(item)
            return item
        finally:
            if not self.db_session:
                session.close()

    def create_thread(self, payload: dict[str, Any]) -> StockAnalysisThread | None:
        session = self._get_session()
        try:
            item = StockAnalysisThread(**payload)
            session.add(item)
            session.commit()
            session.refresh(item)
            session.expunge(item)
            return item
        except Exception:
            session.rollback()
            return None
        finally:
            if not self.db_session:
                session.close()

    def update_thread(
        self,
        *,
        user_id: str,
        thread_id: int,
        payload: dict[str, Any],
    ) -> StockAnalysisThread | None:
        session = self._get_session()
        try:
            item = (
                session.query(StockAnalysisThread)
                .filter(
                    StockAnalysisThread.user_id == user_id,
                    StockAnalysisThread.id == thread_id,
                )
                .first()
            )
            if not item:
                return None
            for key, value in payload.items():
                setattr(item, key, value)
            session.commit()
            session.refresh(item)
            session.expunge(item)
            return item
        except Exception:
            session.rollback()
            return None
        finally:
            if not self.db_session:
                session.close()
