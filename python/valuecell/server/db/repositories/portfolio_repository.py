"""Repository classes for portfolio holdings, diagnoses, and daily briefings."""

from datetime import date
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..connection import get_database_manager
from ..models.daily_briefing import DailyBriefing
from ..models.holding_diagnosis import HoldingDiagnosis
from ..models.user_holding import UserHolding


class BasePortfolioRepository:
    """Base repository with shared session handling."""

    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session

    def _get_session(self) -> Session:
        if self.db_session is not None:
            return self.db_session
        return get_database_manager().get_session()


class HoldingRepository(BasePortfolioRepository):
    """Repository for user holding CRUD operations."""

    def create_holding(
        self,
        *,
        user_id: str,
        ticker: str,
        exchange: str,
        asset_name: str | None,
        quantity: float,
        cost_price: float,
        position_weight: float | None,
        buy_date: date | None,
        thesis_note: str | None,
        notes: str | None,
    ) -> Optional[UserHolding]:
        session = self._get_session()
        try:
            holding = UserHolding(
                user_id=user_id,
                ticker=ticker,
                exchange=exchange,
                asset_name=asset_name,
                quantity=quantity,
                cost_price=cost_price,
                position_weight=position_weight,
                buy_date=buy_date,
                thesis_note=thesis_note,
                notes=notes,
            )
            session.add(holding)
            session.commit()
            session.refresh(holding)
            session.expunge(holding)
            return holding
        except IntegrityError:
            session.rollback()
            return None
        except Exception:
            session.rollback()
            return None
        finally:
            if self.db_session is None:
                session.close()

    def get_holding(self, holding_id: int, user_id: str) -> Optional[UserHolding]:
        session = self._get_session()
        try:
            holding = (
                session.query(UserHolding)
                .filter(UserHolding.id == holding_id, UserHolding.user_id == user_id)
                .first()
            )
            if holding is not None:
                session.expunge(holding)
            return holding
        finally:
            if self.db_session is None:
                session.close()

    def list_holdings(self, user_id: str) -> list[UserHolding]:
        session = self._get_session()
        try:
            holdings = (
                session.query(UserHolding)
                .filter(UserHolding.user_id == user_id)
                .order_by(desc(UserHolding.updated_at), desc(UserHolding.id))
                .all()
            )
            for item in holdings:
                session.expunge(item)
            return holdings
        finally:
            if self.db_session is None:
                session.close()

    def update_holding(
        self,
        *,
        holding_id: int,
        user_id: str,
        ticker: str,
        exchange: str,
        asset_name: str | None,
        quantity: float,
        cost_price: float,
        position_weight: float | None,
        buy_date: date | None,
        thesis_note: str | None,
        notes: str | None,
    ) -> Optional[UserHolding]:
        session = self._get_session()
        try:
            holding = (
                session.query(UserHolding)
                .filter(UserHolding.id == holding_id, UserHolding.user_id == user_id)
                .first()
            )
            if holding is None:
                return None
            holding.ticker = ticker
            holding.exchange = exchange
            holding.asset_name = asset_name
            holding.quantity = quantity
            holding.cost_price = cost_price
            holding.position_weight = position_weight
            holding.buy_date = buy_date
            holding.thesis_note = thesis_note
            holding.notes = notes
            session.commit()
            session.refresh(holding)
            session.expunge(holding)
            return holding
        except Exception:
            session.rollback()
            return None
        finally:
            if self.db_session is None:
                session.close()

    def delete_holding(self, holding_id: int, user_id: str) -> bool:
        session = self._get_session()
        try:
            holding = (
                session.query(UserHolding)
                .filter(UserHolding.id == holding_id, UserHolding.user_id == user_id)
                .first()
            )
            if holding is None:
                return False
            session.delete(holding)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            if self.db_session is None:
                session.close()


