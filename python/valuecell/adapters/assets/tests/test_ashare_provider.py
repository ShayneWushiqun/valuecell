from datetime import datetime
from decimal import Decimal

from valuecell.adapters.assets.ashare_provider import (
    AShareDataProvider,
    is_ashare_ticker,
    normalize_ashare_ticker,
    to_plain_symbol,
    to_prefixed_symbol,
)
from valuecell.adapters.assets.types import AssetPrice, DataSource


def test_ashare_ticker_helpers() -> None:
    assert is_ashare_ticker("SSE:600519")
    assert is_ashare_ticker("SZSE:000001")
    assert is_ashare_ticker("600519.SH")
    assert is_ashare_ticker("000001")
    assert not is_ashare_ticker("BTC-USDT")
    assert to_plain_symbol("SZSE:000001") == "000001"
    assert normalize_ashare_ticker("600519.SH") == "SSE:600519"
    assert normalize_ashare_ticker("000001") == "SZSE:000001"
    assert to_prefixed_symbol("SSE:600519") == "sh600519"


def test_ashare_provider_realtime_fallback(monkeypatch) -> None:
    provider = AShareDataProvider(provider_order=["tushare", "akshare"])

    def fail_provider(provider_name: str, ticker: str):
        if provider_name == "tushare":
            raise RuntimeError("tushare unavailable")
        return AssetPrice(
            ticker=ticker,
            price=Decimal("10.5"),
            currency="CNY",
            timestamp=datetime(2026, 4, 6, 10, 0, 0),
            close_price=Decimal("10.5"),
            source=DataSource.AKSHARE,
        )

    monkeypatch.setattr(provider, "_get_real_time_price_from_provider", fail_provider)

    price = provider.get_real_time_price("SZSE:000001")

    assert price is not None
    assert price.price == Decimal("10.5")
    assert price.source == DataSource.AKSHARE
