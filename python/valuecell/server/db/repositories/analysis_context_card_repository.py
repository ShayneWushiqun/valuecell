from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..connection import get_database_manager
from ..models.analysis_context_card import AnalysisContextCard


class AnalysisContextCardRepository:
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session

    def _get_session(self) -> Session:
        if self.db_session:
            return self.db_session
        return get_database_manager().get_session()

    def list_context_cards(
        self,
        *,
        user_id: str,
        thread_id: int,
    ) -> list[AnalysisContextCard]:
        session = self._get_session()
        try:
            items = (
                session.query(AnalysisContextCard)
                .filter(
                    AnalysisContextCard.user_id == user_id,
                    AnalysisContextCard.thread_id == thread_id,
                )
                .order_by(
                    desc(AnalysisContextCard.is_pinned),
                    desc(AnalysisContextCard.updated_at),
                )
                .all()
            )
            for item in items:
                session.expunge(item)
            return items
        finally:
            if not self.db_session:
                session.close()

    def get_context_card_by_id(
        self,
        *,
        user_id: str,
        thread_id: int,
        context_id: int,
    ) -> AnalysisContextCard | None:
        session = self._get_session()
        try:
            item = (
                session.query(AnalysisContextCard)
                .filter(
                    AnalysisContextCard.user_id == user_id,
                    AnalysisContextCard.thread_id == thread_id,
                    AnalysisContextCard.id == context_id,
                )
                .first()
            )
            if item:
                session.expunge(item)
            return item
        finally:
            if not self.db_session:
                session.close()

    def create_context_card(self, payload: dict[str, Any]) -> AnalysisContextCard | None:
        session = self._get_session()
        try:
            item = AnalysisContextCard(**payload)
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

    def update_context_card(
        self,
        *,
        user_id: str,
        thread_id: int,
        context_id: int,
        payload: dict[str, Any],
    ) -> AnalysisContextCard | None:
        session = self._get_session()
        try:
            item = (
                session.query(AnalysisContextCard)
                .filter(
                    AnalysisContextCard.user_id == user_id,
                    AnalysisContextCard.thread_id == thread_id,
                    AnalysisContextCard.id == context_id,
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

    def delete_context_card(
        self,
        *,
        user_id: str,
        thread_id: int,
        context_id: int,
    ) -> bool:
        session = self._get_session()
        try:
            deleted = (
                session.query(AnalysisContextCard)
                .filter(
                    AnalysisContextCard.user_id == user_id,
                    AnalysisContextCard.thread_id == thread_id,
                    AnalysisContextCard.id == context_id,
                )
                .delete()
            )
            session.commit()
            return deleted > 0
        except Exception:
            session.rollback()
            return False
        finally:
            if not self.db_session:
                session.close()

    def delete_context_cards_by_filter(
        self,
        *,
        user_id: str,
        thread_id: int,
        context_type: str | None = None,
        source_module: str | None = None,
        source_ref: str | None = None,
    ) -> int:
        session = self._get_session()
        try:
            query = session.query(AnalysisContextCard).filter(
                AnalysisContextCard.user_id == user_id,
                AnalysisContextCard.thread_id == thread_id,
            )
            if context_type:
                query = query.filter(AnalysisContextCard.context_type == context_type)
            if source_module:
                query = query.filter(AnalysisContextCard.source_module == source_module)
            if source_ref:
                query = query.filter(AnalysisContextCard.source_ref == source_ref)
            deleted = query.delete()
            session.commit()
            return deleted
        except Exception:
            session.rollback()
            return 0
        finally:
            if not self.db_session:
                session.close()
