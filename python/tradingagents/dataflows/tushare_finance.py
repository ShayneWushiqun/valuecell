from __future__ import annotations

from functools import lru_cache
from typing import Any

import pandas as pd
import tushare as ts

from valuecell.adapters.assets.ashare_provider import is_ashare_ticker, normalize_ashare_ticker
from valuecell.server.config.settings import get_settings


BALANCE_SHEET_FIELDS = [
    "end_date",
    "total_assets",
    "total_liab",
    "total_hldr_eqy_exc_min_int",
    "money_cap",
    "trad_asset",
    "debt_invest",
    "oth_debt_invest",
    "accounts_receiv",
    "prepayment",
    "inventories",
    "fix_assets",
    "intan_assets",
    "goodwill",
    "defer_tax_assets",
    "st_borr",
    "lt_borr",
    "bond_payable",
    "total_cur_liab",
    "total_ncl",
]

CASHFLOW_FIELDS = [
    "end_date",
    "net_profit",
    "c_inf_fr_operate_a",
    "st_cash_out_act",
    "n_cashflow_act",
    "c_disp_withdrwl_invest",
    "c_paid_invest",
    "n_cashflow_inv_act",
    "stot_cash_in_fnc_act",
    "stot_cashout_fnc_act",
    "n_cash_flows_fnc_act",
    "free_cashflow",
    "n_incr_cash_cash_equ",
    "c_cash_equ_beg_period",
    "c_cash_equ_end_period",
]

INCOME_FIELDS = [
    "end_date",
    "basic_eps",
    "diluted_eps",
    "total_revenue",
    "revenue",
    "int_income",
    "oper_cost",
    "admin_exp",
    "fin_exp",
    "sell_exp",
    "rd_exp",
    "operate_profit",
    "total_profit",
    "income_tax",
    "n_income",
    "n_income_attr_p",
]


@lru_cache()
def _get_tushare_pro():
    token = get_settings().TUSHARE_TOKEN
    if not token:
        raise ValueError("TUSHARE_TOKEN is not configured.")
    return ts.pro_api(token)


def is_tushare_ashare_ticker(ticker: str) -> bool:
    return is_ashare_ticker(ticker)


def to_tushare_ts_code(ticker: str) -> str:
    normalized = normalize_ashare_ticker(ticker)
    exchange, symbol = normalized.split(":", 1)
    if exchange == "SSE":
        return f"{symbol}.SH"
    if exchange == "SZSE":
        return f"{symbol}.SZ"
    if exchange == "BSE":
        return f"{symbol}.BJ"
    raise ValueError(f"Unsupported exchange for ticker {ticker}")


def get_ashare_fundamentals(ticker: str, curr_date: str | None = None) -> str:
    pro = _get_tushare_pro()
    ts_code = to_tushare_ts_code(ticker)
    current_date = pd.to_datetime(curr_date or pd.Timestamp.now()).strftime("%Y%m%d")
    start_date = (pd.to_datetime(current_date) - pd.DateOffset(years=5)).strftime("%Y%m%d")

    basic_df = pro.stock_basic(
        ts_code=ts_code,
        fields="ts_code,symbol,name,area,industry,market,list_date",
    )
    indicator_df = pro.fina_indicator(
        ts_code=ts_code,
        start_date=start_date,
        end_date=current_date,
    )
    daily_basic_df = pro.daily_basic(
        ts_code=ts_code,
        start_date=(pd.to_datetime(current_date) - pd.DateOffset(days=45)).strftime("%Y%m%d"),
        end_date=current_date,
    )
    income_df = pro.income(
        ts_code=ts_code,
        start_date=start_date,
        end_date=current_date,
    )

    basic_row = basic_df.iloc[0] if basic_df is not None and not basic_df.empty else None
    indicator_row = _pick_latest_row(indicator_df)
    daily_basic_row = _pick_latest_row(daily_basic_df, "trade_date")
    income_row = _pick_latest_row(income_df)

    fields = [
        ("Name", _row_value(basic_row, "name")),
        ("TS Code", ts_code),
        ("Industry", _row_value(basic_row, "industry")),
        ("Area", _row_value(basic_row, "area")),
        ("Market", _row_value(basic_row, "market")),
        ("List Date", _row_value(basic_row, "list_date")),
        ("Report Date", _row_value(indicator_row, "end_date")),
        ("PE", _row_value(daily_basic_row, "pe")),
        ("PE TTM", _row_value(daily_basic_row, "pe_ttm")),
        ("PB", _row_value(daily_basic_row, "pb")),
        ("PS TTM", _row_value(daily_basic_row, "ps_ttm")),
        ("Dividend Yield TTM", _row_value(daily_basic_row, "dv_ttm")),
        ("Total Market Value", _row_value(daily_basic_row, "total_mv")),
        ("Circulating Market Value", _row_value(daily_basic_row, "circ_mv")),
        ("EPS", _row_value(indicator_row, "eps")),
        ("Diluted EPS", _row_value(indicator_row, "diluted2_eps")),
        ("BPS", _row_value(indicator_row, "bps")),
        ("CFPS", _row_value(indicator_row, "cfps")),
        ("ROE", _row_value(indicator_row, "roe")),
        ("ROE YoY", _row_value(indicator_row, "roe_yoy")),
        ("ROA", _row_value(indicator_row, "roa")),
        ("Gross Profit Margin", _row_value(indicator_row, "grossprofit_margin")),
        ("Net Profit Margin", _row_value(indicator_row, "netprofit_margin")),
        ("Debt To Assets", _row_value(indicator_row, "debt_to_assets")),
        ("Current Ratio", _row_value(indicator_row, "current_ratio")),
        ("Quick Ratio", _row_value(indicator_row, "quick_ratio")),
        ("Net Profit YoY", _row_value(indicator_row, "netprofit_yoy")),
        ("Operating Income YoY", _row_value(indicator_row, "op_yoy")),
        ("Revenue YoY", _row_value(indicator_row, "tr_yoy")),
        ("Operating Income", _row_value(indicator_row, "op_income")),
        ("EBIT", _row_value(indicator_row, "ebit")),
        ("EBITDA", _row_value(indicator_row, "ebitda")),
        ("FCFF", _row_value(indicator_row, "fcff")),
        ("FCFE", _row_value(indicator_row, "fcfe")),
        ("Latest Revenue", _row_value(income_row, "revenue")),
        ("Latest Total Revenue", _row_value(income_row, "total_revenue")),
        ("Latest Net Income", _row_value(income_row, "n_income_attr_p")),
        ("Latest Operating Profit", _row_value(income_row, "operate_profit")),
        ("Latest Total Profit", _row_value(income_row, "total_profit")),
    ]

    lines = [f"{label}: {value}" for label, value in fields if value not in (None, "", "nan")]
    if not lines:
        return f"No fundamentals data found for symbol '{ticker}'"

    header = f"# Company Fundamentals for {ticker.upper()}\n"
    header += f"# Data retrieved on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    return header + "\n".join(lines)


