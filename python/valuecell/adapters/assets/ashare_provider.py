from __future__ import annotations

import os
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

import requests
from loguru import logger

from .manager import get_adapter_manager
from .tushare_adapter import TushareAdapter
from .tushare_short_cycle_gateway import TushareShortCycleGateway
from .types import AssetPrice, DataSource
from valuecell.server.config.settings import get_settings

try:
    import akshare as ak
except ImportError:
    ak = None


ASHARE_PROVIDER_ORDER = [
    "tushare",
    "akshare",
    "baostock",
    "akshare_sina",
    "tencent",
]


def is_ashare_ticker(ticker: str) -> bool:
    normalized = str(ticker).strip().upper()
    return (
        normalized.startswith(("SSE:", "SZSE:", "BSE:"))
        or normalized.endswith((".SH", ".SS", ".SZ", ".BJ"))
        or (normalized.isdigit() and len(normalized) == 6)
    )


def normalize_ashare_ticker(ticker: str) -> str:
    normalized = str(ticker).strip().upper()
    if normalized.startswith(("SSE:", "SZSE:", "BSE:")):
        return normalized
    if normalized.endswith((".SH", ".SS")):
        return f"SSE:{normalized.rsplit('.', 1)[0]}"
    if normalized.endswith(".SZ"):
        return f"SZSE:{normalized[:-3]}"
    if normalized.endswith(".BJ"):
        return f"BSE:{normalized[:-3]}"
    if normalized.isdigit() and len(normalized) == 6:
        if normalized.startswith("6"):
            return f"SSE:{normalized}"
        if normalized.startswith(("0", "2", "3")):
            return f"SZSE:{normalized}"
        return f"BSE:{normalized}"
    raise ValueError(f"Unsupported A-share ticker format: {ticker}")


def to_plain_symbol(ticker: str) -> str:
    return normalize_ashare_ticker(ticker).split(":", 1)[1]


def to_prefixed_symbol(ticker: str) -> str:
    exchange, symbol = normalize_ashare_ticker(ticker).split(":", 1)
    prefix_map = {
        "SSE": "sh",
        "SZSE": "sz",
        "BSE": "bj",
    }
    return f"{prefix_map[exchange]}{symbol}"


