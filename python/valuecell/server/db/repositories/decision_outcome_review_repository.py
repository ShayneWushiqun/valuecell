from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..connection import get_database_manager
from ..models.decision_outcome_review import DecisionOutcomeReview


class DecisionOutcomeReviewRepository:
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session

    def _get_session(self) -> Session:
        if self.db_session:
            return self.db_session
        return get_database_manager().get_session()

    def list_reviews(
        self,
        *,
        user_id: str,
        record_id: int | None = None,
        outcome_status: str | None = None,
        action: str | None = None,
        review_horizon_days: int | None = None,
        limit: int = 50,
    ) -> list[DecisionOutcomeReview]:
        session = self._get_session()
        try:
            query = session.query(DecisionOutcomeReview).filter(
                DecisionOutcomeReview.user_id == user_id,
            )
            if record_id is not None:
                query = query.filter(DecisionOutcomeReview.record_id == record_id)
            if outcome_status:
                query = query.filter(DecisionOutcomeReview.outcome_status == outcome_status)
            if action:
                query = query.filter(DecisionOutcomeReview.action == action)
            if review_horizon_days is not None:
                query = query.filter(
                    DecisionOutcomeReview.review_horizon_days == review_horizon_days
                )
            items = (
                query.order_by(
                    desc(DecisionOutcomeReview.review_date),
                    desc(DecisionOutcomeReview.review_horizon_days),
                    desc(DecisionOutcomeReview.updated_at),
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

    def get_review_by_id(
        self,
        *,
        user_id: str,
        review_id: int,
    ) -> DecisionOutcomeReview | None:
        session = self._get_session()
        try:
            item = (
                session.query(DecisionOutcomeReview)
                .filter(
                    DecisionOutcomeReview.user_id == user_id,
                    DecisionOutcomeReview.id == review_id,
                )
                .first()
            )
            if item:
                session.expunge(item)
            return item
        finally:
            if not self.db_session:
                session.close()

    def get_review_by_dedupe_key(
        self,
        *,
        user_id: str,
        dedupe_key: str,
    ) -> DecisionOutcomeReview | None:
        session = self._get_session()
        try:
            item = (
                session.query(DecisionOutcomeReview)
                .filter(
                    DecisionOutcomeReview.user_id == user_id,
                    DecisionOutcomeReview.dedupe_key == dedupe_key,
                )
                .order_by(desc(DecisionOutcomeReview.updated_at))
                .first()
            )
            if item:
                session.expunge(item)
            return item
        finally:
            if not self.db_session:
                session.close()

    def create_review(self, payload: dict[str, Any]) -> DecisionOutcomeReview | None:
        session = self._get_session()
        try:
            item = DecisionOutcomeReview(**payload)
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

    def update_review(self, review_id: int, payload: dict[str, Any]) -> DecisionOutcomeReview | None:
        session = self._get_session()
        try:
            item = (
                session.query(DecisionOutcomeReview)
                .filter(DecisionOutcomeReview.id == review_id)
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