class HoldingDiagnosisRepository(BasePortfolioRepository):
    """Repository for holding diagnosis persistence."""

    def create_diagnosis(
        self,
        *,
        user_id: str,
        holding_id: int,
        diagnosis_date: date,
        action: str,
        risk_level: str,
        confidence: str,
        summary: str,
        key_risk: str | None,
        reasons: list[str],
        trigger_conditions: list[str],
        invalid_conditions: list[str],
        is_focus: bool,
        raw_context: dict,
    ) -> Optional[HoldingDiagnosis]:
        session = self._get_session()
        try:
            diagnosis = HoldingDiagnosis(
                user_id=user_id,
                holding_id=holding_id,
                diagnosis_date=diagnosis_date,
                action=action,
                risk_level=risk_level,
                confidence=confidence,
                summary=summary,
                key_risk=key_risk,
                reasons_json=reasons,
                trigger_conditions_json=trigger_conditions,
                invalid_conditions_json=invalid_conditions,
                is_focus=is_focus,
                raw_context_json=raw_context,
            )
            session.add(diagnosis)
            session.commit()
            session.refresh(diagnosis)
            session.expunge(diagnosis)
            return diagnosis
        except Exception:
            session.rollback()
            return None
        finally:
            if self.db_session is None:
                session.close()

    def get_latest_by_holding(
        self,
        *,
        user_id: str,
        holding_id: int,
    ) -> Optional[HoldingDiagnosis]:
        session = self._get_session()
        try:
            diagnosis = (
                session.query(HoldingDiagnosis)
                .filter(
                    HoldingDiagnosis.user_id == user_id,
                    HoldingDiagnosis.holding_id == holding_id,
                )
                .order_by(
                    desc(HoldingDiagnosis.diagnosis_date),
                    desc(HoldingDiagnosis.created_at),
                    desc(HoldingDiagnosis.id),
                )
                .first()
            )
            if diagnosis is not None:
                session.expunge(diagnosis)
            return diagnosis
        finally:
            if self.db_session is None:
                session.close()

    def list_latest_by_user(self, user_id: str) -> dict[int, HoldingDiagnosis]:
        session = self._get_session()
        try:
            rows = (
                session.query(HoldingDiagnosis)
                .filter(HoldingDiagnosis.user_id == user_id)
                .order_by(
                    desc(HoldingDiagnosis.diagnosis_date),
                    desc(HoldingDiagnosis.created_at),
                    desc(HoldingDiagnosis.id),
                )
                .all()
            )
            latest_map: dict[int, HoldingDiagnosis] = {}
            for row in rows:
                if row.holding_id in latest_map:
                    continue
                session.expunge(row)
                latest_map[row.holding_id] = row
            return latest_map
        finally:
            if self.db_session is None:
                session.close()


class DailyBriefingRepository(BasePortfolioRepository):
    """Repository for daily portfolio briefings."""

    def upsert_briefing(
        self,
        *,
        user_id: str,
        briefing_date: date,
        content_markdown: str,
        summary: dict,
    ) -> Optional[DailyBriefing]:
        session = self._get_session()
        try:
            briefing = (
                session.query(DailyBriefing)
                .filter(
                    DailyBriefing.user_id == user_id,
                    DailyBriefing.briefing_date == briefing_date,
                )
                .first()
            )
            if briefing is None:
                briefing = DailyBriefing(
                    user_id=user_id,
                    briefing_date=briefing_date,
                    content_markdown=content_markdown,
                    summary_json=summary,
                )
                session.add(briefing)
            else:
                briefing.content_markdown = content_markdown
                briefing.summary_json = summary
            session.commit()
            session.refresh(briefing)
            session.expunge(briefing)
            return briefing
        except Exception:
            session.rollback()
            return None
        finally:
            if self.db_session is None:
                session.close()

    def get_latest_briefing(self, user_id: str) -> Optional[DailyBriefing]:
        session = self._get_session()
        try:
            briefing = (
                session.query(DailyBriefing)
                .filter(DailyBriefing.user_id == user_id)
                .order_by(
                    desc(DailyBriefing.briefing_date),
                    desc(DailyBriefing.updated_at),
                    desc(DailyBriefing.id),
                )
                .first()
            )
            if briefing is not None:
                session.expunge(briefing)
            return briefing
        finally:
            if self.db_session is None:
                session.close()

    def get_briefing_by_date(
        self,
        *,
        user_id: str,
        briefing_date: date,
    ) -> Optional[DailyBriefing]:
        session = self._get_session()
        try:
            briefing = (
                session.query(DailyBriefing)
                .filter(
                    DailyBriefing.user_id == user_id,
                    DailyBriefing.briefing_date == briefing_date,
                )
                .first()
            )
            if briefing is not None:
                session.expunge(briefing)
            return briefing
        finally:
            if self.db_session is None:
                session.close()
