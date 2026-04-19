from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..connection import get_database_manager
from ..models.stock_analysis_research_task import StockAnalysisResearchTask


class StockAnalysisResearchTaskRepository:
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session

    def _get_session(self) -> Session:
        if self.db_session:
            return self.db_session
        return get_database_manager().get_session()

    def list_tasks(
        self,
        *,
        user_id: str,
        thread_id: int,
        status: str | None = None,
        limit: int = 200,
    ) -> list[StockAnalysisResearchTask]:
        session = self._get_session()
        try:
            query = session.query(StockAnalysisResearchTask).filter(
                StockAnalysisResearchTask.user_id == user_id,
                StockAnalysisResearchTask.thread_id == thread_id,
            )
            if status:
                query = query.filter(StockAnalysisResearchTask.status == status)
            items = (
                query.order_by(
                    desc(StockAnalysisResearchTask.updated_at),
                    desc(StockAnalysisResearchTask.id),
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

    def get_task_by_id(
        self,
        *,
        user_id: str,
        thread_id: int,
        task_id: int,
    ) -> StockAnalysisResearchTask | None:
        session = self._get_session()
        try:
            item = (
                session.query(StockAnalysisResearchTask)
                .filter(
                    StockAnalysisResearchTask.user_id == user_id,
                    StockAnalysisResearchTask.thread_id == thread_id,
                    StockAnalysisResearchTask.id == task_id,
                )
                .first()
            )
            if item is not None:
                session.expunge(item)
            return item
        finally:
            if not self.db_session:
                session.close()

    def create_task(self, payload: dict[str, Any]) -> StockAnalysisResearchTask | None:
        session = self._get_session()
        try:
            item = StockAnalysisResearchTask(**payload)
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

    def update_task(
        self,
        *,
        user_id: str,
        thread_id: int,
        task_id: int,
        payload: dict[str, Any],
    ) -> StockAnalysisResearchTask | None:
        session = self._get_session()
        try:
            item = (
                session.query(StockAnalysisResearchTask)
                .filter(
                    StockAnalysisResearchTask.user_id == user_id,
                    StockAnalysisResearchTask.thread_id == thread_id,
                    StockAnalysisResearchTask.id == task_id,
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
