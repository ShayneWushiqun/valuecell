from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..connection import get_database_manager
from ..models.stock_analysis_research_feedback import StockAnalysisResearchFeedback


class StockAnalysisResearchFeedbackRepository:
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session

    def _get_session(self) -> Session:
        if self.db_session:
            return self.db_session
        return get_database_manager().get_session()

    def list_feedbacks(
        self,
        *,
        user_id: str,
        thread_id: int,
        limit: int = 200,
    ) -> list[StockAnalysisResearchFeedback]:
        session = self._get_session()
        try:
            items = (
                session.query(StockAnalysisResearchFeedback)
                .filter(
                    StockAnalysisResearchFeedback.user_id == user_id,
                    StockAnalysisResearchFeedback.thread_id == thread_id,
                )
                .order_by(
                    desc(StockAnalysisResearchFeedback.created_at),
                    desc(StockAnalysisResearchFeedback.id),
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

    def get_feedback_by_id(
        self,
        *,
        user_id: str,
        thread_id: int,
        feedback_id: int,
    ) -> StockAnalysisResearchFeedback | None:
        session = self._get_session()
        try:
            item = (
                session.query(StockAnalysisResearchFeedback)
                .filter(
                    StockAnalysisResearchFeedback.user_id == user_id,
                    StockAnalysisResearchFeedback.thread_id == thread_id,
                    StockAnalysisResearchFeedback.id == feedback_id,
                )
                .first()
            )
            if item is not None:
                session.expunge(item)
            return item
        finally:
            if not self.db_session:
                session.close()

    def create_feedback(
        self,
        payload: dict[str, Any],
    ) -> StockAnalysisResearchFeedback | None:
        session = self._get_session()
        try:
            item = StockAnalysisResearchFeedback(**payload)
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
