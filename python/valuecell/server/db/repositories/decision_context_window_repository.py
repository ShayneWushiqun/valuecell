from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..connection import get_database_manager
from ..models.decision_context_window import DecisionContextWindow


class DecisionContextWindowRepository:
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session

    def _get_session(self) -> Session:
        if self.db_session:
            return self.db_session
        return get_database_manager().get_session()

    def list_windows(
        self,
        *,
        user_id: str,
        ticker: str | None = None,
        window_size: int | None = None,
        limit: int = 100,
    ) -> list[DecisionContextWindow]:
        session = self._get_session()
        try:
            query = session.query(DecisionContextWindow).filter(
                DecisionContextWindow.user_id == user_id,
            )
            if ticker:
                query = query.filter(DecisionContextWindow.ticker == ticker)
            if window_size:
                query = query.filter(DecisionContextWindow.window_size == window_size)
            items = (
                query.order_by(
                    desc(DecisionContextWindow.updated_at),
                    desc(DecisionContextWindow.window_size),
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

    def get_window_by_id(self, *, user_id: str, window_id: int) -> DecisionContextWindow | None:
        session = self._get_session()
        try:
            window = (
                session.query(DecisionContextWindow)
                .filter(
                    DecisionContextWindow.user_id == user_id,
                    DecisionContextWindow.id == window_id,
                )
                .first()
            )
            if window:
                session.expunge(window)
            return window
        finally:
            if not self.db_session:
                session.close()

    def get_window_by_dedupe_key(
        self,
        *,
        user_id: str,
        dedupe_key: str,
    ) -> DecisionContextWindow | None:
        session = self._get_session()
        try:
            window = (
                session.query(DecisionContextWindow)
                .filter(
                    DecisionContextWindow.user_id == user_id,
                    DecisionContextWindow.dedupe_key == dedupe_key,
                )
                .order_by(desc(DecisionContextWindow.updated_at))
                .first()
            )
            if window:
                session.expunge(window)
            return window
        finally:
            if not self.db_session:
                session.close()

    def create_window(self, payload: dict[str, Any]) -> DecisionContextWindow | None:
        session = self._get_session()
        try:
            window = DecisionContextWindow(**payload)
            session.add(window)
            session.commit()
            session.refresh(window)
            session.expunge(window)
            return window
        except Exception:
            session.rollback()
            return None
        finally:
            if not self.db_session:
                session.close()

    def update_window(self, window_id: int, payload: dict[str, Any]) -> DecisionContextWindow | None:
        session = self._get_session()
        try:
            window = (
                session.query(DecisionContextWindow)
                .filter(DecisionContextWindow.id == window_id)
                .first()
            )
            if not window:
                return None
            for key, value in payload.items():
                setattr(window, key, value)
            session.commit()
            session.refresh(window)
            session.expunge(window)
            return window
        except Exception:
            session.rollback()
            return None
        finally:
            if not self.db_session:
                session.close()
