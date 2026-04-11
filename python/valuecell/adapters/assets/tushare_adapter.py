from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, List, Optional

from loguru import logger
import pandas as pd

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
        self.pro = ts.pro_api(str(self.api_key))
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
        change = self._to_decimal(row.get("change"))
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

    def get_daily_frame(
        self,
        ticker: str | None = None,
        trade_date: str | date | datetime | None = None,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> pd.DataFrame:
        return self._get_tushare_frame(
            "daily",
            ticker=ticker,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            limit=limit,
            offset=offset,
            **filters,
        )

    def get_daily_basic_frame(
        self,
        ticker: str | None = None,
        trade_date: str | date | datetime | None = None,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> pd.DataFrame:
        return self._get_tushare_frame(
            "daily_basic",
            ticker=ticker,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            limit=limit,
            offset=offset,
            **filters,
        )

    def get_daily_info_frame(
        self,
        trade_date: str | date | datetime | None = None,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> pd.DataFrame:
        return self._get_tushare_frame(
            "daily_info",
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            limit=limit,
            offset=offset,
            **filters,
        )

    def get_stk_limit_frame(
        self,
        ticker: str | None = None,
        trade_date: str | date | datetime | None = None,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> pd.DataFrame:
        return self._get_tushare_frame(
            "stk_limit",
            ticker=ticker,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            limit=limit,
            offset=offset,
            **filters,
        )

    def get_limit_list_d_frame(
        self,
        ticker: str | None = None,
        trade_date: str | date | datetime | None = None,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> pd.DataFrame:
        return self._get_tushare_frame(
            "limit_list_d",
            ticker=ticker,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            limit=limit,
            offset=offset,
            **filters,
        )

    def get_kpl_list_frame(
        self,
        ticker: str | None = None,
        trade_date: str | date | datetime | None = None,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> pd.DataFrame:
        return self._get_tushare_frame(
            "kpl_list",
            ticker=ticker,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            limit=limit,
            offset=offset,
            **filters,
        )

    def get_ths_index_frame(
        self,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> pd.DataFrame:
        return self._get_tushare_frame(
            "ths_index",
            fields=fields,
            limit=limit,
            offset=offset,
            **filters,
        )

    def get_ths_daily_frame(
        self,
        ts_code: str | None = None,
        trade_date: str | date | datetime | None = None,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> pd.DataFrame:
        params = dict(filters)
        if ts_code:
            params["ts_code"] = str(ts_code).strip().upper()
        return self._get_tushare_frame(
            "ths_daily",
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            limit=limit,
            offset=offset,
            **params,
        )

    def get_ths_member_frame(
        self,
        ts_code: str | None = None,
        ticker: str | None = None,
        trade_date: str | date | datetime | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> pd.DataFrame:
        params = dict(filters)
        if ts_code:
            params["ts_code"] = str(ts_code).strip().upper()
        return self._get_tushare_frame(
            "ths_member",
            ticker=ticker,
            trade_date=trade_date,
            fields=fields,
            limit=limit,
            offset=offset,
            **params,
        )

    def get_moneyflow_ind_ths_frame(
        self,
        ts_code: str | None = None,
        trade_date: str | date | datetime | None = None,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> pd.DataFrame:
        params = dict(filters)
        if ts_code:
            params["ts_code"] = str(ts_code).strip().upper()
        return self._get_tushare_frame(
            "moneyflow_ind_ths",
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            limit=limit,
            offset=offset,
            **params,
        )

    def get_moneyflow_ind_dc_frame(
        self,
        ts_code: str | None = None,
        trade_date: str | date | datetime | None = None,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> pd.DataFrame:
        params = dict(filters)
        if ts_code:
            params["ts_code"] = str(ts_code).strip().upper()
        return self._get_tushare_frame(
            "moneyflow_ind_dc",
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            limit=limit,
            offset=offset,
            **params,
        )

    def get_moneyflow_frame(
        self,
        ticker: str | None = None,
        trade_date: str | date | datetime | None = None,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> pd.DataFrame:
        return self._get_tushare_frame(
            "moneyflow",
            ticker=ticker,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            limit=limit,
            offset=offset,
            **filters,
        )

    def get_ths_hot_frame(
        self,
        ticker: str | None = None,
        trade_date: str | date | datetime | None = None,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> pd.DataFrame:
        return self._get_tushare_frame(
            "ths_hot",
            ticker=ticker,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            limit=limit,
            offset=offset,
            **filters,
        )

    def get_disclosure_date_frame(
        self,
        ticker: str | None = None,
        ts_code: str | None = None,
        end_date: str | date | datetime | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> pd.DataFrame:
        params = dict(filters)
        if ts_code:
            params["ts_code"] = str(ts_code).strip().upper()
        return self._get_tushare_frame(
            "disclosure_date",
            ticker=ticker,
            end_date=end_date,
            fields=fields,
            limit=limit,
            offset=offset,
            **params,
        )

    def get_stk_holdertrade_frame(
        self,
        ticker: str | None = None,
        ann_date: str | date | datetime | None = None,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> pd.DataFrame:
        params = dict(filters)
        if ann_date:
            params["ann_date"] = self._normalize_date_value(ann_date)
        return self._get_tushare_frame(
            "stk_holdertrade",
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            limit=limit,
            offset=offset,
            **params,
        )

    def get_share_float_frame(
        self,
        ticker: str | None = None,
        ann_date: str | date | datetime | None = None,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> pd.DataFrame:
        params = dict(filters)
        if ann_date:
            params["ann_date"] = self._normalize_date_value(ann_date)
        return self._get_tushare_frame(
            "share_float",
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            limit=limit,
            offset=offset,
            **params,
        )

    def get_top_list_frame(
        self,
        ticker: str | None = None,
        trade_date: str | date | datetime | None = None,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> pd.DataFrame:
        return self._get_tushare_frame(
            "top_list",
            ticker=ticker,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            limit=limit,
            offset=offset,
            **filters,
        )

    def get_top_inst_frame(
        self,
        ticker: str | None = None,
        trade_date: str | date | datetime | None = None,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> pd.DataFrame:
        return self._get_tushare_frame(
            "top_inst",
            ticker=ticker,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            limit=limit,
            offset=offset,
            **filters,
        )

    def get_forecast_vip_frame(
        self,
        ticker: str | None = None,
        ann_date: str | date | datetime | None = None,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> pd.DataFrame:
        params = dict(filters)
        if ann_date:
            params["ann_date"] = self._normalize_date_value(ann_date)
        return self._get_tushare_frame(
            "forecast_vip",
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            limit=limit,
            offset=offset,
            **params,
        )

    def get_express_vip_frame(
        self,
        ticker: str | None = None,
        ann_date: str | date | datetime | None = None,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> pd.DataFrame:
        params = dict(filters)
        if ann_date:
            params["ann_date"] = self._normalize_date_value(ann_date)
        return self._get_tushare_frame(
            "express_vip",
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            limit=limit,
            offset=offset,
            **params,
        )

    def get_tdx_index_frame(
        self,
        ts_code: str | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> pd.DataFrame:
        params = dict(filters)
        if ts_code:
            params["ts_code"] = str(ts_code).strip().upper()
        return self._get_tushare_frame(
            "tdx_index",
            fields=fields,
            limit=limit,
            offset=offset,
            **params,
        )

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

    def _get_tushare_frame(
        self,
        api_name: str,
        ticker: str | None = None,
        trade_date: str | date | datetime | None = None,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> pd.DataFrame:
        endpoint = getattr(self.pro, api_name, None)
        if endpoint is None:
            logger.warning("Unsupported Tushare endpoint: {}", api_name)
            return pd.DataFrame()

        params = {key: value for key, value in filters.items() if value is not None}
        if ticker:
            params["ts_code"] = self._normalize_source_ticker(ticker)
        if trade_date:
            params["trade_date"] = self._normalize_date_value(trade_date)
        if start_date:
            params["start_date"] = self._normalize_date_value(start_date)
        if end_date:
            params["end_date"] = self._normalize_date_value(end_date)
        if fields:
            params["fields"] = fields
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        try:
            frame = endpoint(**params)
        except Exception as exc:
            logger.warning(
                "Tushare endpoint failed: endpoint={endpoint}, err={err}",
                endpoint=api_name,
                err=str(exc),
            )
            return pd.DataFrame()

        if frame is None:
            return pd.DataFrame()
        if not isinstance(frame, pd.DataFrame):
            frame = pd.DataFrame(frame)
        return self._decorate_frame(frame.copy())

    def _normalize_source_ticker(self, ticker: str) -> str:
        normalized = str(ticker).strip().upper()
        if ":" in normalized:
            return self.convert_to_source_ticker(normalized)
        if normalized.endswith((".SH", ".SZ", ".BJ")):
            return normalized
        if normalized.isdigit() and len(normalized) == 6:
            if normalized.startswith("6"):
                return f"{normalized}.SH"
            if normalized.startswith(("0", "2", "3")):
                return f"{normalized}.SZ"
            return f"{normalized}.BJ"
        return normalized

    def _decorate_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        if "ts_code" in frame.columns and "ticker" not in frame.columns:
            frame["ticker"] = frame["ts_code"].map(self._safe_convert_to_internal_ticker)
        if "con_code" in frame.columns and "con_ticker" not in frame.columns:
            frame["con_ticker"] = frame["con_code"].map(
                self._safe_convert_to_internal_ticker
            )
        return frame

    def _safe_convert_to_internal_ticker(self, value: Any) -> str | None:
        text = str(value or "").strip().upper()
        if not text:
            return None
        try:
            return self.convert_to_internal_ticker(text)
        except ValueError:
            return text

    @staticmethod
    def _normalize_date_value(value: str | date | datetime) -> str:
        if isinstance(value, datetime):
            return value.strftime("%Y%m%d")
        if isinstance(value, date):
            return value.strftime("%Y%m%d")
        text = str(value).strip()
        if not text:
            return text
        return text.replace("-", "").replace("/", "")

    @staticmethod
    def _to_decimal(value: Any) -> Optional[Decimal]:
        if value in (None, ""):
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return None