def get_ashare_statement(
    ticker: str,
    statement_type: str,
    freq: str = "quarterly",
    curr_date: str | None = None,
) -> str:
    pro = _get_tushare_pro()
    ts_code = to_tushare_ts_code(ticker)
    current_date = pd.to_datetime(curr_date or pd.Timestamp.now()).strftime("%Y%m%d")
    start_date = (pd.to_datetime(current_date) - pd.DateOffset(years=5)).strftime("%Y%m%d")

    fetchers = {
        "balance_sheet": ("balancesheet", BALANCE_SHEET_FIELDS),
        "cashflow": ("cashflow", CASHFLOW_FIELDS),
        "income_statement": ("income", INCOME_FIELDS),
    }
    if statement_type not in fetchers:
        raise ValueError(f"Unsupported statement type: {statement_type}")

    api_name, selected_fields = fetchers[statement_type]
    data = getattr(pro, api_name)(
        ts_code=ts_code,
        start_date=start_date,
        end_date=current_date,
    )
    if data is None or data.empty:
        return _statement_empty_message(statement_type, ticker)

    filtered = _prepare_statement_frame(data, selected_fields, freq, curr_date)
    if filtered.empty:
        return _statement_empty_message(statement_type, ticker)

    header = f"# {statement_type.replace('_', ' ').title()} data for {ticker.upper()} ({freq})\n"
    header += f"# Data retrieved on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    return header + filtered.to_csv(index=False)


def _statement_empty_message(statement_type: str, ticker: str) -> str:
    label = statement_type.replace("_", " ")
    return f"No {label} data found for symbol '{ticker}'"


def _pick_latest_row(data: pd.DataFrame | None, sort_column: str = "end_date") -> pd.Series | None:
    if data is None or data.empty:
        return None
    sort_columns = [column for column in [sort_column, "ann_date"] if column in data.columns]
    if not sort_columns:
        return data.iloc[0]
    sorted_data = data.sort_values(sort_columns, ascending=False, na_position="last")
    return sorted_data.iloc[0]


def _row_value(row: pd.Series | None, key: str) -> Any:
    if row is None:
        return None
    value = row.get(key)
    if isinstance(value, (list, dict, tuple, set)):
        return value
    if value is None:
        return None
    if bool(pd.isna(value)):
        return None
    return value


def _prepare_statement_frame(
    data: pd.DataFrame,
    selected_fields: list[str],
    freq: str,
    curr_date: str | None,
) -> pd.DataFrame:
    prepared = data.copy()
    prepared["end_date"] = pd.to_datetime(prepared["end_date"], format="%Y%m%d", errors="coerce")
    if "ann_date" in prepared.columns:
        prepared["ann_date"] = pd.to_datetime(prepared["ann_date"], format="%Y%m%d", errors="coerce")
    if curr_date:
        cutoff = pd.to_datetime(curr_date)
        prepared = prepared.loc[prepared["end_date"] <= cutoff]
    if freq.lower() == "annual":
        prepared = prepared.loc[prepared["end_date"].dt.strftime("%m%d") == "1231"]
        limit = 5
    else:
        limit = 8
    available_fields = [field for field in selected_fields if field in prepared.columns]
    sort_columns = [column for column in ["end_date", "ann_date"] if column in prepared.columns]
    prepared = prepared.sort_values(sort_columns, ascending=False, na_position="last")
    prepared = prepared[available_fields].head(limit).copy()
    prepared["end_date"] = pd.to_datetime(prepared["end_date"]).dt.strftime("%Y-%m-%d")
    return prepared
