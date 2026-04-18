from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from ..connection import get_database_manager
from ..models.stock_analysis_thread_memory import StockAnalysisThreadMemory


class StockAnalysisThreadMemoryRepository:
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session

    def _get_session(self) -> Session:
        if self.db_session:
            return self.db_session
        return get_database_manager().get_session()

    def list_memories(
        self,
        *,
        user_id: str,
        thread_id: int,
        limit: int = 100,
    ) -> list[StockAnalysisThreadMemory]:
        session = self._get_session()
        try:
            items = (
                session.query(StockAnalysisThreadMemory)
                .filter(
                    StockAnalysisThreadMemory.user_id == user_id,
                    StockAnalysisThreadMemory.thread_id == thread_id,
                )
                .order_by(
                    desc(StockAnalysisThreadMemory.created_at),
                    desc(StockAnalysisThreadMemory.id),
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

    def get_memory_by_id(
        self,
        *,
        user_id: str,
        thread_id: int,
        memory_id: int,
    ) -> StockAnalysisThreadMemory | None:
        session = self._get_session()
        try:
            item = (
                session.query(StockAnalysisThreadMemory)
                .filter(
                    StockAnalysisThreadMemory.user_id == user_id,
                    StockAnalysisThreadMemory.thread_id == thread_id,
                    StockAnalysisThreadMemory.id == memory_id,
                )
                .first()
            )
            if item is not None:
                session.expunge(item)
            return item
        finally:
            if not self.db_session:
                session.close()

    def get_active_memory(
        self,
        *,
        user_id: str,
        thread_id: int,
    ) -> StockAnalysisThreadMemory | None:
        session = self._get_session()
        try:
            item = (
                session.query(StockAnalysisThreadMemory)
                .filter(
                    StockAnalysisThreadMemory.user_id == user_id,
                    StockAnalysisThreadMemory.thread_id == thread_id,
                    StockAnalysisThreadMemory.is_active.is_(True),
                )
                .order_by(
                    desc(StockAnalysisThreadMemory.updated_at),
                    desc(StockAnalysisThreadMemory.id),
                )
                .first()
            )
            if item is not None:
                session.expunge(item)
            return item
        finally:
            if not self.db_session:
                session.close()

    def create_memory(self, payload: dict[str, Any]) -> StockAnalysisThreadMemory | None:
        session = self._get_session()
        try:
            item = StockAnalysisThreadMemory(**payload)
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

    def update_memory(
        self,
        *,
        user_id: str,
        thread_id: int,
        memory_id: int,
        payload: dict[str, Any],
    ) -> StockAnalysisThreadMemory | None:
        session = self._get_session()
        try:
            item = (
                session.query(StockAnalysisThreadMemory)
                .filter(
                    StockAnalysisThreadMemory.user_id == user_id,
                    StockAnalysisThreadMemory.thread_id == thread_id,
                    StockAnalysisThreadMemory.id == memory_id,
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

    def deactivate_thread_memories(
        self,
        *,
        user_id: str,
        thread_id: int,
        exclude_memory_id: int | None = None,
    ) -> int:
        session = self._get_session()
        try:
            query = session.query(StockAnalysisThreadMemory).filter(
                StockAnalysisThreadMemory.user_id == user_id,
                StockAnalysisThreadMemory.thread_id == thread_id,
                StockAnalysisThreadMemory.is_active.is_(True),
            )
            if exclude_memory_id is not None:
                query = query.filter(StockAnalysisThreadMemory.id != exclude_memory_id)
            items = query.order_by(asc(StockAnalysisThreadMemory.id)).all()
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
