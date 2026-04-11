from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from valuecell.server.services.assets.short_cycle_data_service import (
    ShortCycleDataService,
)


@dataclass
class FakeMarketBundle:
    daily_info: pd.DataFrame
    limit_list_d: pd.DataFrame
    kpl_list: pd.DataFrame
    ths_hot: pd.DataFrame


@dataclass
class FakeThemeBundle:
    ths_index: pd.DataFrame
    ths_daily: pd.DataFrame
    ths_member: pd.DataFrame
    moneyflow_ind_ths: pd.DataFrame
    moneyflow_ind_dc: pd.DataFrame
    kpl_list: pd.DataFrame
    ths_hot: pd.DataFrame
    tdx_index: pd.DataFrame


@dataclass
class FakeStockBundle:
    daily: pd.DataFrame
    daily_basic: pd.DataFrame
    moneyflow: pd.DataFrame
    stk_limit: pd.DataFrame
    limit_list_d: pd.DataFrame
    ths_hot: pd.DataFrame
    disclosure_date: pd.DataFrame
    stk_holdertrade: pd.DataFrame
    share_float: pd.DataFrame
    top_list: pd.DataFrame
    top_inst: pd.DataFrame
    forecast_vip: pd.DataFrame
    express_vip: pd.DataFrame


class FakeGateway:
    def get_market_pulse_bundle(self, trade_date=None):
        return FakeMarketBundle(
            daily_info=pd.DataFrame([{"trade_date": "20250410", "up_limit": 88}]),
            limit_list_d=pd.DataFrame([{"ticker": "SZSE:000001"}]),
            kpl_list=pd.DataFrame([{"ticker": "SSE:600519"}]),
            ths_hot=pd.DataFrame([{"ticker": "SZSE:300750"}]),
        )

    def get_theme_focus_bundle(self, **kwargs):
        return FakeThemeBundle(
            ths_index=pd.DataFrame([{"ts_code": "885001.TI"}]),
            ths_daily=pd.DataFrame([{"trade_date": "20250410"}]),
            ths_member=pd.DataFrame([{"con_ticker": "SZSE:000001"}]),
            moneyflow_ind_ths=pd.DataFrame([{"trade_date": "20250410"}]),
            moneyflow_ind_dc=pd.DataFrame([{"trade_date": "20250410"}]),
            kpl_list=pd.DataFrame([{"ticker": "SSE:600519"}]),
            ths_hot=pd.DataFrame([{"ticker": "SZSE:300750"}]),
            tdx_index=pd.DataFrame([{"ts_code": "880001.TI"}]),
        )

    def get_stock_observation_bundle(self, ticker: str, **kwargs):
        return FakeStockBundle(
            daily=pd.DataFrame([{"ticker": ticker, "trade_date": "20250410"}]),
            daily_basic=pd.DataFrame([{"ticker": ticker, "turnover_rate": 2.5}]),
            moneyflow=pd.DataFrame([{"ticker": ticker, "net_mf_amount": 10}]),
            stk_limit=pd.DataFrame([{"ticker": ticker, "up_limit": 12.3}]),
            limit_list_d=pd.DataFrame([{"ticker": ticker, "fd_amount": 3.2}]),
            ths_hot=pd.DataFrame([{"ticker": ticker, "rank": 8}]),
            disclosure_date=pd.DataFrame([{"ticker": ticker, "pre_date": "20250430"}]),
            stk_holdertrade=pd.DataFrame([{"ticker": ticker, "holder_name": "张三"}]),
            share_float=pd.DataFrame([{"ticker": ticker, "float_share": 12345}]),
            top_list=pd.DataFrame([{"ticker": ticker, "amount": 2345}]),
            top_inst=pd.DataFrame([{"ticker": ticker, "buy": 678}]),
            forecast_vip=pd.DataFrame([{"ticker": ticker, "type": "预增"}]),
            express_vip=pd.DataFrame([{"ticker": ticker, "revenue": 100}]),
        )


class FakeProvider:
    def __init__(self, gateway):
        self.gateway = gateway

    def get_tushare_short_cycle_gateway(self):
        return self.gateway


def test_short_cycle_data_service_serializes_market_pulse_bundle() -> None:
    service = ShortCycleDataService(ashare_provider=FakeProvider(FakeGateway()))

    result = service.get_market_pulse_data(trade_date="2025-04-10")

    assert result["success"] is True
    assert result["scope"] == "market_pulse"
    assert result["trade_date"] == "2025-04-10"
    assert result["data"]["daily_info"]["count"] == 1
    assert result["data"]["limit_list_d"]["rows"][0]["ticker"] == "SZSE:000001"


def test_short_cycle_data_service_serializes_stock_observation_bundle() -> None:
    service = ShortCycleDataService(ashare_provider=FakeProvider(FakeGateway()))

    result = service.get_stock_observation_data(
        ticker="SZSE:000001",
        trade_date="2025-04-10",
        start_date="2025-04-01",
        end_date="2025-04-10",
    )

    assert result["success"] is True
    assert result["ticker"] == "SZSE:000001"
    assert result["data"]["daily"]["rows"][0]["ticker"] == "SZSE:000001"
    assert result["data"]["forecast_vip"]["count"] == 1
    assert result["data"]["express_vip"]["count"] == 1


def test_short_cycle_data_service_handles_missing_gateway() -> None:
    service = ShortCycleDataService(ashare_provider=FakeProvider(None))

    result = service.get_theme_focus_data(trade_date="2025-04-10")

    assert result["success"] is False
    assert "gateway" in result["error"].lower()
