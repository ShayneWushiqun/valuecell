"""Holding service for A-share phase one portfolio workflows."""

from __future__ import annotations

from datetime import date
from typing import Optional

from loguru import logger

from ....adapters.assets.ashare_provider import normalize_ashare_ticker
from ...services.assets.asset_service import AssetService
from ...db.repositories.portfolio_repository import (
    HoldingDiagnosisRepository,
    HoldingRepository,
)


class HoldingService:
    """CRUD and presentation service for user holdings."""

    def __init__(
        self,
        holding_repository: Optional[HoldingRepository] = None,
        diagnosis_repository: Optional[HoldingDiagnosisRepository] = None,
        asset_service: Optional[AssetService] = None,
    ) -> None:
        self.holding_repository = holding_repository or HoldingRepository()
        self.diagnosis_repository = diagnosis_repository or HoldingDiagnosisRepository()
        self.asset_service = asset_service or AssetService()

    def list_holdings(self, user_id: str) -> list[dict]:
        holdings = self.holding_repository.list_holdings(user_id)
        diagnosis_map = self.diagnosis_repository.list_latest_by_user(user_id)
        serialized_holdings: list[dict] = []
        for item in holdings:
            holding_data = item.to_dict()
            serialized_holdings.append(
                self._serialize_holding(
                    holding_data,
                    diagnosis_map.get(holding_data["id"]),
                )
            )
        return serialized_holdings

    def get_holding(self, user_id: str, holding_id: int) -> Optional[dict]:
        holding = self.holding_repository.get_holding(holding_id, user_id)
        if holding is None:
            return None
        diagnosis = self.diagnosis_repository.get_latest_by_holding(
            user_id=user_id,
            holding_id=holding_id,
        )
        return self._serialize_holding(holding.to_dict(), diagnosis)

    def create_holding(
        self,
        *,
        user_id: str,
        ticker: str,
        asset_name: str | None,
        quantity: float,
        cost_price: float,
        position_weight: float | None,
        buy_date: date | None,
        thesis_note: str | None,
        notes: str | None,
    ) -> Optional[dict]:
        normalized_ticker = normalize_ashare_ticker(ticker)
        exchange = normalized_ticker.split(":", 1)[0]
        resolved_name = self._resolve_asset_name(normalized_ticker, asset_name)
        holding = self.holding_repository.create_holding(
            user_id=user_id,
            ticker=normalized_ticker,
            exchange=exchange,
            asset_name=resolved_name,
            quantity=quantity,
            cost_price=cost_price,
            position_weight=position_weight,
            buy_date=buy_date,
            thesis_note=thesis_note,
            notes=notes,
        )
        if holding is None:
            return None
        return holding.to_dict()

    def update_holding(
        self,
        *,
        user_id: str,
        holding_id: int,
        ticker: str,
        asset_name: str | None,
        quantity: float,
        cost_price: float,
        position_weight: float | None,
        buy_date: date | None,
        thesis_note: str | None,
        notes: str | None,
    ) -> Optional[dict]:
        normalized_ticker = normalize_ashare_ticker(ticker)
        exchange = normalized_ticker.split(":", 1)[0]
        resolved_name = self._resolve_asset_name(normalized_ticker, asset_name)
        holding = self.holding_repository.update_holding(
            holding_id=holding_id,
            user_id=user_id,
            ticker=normalized_ticker,
            exchange=exchange,
            asset_name=resolved_name,
            quantity=quantity,
            cost_price=cost_price,
            position_weight=position_weight,
            buy_date=buy_date,
            thesis_note=thesis_note,
            notes=notes,
        )
        if holding is None:
            return None
        diagnosis = self.diagnosis_repository.get_latest_by_holding(
            user_id=user_id,
            holding_id=holding_id,
        )
        return self._serialize_holding(holding.to_dict(), diagnosis)

    def delete_holding(self, user_id: str, holding_id: int) -> bool:
        return self.holding_repository.delete_holding(holding_id, user_id)

    def _resolve_asset_name(self, ticker: str, asset_name: str | None) -> str | None:
        if asset_name:
            return asset_name
        asset_info = self.asset_service.get_asset_info(ticker, language="zh-CN")
        if asset_info.get("success") is False:
            return None
        return asset_info.get("display_name")

    def _serialize_holding(self, holding: dict, diagnosis) -> dict:
        latest_diagnosis = diagnosis.to_dict() if diagnosis is not None else None
        raw_context = latest_diagnosis["raw_context"] if latest_diagnosis else {}
        market_snapshot = {
            "current_price": raw_context.get("current_price"),
            "latest_change_percent": raw_context.get("latest_change_percent"),
            "profit_percent": raw_context.get("profit_percent"),
        }
        return {
            **holding,
            "latest_diagnosis": latest_diagnosis,
            "market_snapshot": market_snapshot,
        }


_holding_service: Optional[HoldingService] = None


def get_holding_service() -> HoldingService:
    """Get global holding service instance."""
    global _holding_service
    if _holding_service is None:
        logger.info("Initializing holding service")
        _holding_service = HoldingService()
    return _holding_service
