from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

import pandas as pd

from .tushare_adapter import TushareAdapter


@dataclass
class MarketPulseBundle:
    daily_info: pd.DataFrame
    limit_list_d: pd.DataFrame
    kpl_list: pd.DataFrame
    ths_hot: pd.DataFrame


@dataclass
class ThemeFocusBundle:
    ths_index: pd.DataFrame
    ths_daily: pd.DataFrame
    ths_member: pd.DataFrame
    moneyflow_ind_ths: pd.DataFrame
    moneyflow_ind_dc: pd.DataFrame
    kpl_list: pd.DataFrame
    ths_hot: pd.DataFrame
    tdx_index: pd.DataFrame


@dataclass
class StockObservationBundle:
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


class TushareShortCycleGateway:
    def __init__(self, adapter: TushareAdapter):
        self.adapter = adapter

    def get_market_pulse_bundle(
        self,
        trade_date: str | date | datetime | None = None,
    ) -> MarketPulseBundle:
        return MarketPulseBundle(
            daily_info=self.adapter.get_daily_info_frame(trade_date=trade_date),
            limit_list_d=self.adapter.get_limit_list_d_frame(trade_date=trade_date),
            kpl_list=self.adapter.get_kpl_list_frame(trade_date=trade_date),
            ths_hot=self.adapter.get_ths_hot_frame(trade_date=trade_date),
        )

    def get_theme_focus_bundle(
        self,
        trade_date: str | date | datetime | None = None,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
        ths_index_code: str | None = None,
        tdx_index_code: str | None = None,
        **filters,
    ) -> ThemeFocusBundle:
        return ThemeFocusBundle(
            ths_index=self.adapter.get_ths_index_frame(**filters),
            ths_daily=self.adapter.get_ths_daily_frame(
                ts_code=ths_index_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
            ),
            ths_member=self.adapter.get_ths_member_frame(
                ts_code=ths_index_code,
                trade_date=trade_date,
            ),
            moneyflow_ind_ths=self.adapter.get_moneyflow_ind_ths_frame(
                ts_code=ths_index_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
            ),
            moneyflow_ind_dc=self.adapter.get_moneyflow_ind_dc_frame(
                ts_code=ths_index_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
            ),
            kpl_list=self.adapter.get_kpl_list_frame(trade_date=trade_date),
            ths_hot=self.adapter.get_ths_hot_frame(trade_date=trade_date),
            tdx_index=self.adapter.get_tdx_index_frame(ts_code=tdx_index_code),
        )

    def get_stock_observation_bundle(
        self,
        ticker: str,
        trade_date: str | date | datetime | None = None,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
    ) -> StockObservationBundle:
        return StockObservationBundle(
            daily=self.adapter.get_daily_frame(
                ticker=ticker,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
            ),
            daily_basic=self.adapter.get_daily_basic_frame(
                ticker=ticker,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
            ),
            moneyflow=self.adapter.get_moneyflow_frame(
                ticker=ticker,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
            ),
            stk_limit=self.adapter.get_stk_limit_frame(
                ticker=ticker,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
            ),
            limit_list_d=self.adapter.get_limit_list_d_frame(
                ticker=ticker,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
            ),
            ths_hot=self.adapter.get_ths_hot_frame(
                ticker=ticker,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
            ),
            disclosure_date=self.adapter.get_disclosure_date_frame(
                ticker=ticker,
                end_date=end_date,
            ),
            stk_holdertrade=self.adapter.get_stk_holdertrade_frame(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
            ),
            share_float=self.adapter.get_share_float_frame(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
            ),
            top_list=self.adapter.get_top_list_frame(
                ticker=ticker,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
            ),
            top_inst=self.adapter.get_top_inst_frame(
                ticker=ticker,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
            ),
            forecast_vip=self.adapter.get_forecast_vip_frame(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
            ),
            express_vip=self.adapter.get_express_vip_frame(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
            ),
        )
