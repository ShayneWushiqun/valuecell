from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pandas as pd

from valuecell.adapters.assets.tushare_adapter import TushareAdapter
from valuecell.adapters.assets.tushare_short_cycle_gateway import (
    TushareShortCycleGateway,
)


class FakePro:
    def __init__(self):
        self.calls: list[tuple[str, dict]] = []

    def stock_basic(self, **kwargs):
        self.calls.append(("stock_basic", kwargs))
        return pd.DataFrame(
            [
                {
                    "ts_code": "000001.SZ",
                    "symbol": "000001",
                    "name": "平安银行",
                    "area": "深圳",
                    "industry": "银行",
                    "market": "主板",
                    "list_date": "19910403",
                }
            ]
        )

    def __getattr__(self, name: str):
        def caller(**kwargs):
            self.calls.append((name, kwargs))
            if name == "ths_member":
                return pd.DataFrame(
                    [{"ts_code": "885001.TI", "con_code": "000001.SZ"}]
                )
            if name in {"ths_index", "tdx_index"}:
                return pd.DataFrame([{"ts_code": "885001.TI", "name": "AI概念"}])
            if name == "daily_info":
                return pd.DataFrame([{"trade_date": "20250410", "up_limit": 80}])
            return pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "20250410"}])

        return caller


def build_adapter(monkeypatch) -> tuple[TushareAdapter, FakePro]:
    fake_pro = FakePro()
    fake_ts = SimpleNamespace(pro_api=lambda api_key: fake_pro)
    monkeypatch.setattr("valuecell.adapters.assets.tushare_adapter.ts", fake_ts)
    adapter = TushareAdapter(api_key="token")
    return adapter, fake_pro


def test_tushare_adapter_short_cycle_methods_normalize_params(monkeypatch) -> None:
    adapter, fake_pro = build_adapter(monkeypatch)

    daily_basic = adapter.get_daily_basic_frame(
        ticker="SZSE:000001",
        trade_date="2025-04-10",
    )
    moneyflow = adapter.get_moneyflow_frame(
        ticker="600519",
        start_date=date(2025, 4, 1),
        end_date=date(2025, 4, 10),
    )
    top_list = adapter.get_top_list_frame(
        ticker="000001.SZ",
        trade_date="20250410",
    )

    assert not daily_basic.empty
    assert not moneyflow.empty
    assert not top_list.empty

    call_map = {name: params for name, params in fake_pro.calls}
    assert call_map["daily_basic"]["ts_code"] == "000001.SZ"
    assert call_map["daily_basic"]["trade_date"] == "20250410"
    assert call_map["moneyflow"]["ts_code"] == "600519.SH"
    assert call_map["moneyflow"]["start_date"] == "20250401"
    assert call_map["moneyflow"]["end_date"] == "20250410"
    assert call_map["top_list"]["ts_code"] == "000001.SZ"


def test_tushare_adapter_adds_internal_ticker_columns(monkeypatch) -> None:
    adapter, _ = build_adapter(monkeypatch)

    daily = adapter.get_daily_frame(ticker="SZSE:000001", trade_date="20250410")
    members = adapter.get_ths_member_frame(ts_code="885001.TI", trade_date="20250410")

    assert daily.loc[0, "ticker"] == "SZSE:000001"
    assert members.loc[0, "con_ticker"] == "SZSE:000001"


def test_tushare_short_cycle_gateway_returns_reusable_bundles(monkeypatch) -> None:
    adapter, _ = build_adapter(monkeypatch)
    gateway = TushareShortCycleGateway(adapter)

    market_bundle = gateway.get_market_pulse_bundle(trade_date="20250410")
    theme_bundle = gateway.get_theme_focus_bundle(
        trade_date="20250410",
        start_date="20250401",
        end_date="20250410",
        ths_index_code="885001.TI",
        tdx_index_code="880001.TI",
    )
    stock_bundle = gateway.get_stock_observation_bundle(
        ticker="SZSE:000001",
        trade_date="20250410",
        start_date="20250401",
        end_date="20250410",
    )

    assert not market_bundle.daily_info.empty
    assert not market_bundle.limit_list_d.empty
    assert not theme_bundle.ths_index.empty
    assert not theme_bundle.moneyflow_ind_ths.empty
    assert not stock_bundle.daily.empty
    assert not stock_bundle.forecast_vip.empty
    assert not stock_bundle.express_vip.empty
