from __future__ import annotations

from typing import Any, cast

from valuecell.server.services.assets.stock_analysis_external_tool_service import (
    StockAnalysisExternalToolService,
)


class FakeAShareProvider:
    def __init__(self, with_news: bool = True) -> None:
        self.with_news = with_news

    def get_recent_news(self, ticker: str, limit: int = 3) -> list[dict[str, Any]]:
        del limit
        if not self.with_news:
            return []
        return [
            {
                "title": f"{ticker} 新闻一",
                "published_at": "2026-04-18T09:30:00+00:00",
                "source": "Tavily",
            },
            {
                "title": f"{ticker} 新闻二",
                "published_at": "2026-04-18T08:00:00+00:00",
                "source": "Tavily",
            },
        ]


class FakeYFinanceAdapter:
    def __init__(self, available: bool = True) -> None:
        self.available = available

    def validate_ticker(self, ticker: str) -> bool:
        del ticker
        return self.available

    def get_historical_prices(self, ticker: str, **kwargs) -> dict[str, Any]:
        del ticker, kwargs
        if not self.available:
            return {"prices": []}
        return {
            "prices": [
                {"close_price": 10.0, "date": "2026-04-14"},
                {"close_price": 10.5, "date": "2026-04-15"},
                {"close_price": 10.8, "date": "2026-04-16"},
                {"close_price": 10.6, "date": "2026-04-17"},
                {"close_price": 11.0, "date": "2026-04-18"},
            ]
        }


class FakeShortCycleDataService:
    def __init__(self, available: bool = True) -> None:
        self.available = available

    def get_stock_observation_data(
        self,
        *,
        ticker: str,
        start_date: str,
        end_date: str,
    ) -> dict[str, Any]:
        del ticker, start_date, end_date
        if not self.available:
            return {"available": False}
        return {
            "available": True,
            "observation": {
                "items": [
                    {"trade_date": "2026-04-18", "close": 10.8},
                ]
            },
        }


def test_stock_analysis_external_tool_service_collects_news_and_external_confirmation() -> None:
    service = StockAnalysisExternalToolService(
        ashare_provider=cast(Any, FakeAShareProvider(with_news=True)),
        yfinance_adapter=cast(Any, FakeYFinanceAdapter(available=True)),
        short_cycle_data_service=cast(Any, FakeShortCycleDataService(available=True)),
    )

    result = service.collect_external_evidence(
        missing_context_hints=["recent_news", "recent_external_confirmation"],
        ticker_refs=["SZSE:300308"],
        theme_refs=["AI算力"],
    )

    assert result.used_external_sources
    assert result.provider_attempts
    assert result.provider_used
    assert "YFinanceAdapter" in result.provider_fallback_chain
    assert len(result.temporary_evidence_blocks) >= 2
    assert any(block["type"] == "recent_news" for block in result.temporary_evidence_blocks)
    assert any(
        block["type"] == "recent_external_confirmation"
        for block in result.temporary_evidence_blocks
    )


def test_stock_analysis_external_tool_service_gracefully_degrades_when_providers_unavailable() -> None:
    service = StockAnalysisExternalToolService(
        ashare_provider=cast(Any, FakeAShareProvider(with_news=False)),
        yfinance_adapter=cast(Any, FakeYFinanceAdapter(available=False)),
        short_cycle_data_service=cast(Any, FakeShortCycleDataService(available=False)),
    )

    result = service.collect_external_evidence(
        missing_context_hints=["recent_news", "recent_external_confirmation"],
        ticker_refs=["SZSE:300308"],
        theme_refs=[],
    )

    assert result.temporary_evidence_blocks == []
    assert result.unavailable_tools
    assert result.provider_attempts
    assert any(item["provider"] == "ShortCycleDataService" for item in result.provider_attempts)
    assert any(item["tool"] == "AShareDataProvider.get_recent_news" for item in result.unavailable_tools)
    assert any(item["tool"] == "external_confirmation_provider" for item in result.unavailable_tools)
