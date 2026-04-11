from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from typing import Any, Optional

import pandas as pd
from loguru import logger

from ....adapters.assets.ashare_provider import AShareDataProvider
from ....adapters.assets.tushare_short_cycle_gateway import TushareShortCycleGateway


class ShortCycleDataService:
    def __init__(
        self,
        ashare_provider: Optional[AShareDataProvider] = None,
    ) -> None:
        self.ashare_provider = ashare_provider or AShareDataProvider()

    def get_market_pulse_data(
        self,
        trade_date: str | date | datetime | None = None,
    ) -> dict[str, Any]:
        gateway = self._get_gateway()
        if gateway is None:
            return self._gateway_unavailable_response()
        bundle = gateway.get_market_pulse_bundle(trade_date=trade_date)
        return {
            "success": True,
            "scope": "market_pulse",
            "trade_date": self._stringify_value(trade_date),
            "data": self._serialize_bundle(bundle),
        }

    def get_market_pulse_window_data(
        self,
        start_date: str | date | datetime,
        end_date: str | date | datetime,
        max_points: int = 7,
    ) -> dict[str, Any]:
        gateway = self._get_gateway()
        if gateway is None:
            return self._gateway_unavailable_response()

        trade_dates_frame = gateway.adapter.get_daily_info_frame(
            start_date=start_date,
            end_date=end_date,
            fields="trade_date",
        )
        if trade_dates_frame.empty or "trade_date" not in trade_dates_frame.columns:
            return {
                "success": True,
                "scope": "market_pulse_window",
                "start_date": self._stringify_value(start_date),
                "end_date": self._stringify_value(end_date),
                "items": [],
            }

        trade_dates = sorted(
            {
                str(value)
                for value in trade_dates_frame["trade_date"].tolist()
                if value not in (None, "")
            }
        )[-max_points:]
        items = [
            self.get_market_pulse_data(trade_date=trade_date)
            for trade_date in trade_dates
        ]
        return {
            "success": True,
            "scope": "market_pulse_window",
            "start_date": self._stringify_value(start_date),
            "end_date": self._stringify_value(end_date),
            "items": items,
        }

    def get_theme_focus_data(
        self,
        trade_date: str | date | datetime | None = None,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
        ths_index_code: str | None = None,
        tdx_index_code: str | None = None,
        **filters: Any,
    ) -> dict[str, Any]:
        gateway = self._get_gateway()
        if gateway is None:
            return self._gateway_unavailable_response()
        bundle = gateway.get_theme_focus_bundle(
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
            ths_index_code=ths_index_code,
            tdx_index_code=tdx_index_code,
            **filters,
        )
        return {
            "success": True,
            "scope": "theme_focus",
            "trade_date": self._stringify_value(trade_date),
            "start_date": self._stringify_value(start_date),
            "end_date": self._stringify_value(end_date),
            "ths_index_code": ths_index_code,
            "tdx_index_code": tdx_index_code,
            "data": self._serialize_bundle(bundle),
        }

    def get_stock_observation_data(
        self,
        ticker: str,
        trade_date: str | date | datetime | None = None,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
    ) -> dict[str, Any]:
        gateway = self._get_gateway()
        if gateway is None:
            return self._gateway_unavailable_response()
        bundle = gateway.get_stock_observation_bundle(
            ticker=ticker,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
        )
        return {
            "success": True,
            "scope": "stock_observation",
            "ticker": ticker,
            "trade_date": self._stringify_value(trade_date),
            "start_date": self._stringify_value(start_date),
            "end_date": self._stringify_value(end_date),
            "data": self._serialize_bundle(bundle),
        }

    def _get_gateway(self) -> Optional[TushareShortCycleGateway]:
        try:
            return self.ashare_provider.get_tushare_short_cycle_gateway()
        except Exception as exc:
            logger.warning("Failed to get short cycle gateway: {}", str(exc))
            return None

    def _gateway_unavailable_response(self) -> dict[str, Any]:
        return {
            "success": False,
            "error": "Tushare short cycle gateway is not available",
            "data": {},
        }

    def _serialize_bundle(self, bundle: Any) -> dict[str, Any]:
        if not is_dataclass(bundle):
            return {}
        serialized: dict[str, Any] = {}
        for key, value in asdict(bundle).items():
            if isinstance(value, pd.DataFrame):
                serialized[key] = self._serialize_frame(value)
                continue
            serialized[key] = value
        for key, value in vars(bundle).items():
            if isinstance(value, pd.DataFrame):
                serialized[key] = self._serialize_frame(value)
        return serialized

    @staticmethod
    def _serialize_frame(frame: pd.DataFrame) -> dict[str, Any]:
        safe_frame = frame.where(pd.notnull(frame), None)
        return {
            "count": int(len(safe_frame.index)),
            "columns": [str(column) for column in safe_frame.columns.tolist()],
            "rows": safe_frame.to_dict(orient="records"),
        }

    @staticmethod
    def _stringify_value(value: str | date | datetime | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        if isinstance(value, date):
            return value.isoformat()
        return str(value)


_short_cycle_data_service: Optional[ShortCycleDataService] = None


def get_short_cycle_data_service() -> ShortCycleDataService:
    global _short_cycle_data_service
    if _short_cycle_data_service is None:
        _short_cycle_data_service = ShortCycleDataService()
    return _short_cycle_data_service


def reset_short_cycle_data_service() -> None:
    global _short_cycle_data_service
    _short_cycle_data_service = None
