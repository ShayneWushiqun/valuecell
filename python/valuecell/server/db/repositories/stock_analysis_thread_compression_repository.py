from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from ..connection import get_database_manager
from ..models.stock_analysis_thread_compression import StockAnalysisThreadCompression


class StockAnalysisThreadCompressionRepository:
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session

    def _get_session(self) -> Session:
        if self.db_session:
            return self.db_session
        return get_database_manager().get_session()

    def list_compressions(
        self,
        *,
        user_id: str,
        thread_id: int,
        limit: int = 100,
    ) -> list[StockAnalysisThreadCompression]:
        session = self._get_session()
        try:
            items = (
                session.query(StockAnalysisThreadCompression)
                .filter(
                    StockAnalysisThreadCompression.user_id == user_id,
                    StockAnalysisThreadCompression.thread_id == thread_id,
                )
                .order_by(
                    desc(StockAnalysisThreadCompression.created_at),
                    desc(StockAnalysisThreadCompression.id),
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

    def get_compression_by_id(
        self,
        *,
        user_id: str,
        thread_id: int,
        compression_id: int,
    ) -> StockAnalysisThreadCompression | None:
        session = self._get_session()
        try:
            item = (
                session.query(StockAnalysisThreadCompression)
                .filter(
                    StockAnalysisThreadCompression.user_id == user_id,
                    StockAnalysisThreadCompression.thread_id == thread_id,
                    StockAnalysisThreadCompression.id == compression_id,
                )
                .first()
            )
            if item is not None:
                session.expunge(item)
            return item
        finally:
            if not self.db_session:
                session.close()

    def get_active_compression(
        self,
        *,
        user_id: str,
        thread_id: int,
    ) -> StockAnalysisThreadCompression | None:
        session = self._get_session()
        try:
            item = (
                session.query(StockAnalysisThreadCompression)
                .filter(
                    StockAnalysisThreadCompression.user_id == user_id,
                    StockAnalysisThreadCompression.thread_id == thread_id,
                    StockAnalysisThreadCompression.is_active.is_(True),
                )
                .order_by(
                    desc(StockAnalysisThreadCompression.updated_at),
                    desc(StockAnalysisThreadCompression.id),
                )
                .first()
            )
            if item is not None:
                session.expunge(item)
            return item
        finally:
            if not self.db_session:
                session.close()

    def create_compression(
        self,
        payload: dict[str, Any],
    ) -> StockAnalysisThreadCompression | None:
        session = self._get_session()
        try:
            item = StockAnalysisThreadCompression(**payload)
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

    def update_compression(
        self,
        *,
        user_id: str,
        thread_id: int,
        compression_id: int,
        payload: dict[str, Any],
    ) -> StockAnalysisThreadCompression | None:
        session = self._get_session()
        try:
            item = (
                session.query(StockAnalysisThreadCompression)
                .filter(
                    StockAnalysisThreadCompression.user_id == user_id,
                    StockAnalysisThreadCompression.thread_id == thread_id,
                    StockAnalysisThreadCompression.id == compression_id,
                )
                .first()
            )
            if item is None:
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

    def deactivate_thread_compressions(
        self,
        *,
        user_id: str,
        thread_id: int,
        exclude_compression_id: int | None = None,
    ) -> int:
        session = self._get_session()
        try:
            query = session.query(StockAnalysisThreadCompression).filter(
                StockAnalysisThreadCompression.user_id == user_id,
                StockAnalysisThreadCompression.thread_id == thread_id,
                StockAnalysisThreadCompression.is_active.is_(True),
            )
            if exclude_compression_id is not None:
                query = query.filter(
                    StockAnalysisThreadCompression.id != exclude_compression_id
                )
            items = query.order_by(asc(StockAnalysisThreadCompression.id)).all()
            for item in items:
                item.is_active = False
            session.commit()
            return len(items)
        except Exception:
            session.rollback()
            return 0
        finally:
            if not self.db_session:
                session.close()