class AShareDataProvider:
    def __init__(self, provider_order: list[str] | None = None):
        self.adapter_manager = get_adapter_manager()
        self.provider_order = provider_order or list(ASHARE_PROVIDER_ORDER)
        self._ensure_default_adapters()

    def _ensure_default_adapters(self) -> None:
        settings = get_settings()
        if DataSource.AKSHARE not in self.adapter_manager.adapters:
            try:
                self.adapter_manager.configure_akshare()
            except Exception as exc:
                logger.warning("Auto configure AKShare failed: {}", str(exc))
        if DataSource.TUSHARE not in self.adapter_manager.adapters and settings.TUSHARE_TOKEN:
            try:
                self.adapter_manager.configure_tushare(api_key=settings.TUSHARE_TOKEN)
            except Exception as exc:
                logger.warning("Auto configure Tushare failed: {}", str(exc))
        if DataSource.BAOSTOCK not in self.adapter_manager.adapters:
            try:
                self.adapter_manager.configure_baostock()
            except Exception as exc:
                logger.warning("Auto configure BaoStock failed: {}", str(exc))

    def get_real_time_price(self, ticker: str) -> Optional[AssetPrice]:
        if not is_ashare_ticker(ticker):
            return None
        ticker = normalize_ashare_ticker(ticker)

        for provider in self.provider_order:
            try:
                price = self._get_real_time_price_from_provider(provider, ticker)
            except Exception as exc:
                logger.warning(
                    "A-share realtime provider failed: provider={provider}, ticker={ticker}, err={err}",
                    provider=provider,
                    ticker=ticker,
                    err=str(exc),
                )
                continue
            if price is not None:
                return price
        return None

    def get_historical_prices(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
    ) -> list[AssetPrice]:
        if not is_ashare_ticker(ticker):
            return []
        ticker = normalize_ashare_ticker(ticker)

        for provider in self.provider_order:
            try:
                prices = self._get_historical_prices_from_provider(
                    provider,
                    ticker,
                    start_date,
                    end_date,
                    interval,
                )
            except Exception as exc:
                logger.warning(
                    "A-share historical provider failed: provider={provider}, ticker={ticker}, err={err}",
                    provider=provider,
                    ticker=ticker,
                    err=str(exc),
                )
                continue
            if prices:
                return prices
        return []

    def get_recent_news(self, ticker: str, limit: int = 8) -> list[dict[str, str]]:
        if not is_ashare_ticker(ticker):
            return []
        ticker = normalize_ashare_ticker(ticker)

        api_keys = [
            item.strip()
            for item in os.getenv("TAVILY_API_KEYS", "").split(",")
            if item.strip()
        ]
        if not api_keys:
            return []

        symbol = to_plain_symbol(ticker)
        tushare_adapter = self.adapter_manager.adapters.get(DataSource.TUSHARE)
        asset_info = None
        if tushare_adapter is not None:
            try:
                asset_info = tushare_adapter.get_asset_info(ticker)
            except Exception as exc:
                logger.debug(
                    "A-share company name lookup via Tushare failed: ticker={ticker}, err={err}",
                    ticker=ticker,
                    err=str(exc),
                )
        company_name = ""
        if asset_info is not None:
            company_name = (
                asset_info.names.get_name("zh-CN")
                or asset_info.names.get_name("en-US")
            )
        query_parts = [symbol, ticker, "A股", "股票", "公告", "新闻", "研报"]
        if company_name:
            query_parts.insert(0, company_name)
        query = " ".join(query_parts)
        for api_key in api_keys:
            try:
                response = requests.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": api_key,
                        "query": query,
                        "topic": "news",
                        "max_results": limit,
                        "search_depth": "advanced",
                    },
                    timeout=15,
                )
                response.raise_for_status()
                payload = response.json()
                return [
                    {
                        "title": str(item.get("title") or ""),
                        "url": str(item.get("url") or ""),
                        "content": str(item.get("content") or ""),
                        "published_at": str(item.get("published_date") or ""),
                        "source": str(item.get("source") or "tavily"),
                    }
                    for item in payload.get("results", [])
                ]
            except Exception as exc:
                logger.warning(
                    "A-share Tavily news failed for {ticker}: {err}",
                    ticker=ticker,
                    err=str(exc),
                )
        return []

    def get_tushare_short_cycle_gateway(self) -> Optional[TushareShortCycleGateway]:
        adapter = self.adapter_manager.adapters.get(DataSource.TUSHARE)
        if not isinstance(adapter, TushareAdapter):
            return None
        return TushareShortCycleGateway(adapter)

    def _get_real_time_price_from_provider(
        self,
        provider: str,
        ticker: str,
    ) -> Optional[AssetPrice]:
        if provider == "tushare":
            return self._get_adapter_price(DataSource.TUSHARE, ticker)
        if provider == "akshare":
            return self._get_adapter_price(DataSource.AKSHARE, ticker)
        if provider == "baostock":
            return self._get_adapter_price(DataSource.BAOSTOCK, ticker)
        if provider == "akshare_sina":
            return self._get_price_from_akshare_spot(ticker)
        if provider == "tencent":
            return self._get_price_from_tencent_daily(ticker)
        return None

    def _get_historical_prices_from_provider(
        self,
        provider: str,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
    ) -> list[AssetPrice]:
        if provider == "tushare":
            return self._get_adapter_history(DataSource.TUSHARE, ticker, start_date, end_date, interval)
        if provider == "akshare":
            return self._get_adapter_history(DataSource.AKSHARE, ticker, start_date, end_date, interval)
        if provider == "baostock":
            return self._get_adapter_history(DataSource.BAOSTOCK, ticker, start_date, end_date, interval)
        if provider == "akshare_sina":
            return self._get_history_from_akshare_sina(ticker, start_date, end_date, interval)
        if provider == "tencent":
            return self._get_history_from_tencent(ticker, start_date, end_date, interval)
        return []

    def _get_adapter_price(
        self,
        source: DataSource,
        ticker: str,
    ) -> Optional[AssetPrice]:
        adapter = self.adapter_manager.adapters.get(source)
        if adapter is None or not adapter.validate_ticker(ticker):
            return None
        return adapter.get_real_time_price(ticker)

    def _get_adapter_history(
        self,
        source: DataSource,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
    ) -> list[AssetPrice]:
        adapter = self.adapter_manager.adapters.get(source)
        if adapter is None or not adapter.validate_ticker(ticker):
            return []
        return adapter.get_historical_prices(ticker, start_date, end_date, interval)

    def _get_price_from_akshare_spot(self, ticker: str) -> Optional[AssetPrice]:
        if ak is None:
            return None

        prefixed_symbol = to_prefixed_symbol(ticker)
        spot_frame = ak.stock_zh_a_spot()
        matched = spot_frame.loc[spot_frame["代码"].astype(str) == prefixed_symbol]
        if matched.empty:
            return None

        row = matched.iloc[0]
        price = self._to_decimal(row.get("最新价"))
        if price is None:
            return None
        previous_close = self._to_decimal(row.get("昨收"))
        return AssetPrice(
            ticker=ticker,
            price=price,
            currency="CNY",
            timestamp=self._parse_intraday_timestamp(row.get("时间戳")),
            open_price=self._to_decimal(row.get("今开")),
            high_price=self._to_decimal(row.get("最高")),
            low_price=self._to_decimal(row.get("最低")),
            close_price=price,
            volume=self._to_decimal(row.get("成交量")),
            change=self._to_decimal(row.get("涨跌额")),
            change_percent=self._to_decimal(row.get("涨跌幅")),
            source=DataSource.AKSHARE,
        )

    def _get_price_from_tencent_daily(self, ticker: str) -> Optional[AssetPrice]:
        prices = self._get_history_from_tencent(
            ticker,
            start_date=datetime.now().replace(day=1),
            end_date=datetime.now(),
            interval="1d",
        )
        if not prices:
            return None
        return prices[-1]

    def _get_history_from_akshare_sina(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
    ) -> list[AssetPrice]:
        if ak is None:
            return []

        if interval.endswith("m"):
            period = interval[:-1]
            if period not in {"1", "5", "15", "30", "60"}:
                return []
            frame = ak.stock_zh_a_minute(
                symbol=to_prefixed_symbol(ticker),
                period=period,
                adjust="",
            )
            return self._minute_frame_to_prices(ticker, frame, "day")

        if interval != "1d":
            return []

        frame = ak.stock_zh_a_hist(
            symbol=to_plain_symbol(ticker),
            period="daily",
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d"),
            adjust="",
        )
        if frame is None or frame.empty:
            return []
        prices: list[AssetPrice] = []
        for _, row in frame.iterrows():
            price = self._to_decimal(row.get("收盘"))
            if price is None:
                continue
            prices.append(
                AssetPrice(
                    ticker=ticker,
                    price=price,
                    currency="CNY",
                    timestamp=self._coerce_datetime(row.get("日期")),
                    open_price=self._to_decimal(row.get("开盘")),
                    high_price=self._to_decimal(row.get("最高")),
                    low_price=self._to_decimal(row.get("最低")),
                    close_price=price,
                    volume=self._to_decimal(row.get("成交量")),
                    change=self._to_decimal(row.get("涨跌额")),
                    change_percent=self._to_decimal(row.get("涨跌幅")),
                    source=DataSource.AKSHARE,
                )
            )
        return prices

    def _get_history_from_tencent(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
    ) -> list[AssetPrice]:
        if ak is None or interval != "1d":
            return []

        frame = ak.stock_zh_a_hist_tx(
            symbol=to_prefixed_symbol(ticker),
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d"),
        )
        if frame is None or frame.empty:
            return []

        prices: list[AssetPrice] = []
        for _, row in frame.iterrows():
            price = self._to_decimal(row.get("close"))
            if price is None:
                continue
            prices.append(
                AssetPrice(
                    ticker=ticker,
                    price=price,
                    currency="CNY",
                    timestamp=self._coerce_datetime(row.get("date")),
                    open_price=self._to_decimal(row.get("open")),
                    high_price=self._to_decimal(row.get("high")),
                    low_price=self._to_decimal(row.get("low")),
                    close_price=price,
                    volume=self._to_decimal(row.get("amount")),
                    source=DataSource.AKSHARE,
                )
            )
        return prices

    def _minute_frame_to_prices(
        self,
        ticker: str,
        frame,
        timestamp_column: str,
    ) -> list[AssetPrice]:
        if frame is None or frame.empty:
            return []
        prices: list[AssetPrice] = []
        for _, row in frame.iterrows():
            price = self._to_decimal(row.get("close"))
            if price is None:
                continue
            prices.append(
                AssetPrice(
                    ticker=ticker,
                    price=price,
                    currency="CNY",
                    timestamp=self._coerce_datetime(row.get(timestamp_column)),
                    open_price=self._to_decimal(row.get("open")),
                    high_price=self._to_decimal(row.get("high")),
                    low_price=self._to_decimal(row.get("low")),
                    close_price=price,
                    volume=self._to_decimal(row.get("volume")),
                    source=DataSource.AKSHARE,
                )
            )
        return prices

    @staticmethod
    def _to_decimal(value: Any) -> Optional[Decimal]:
        if value in (None, ""):
            return None
        try:
            return Decimal(str(value))
        except Exception:
            return None

    @staticmethod
    def _coerce_datetime(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if hasattr(value, "to_pydatetime"):
            return value.to_pydatetime()
        if hasattr(value, "strftime"):
            return datetime.strptime(value.strftime("%Y-%m-%d"), "%Y-%m-%d")
        text = str(value)
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return datetime.now()

    @staticmethod
    def _parse_intraday_timestamp(value: Any) -> datetime:
        text = str(value or "").strip()
        if text:
            try:
                return datetime.strptime(
                    f"{datetime.now():%Y-%m-%d} {text}",
                    "%Y-%m-%d %H:%M:%S",
                )
            except ValueError:
                pass
        return datetime.now()
