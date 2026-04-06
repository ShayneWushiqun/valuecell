from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, List, Optional

from loguru import logger

from .base import AdapterCapability, BaseDataAdapter
from .types import (
    Asset,
    AssetPrice,
    AssetSearchQuery,
    AssetSearchResult,
    AssetType,
    DataSource,
    Exchange,
    LocalizedName,
    MarketInfo,
    MarketStatus,
)

try:
    import tushare as ts
except ImportError:
    ts = None


class TushareAdapter(BaseDataAdapter):
    def __init__(self, api_key: str | None = None, **kwargs):
        super().__init__(DataSource.TUSHARE, api_key=api_key, **kwargs)

        if ts is None:
            raise ImportError("tushare library is not installed.")
        if not self.api_key:
            raise ValueError("Tushare token is required.")

    def _initialize(self) -> None:
        if ts is None:
            raise ImportError("tushare library is not installed.")
        self.pro = ts.pro_api(self.api_key)
        self.exchange_mapping = {
            Exchange.SSE: ".SH",
            Exchange.SZSE: ".SZ",
            Exchange.BSE: ".BJ",
        }

    def search_assets(self, query: AssetSearchQuery) -> List[AssetSearchResult]:
        basics = self._get_stock_basic()
        if basics.empty:
            return []

        lookup = query.query.strip().lower()
        mask = (
            basics["ts_code"].fillna("").str.lower().str.contains(lookup)
            | basics["symbol"].fillna("").str.lower().str.contains(lookup)
            | basics["name"].fillna("").str.lower().str.contains(lookup)
        )
        matched = basics.loc[mask].head(query.limit)
        results: List[AssetSearchResult] = []
        for _, row in matched.iterrows():
            ticker = self.convert_to_internal_ticker(str(row["ts_code"]))
            results.append(
                AssetSearchResult(
                    ticker=ticker,
                    asset_type=AssetType.STOCK,
                    names={
                        "zh-CN": str(row.get("name") or ticker),
                        "en-US": str(row.get("name") or ticker),
                    },
                    exchange=ticker.split(":")[0],
                    country="CN",
                    currency="CNY",
                    market_status=MarketStatus.UNKNOWN,
                    relevance_score=1.0,
                )
            )
        return results

    def get_asset_info(self, ticker: str) -> Optional[Asset]:
        source_ticker = self.convert_to_source_ticker(ticker)
        basics = self._get_stock_basic()
        matched = basics.loc[basics["ts_code"] == source_ticker]
        if matched.empty:
            return None

        row = matched.iloc[0]
        exchange = Exchange(ticker.split(":")[0])
        names = LocalizedName()
        display_name = str(row.get("name") or ticker)
        names.set_name("zh-CN", display_name)
        names.set_name("en-US", display_name)
        return Asset(
            ticker=ticker,
            asset_type=AssetType.STOCK,
            names=names,
            market_info=MarketInfo(
                exchange=exchange.value,
                country="CN",
                currency="CNY",
                timezone="Asia/Shanghai",
                market_status=MarketStatus.UNKNOWN,
            ),
            source_mappings={DataSource.TUSHARE: source_ticker},
            properties={
                "industry": row.get("industry"),
                "market": row.get("market"),
                "list_date": row.get("list_date"),
            },
        )

    def get_real_time_price(self, ticker: str) -> Optional[AssetPrice]:
        source_ticker = self.convert_to_source_ticker(ticker)

        daily_frame = self.pro.daily(
            ts_code=source_ticker,
            start_date=datetime.now().strftime("%Y%m%d"),
            end_date=datetime.now().strftime("%Y%m%d"),
        )
        if daily_frame is None or daily_frame.empty:
            daily_frame = self.pro.daily(
                ts_code=source_ticker,
                start_date=(datetime.now().replace(day=1)).strftime("%Y%m%d"),
                end_date=datetime.now().strftime("%Y%m%d"),
            )
        if daily_frame is None or daily_frame.empty:
            return None

        row = daily_frame.iloc[0]
        price = self._to_decimal(row.get("close"))
        if price is None:
            return None
        pre_close = price
        change = self._to_decimal(row.get("change"))
        if change is not None:
            pre_close = price - change
        return AssetPrice(
            ticker=ticker,
            price=price,
            currency="CNY",
            timestamp=datetime.strptime(str(row["trade_date"]), "%Y%m%d"),
            open_price=self._to_decimal(row.get("open")),
            high_price=self._to_decimal(row.get("high")),
            low_price=self._to_decimal(row.get("low")),
            close_price=price,
            volume=self._to_decimal(row.get("vol")),
            change=change,
            change_percent=self._to_decimal(row.get("pct_chg")),
            source=DataSource.TUSHARE,
        )

    def get_historical_prices(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
    ) -> List[AssetPrice]:
        if interval != "1d":
            return []

        source_ticker = self.convert_to_source_ticker(ticker)
        daily_frame = self.pro.daily(
            ts_code=source_ticker,
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d"),
        )
        if daily_frame is None or daily_frame.empty:
            return []

        prices: List[AssetPrice] = []
        for _, row in daily_frame.sort_values("trade_date").iterrows():
            price = self._to_decimal(row.get("close"))
            if price is None:
                continue
            prices.append(
                AssetPrice(
                    ticker=ticker,
                    price=price,
                    currency="CNY",
                    timestamp=datetime.strptime(str(row["trade_date"]), "%Y%m%d"),
                    open_price=self._to_decimal(row.get("open")),
                    high_price=self._to_decimal(row.get("high")),
                    low_price=self._to_decimal(row.get("low")),
                    close_price=price,
                    volume=self._to_decimal(row.get("vol")),
                    change=self._to_decimal(row.get("change")),
                    change_percent=self._to_decimal(row.get("pct_chg")),
                    source=DataSource.TUSHARE,
                )
            )
        return prices

    def convert_to_source_ticker(self, internal_ticker: str) -> str:
        exchange_str, symbol = internal_ticker.split(":", 1)
        exchange = Exchange(exchange_str)
        suffix = self.exchange_mapping.get(exchange)
        if suffix is None:
            raise ValueError(f"Unsupported exchange for Tushare: {exchange_str}")
        return f"{symbol}{suffix}"

    def convert_to_internal_ticker(
        self, source_ticker: str, default_exchange: Optional[str] = None
    ) -> str:
        normalized = source_ticker.upper()
        if normalized.endswith(".SH"):
            return f"{Exchange.SSE.value}:{normalized[:-3]}"
        if normalized.endswith(".SZ"):
            return f"{Exchange.SZSE.value}:{normalized[:-3]}"
        if normalized.endswith(".BJ"):
            return f"{Exchange.BSE.value}:{normalized[:-3]}"
        if default_exchange:
            return f"{default_exchange}:{normalized}"
        raise ValueError(f"Unsupported Tushare ticker: {source_ticker}")

    def get_capabilities(self) -> List[AdapterCapability]:
        return [
            AdapterCapability(
                asset_type=AssetType.STOCK,
                exchanges={Exchange.SSE, Exchange.SZSE, Exchange.BSE},
            )
        ]

    def _get_stock_basic(self):
        return self.pro.stock_basic(
            exchange="",
            list_status="L",
            fields="ts_code,symbol,name,area,industry,market,list_date",
        )

    @staticmethod
    def _to_decimal(value: Any) -> Optional[Decimal]:
        if value in (None, ""):
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return None
