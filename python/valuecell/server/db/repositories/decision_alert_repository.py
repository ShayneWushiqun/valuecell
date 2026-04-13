from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..connection import get_database_manager
from ..models.decision_alert import DecisionAlert


class DecisionAlertRepository:
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session

    def _get_session(self) -> Session:
        if self.db_session:
            return self.db_session
        return get_database_manager().get_session()

    def get_active_alert_by_dedupe_key(
        self,
        *,
        user_id: str,
        dedupe_key: str,
    ) -> DecisionAlert | None:
        session = self._get_session()
        try:
            alert = (
                session.query(DecisionAlert)
                .filter(
                    DecisionAlert.user_id == user_id,
                    DecisionAlert.dedupe_key == dedupe_key,
                    DecisionAlert.dismissed_at.is_(None),
                )
                .order_by(desc(DecisionAlert.updated_at))
                .first()
            )
            if alert:
                session.expunge(alert)
            return alert
        finally:
            if not self.db_session:
                session.close()

    def create_alert(self, payload: dict[str, Any]) -> DecisionAlert | None:
        session = self._get_session()
        try:
            alert = DecisionAlert(**payload)
            session.add(alert)
            session.commit()
            session.refresh(alert)
            session.expunge(alert)
            return alert
        except Exception:
            session.rollback()
            return None
        finally:
            if not self.db_session:
                session.close()

    def update_alert(self, alert_id: int, payload: dict[str, Any]) -> DecisionAlert | None:
        session = self._get_session()
        try:
            alert = session.query(DecisionAlert).filter(DecisionAlert.id == alert_id).first()
            if not alert:
                return None
            for key, value in payload.items():
                setattr(alert, key, value)
            session.commit()
            session.refresh(alert)
            session.expunge(alert)
            return alert
        except Exception:
            session.rollback()
            return None
        finally:
            if not self.db_session:
                session.close()

    def list_alerts(
        self,
        *,
        user_id: str,
        status: str = "all",
        alert_type: str | None = None,
        limit: int = 50,
    ) -> list[DecisionAlert]:
        session = self._get_session()
        try:
            query = session.query(DecisionAlert).filter(DecisionAlert.user_id == user_id)
            if status == "dismissed":
                query = query.filter(DecisionAlert.dismissed_at.is_not(None))
            elif status == "active":
                query = query.filter(DecisionAlert.dismissed_at.is_(None))
            elif status == "all":
                pass
            else:
                query = query.filter(DecisionAlert.dismissed_at.is_(None))
                if status == "unread":
                    query = query.filter(DecisionAlert.read_at.is_(None))
                elif status == "read":
                    query = query.filter(DecisionAlert.read_at.is_not(None))
            if alert_type:
                query = query.filter(DecisionAlert.alert_type == alert_type)
            alerts = query.order_by(desc(DecisionAlert.updated_at)).limit(limit).all()
            for alert in alerts:
                session.expunge(alert)
            return alerts
        finally:
            if not self.db_session:
                session.close()

    def count_alerts(
        self,
        *,
        user_id: str,
        status: str = "all",
        alert_type: str | None = None,
    ) -> int:
        session = self._get_session()
        try:
            query = session.query(DecisionAlert).filter(DecisionAlert.user_id == user_id)
            if status == "dismissed":
                query = query.filter(DecisionAlert.dismissed_at.is_not(None))
            elif status == "active":
                query = query.filter(DecisionAlert.dismissed_at.is_(None))
            elif status == "all":
                pass
            else:
                query = query.filter(DecisionAlert.dismissed_at.is_(None))
                if status == "unread":
                    query = query.filter(DecisionAlert.read_at.is_(None))
                elif status == "read":
                    query = query.filter(DecisionAlert.read_at.is_not(None))
            if alert_type:
                query = query.filter(DecisionAlert.alert_type == alert_type)
            return int(query.count())
        finally:
            if not self.db_session:
                session.close()

    def mark_alert_read(self, *, alert_id: int, user_id: str) -> DecisionAlert | None:
        return self._update_read_state(
            alert_id=alert_id,
            user_id=user_id,
            read_at=datetime.now(UTC),
        )

    def mark_all_read(self, *, user_id: str) -> int:
        session = self._get_session()
        try:
            updated_count = (
                session.query(DecisionAlert)
                .filter(
                    DecisionAlert.user_id == user_id,
                    DecisionAlert.dismissed_at.is_(None),
                    DecisionAlert.read_at.is_(None),
                )
                .update({"read_at": datetime.now(UTC)}, synchronize_session=False)
            )
            session.commit()
            return int(updated_count or 0)
        except Exception:
            session.rollback()
            return 0
        finally:
            if not self.db_session:
                session.close()

    def dismiss_alert(self, *, alert_id: int, user_id: str) -> DecisionAlert | None:
        session = self._get_session()
        try:
            alert = (
                session.query(DecisionAlert)
                .filter(DecisionAlert.id == alert_id, DecisionAlert.user_id == user_id)
                .first()
            )
            if not alert:
                return None
            alert.dismissed_at = datetime.now(UTC)
            session.commit()
            session.refresh(alert)
            session.expunge(alert)
            return alert
        except Exception:
            session.rollback()
            return None
        finally:
            if not self.db_session:
                session.close()

    def _update_read_state(
        self,
        *,
        alert_id: int,
        user_id: str,
        read_at: datetime,
    ) -> DecisionAlert | None:
        session = self._get_session()
        try:
            alert = (
                session.query(DecisionAlert)
                .filter(DecisionAlert.id == alert_id, DecisionAlert.user_id == user_id)
                .first()
            )
            if not alert:
                return None
            alert.read_at = read_at
            session.commit()
            session.refresh(alert)
            session.expunge(alert)
            return alert
        except Exception:
            session.rollback()
            return None
        finally:
            if not self.db_session:
                session.close()
