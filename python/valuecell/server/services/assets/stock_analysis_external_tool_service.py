from __future__ import annotations

import datetime as dt
from typing import Any, Optional, Sequence

from pydantic import BaseModel, Field

from valuecell.adapters.assets.ashare_provider import AShareDataProvider
from valuecell.adapters.assets.base import DataSource
from valuecell.adapters.assets.manager import get_adapter_manager
from valuecell.adapters.assets.yfinance_adapter import YFinanceAdapter

from .short_cycle_data_service import ShortCycleDataService


class StockAnalysisExternalToolResult(BaseModel):
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    tool_call_summaries: list[str] = Field(default_factory=list)
    temporary_evidence_blocks: list[dict[str, Any]] = Field(default_factory=list)
    unavailable_tools: list[dict[str, Any]] = Field(default_factory=list)
    used_external_sources: list[str] = Field(default_factory=list)
    evidence_generated_at: str | None = None
    evidence_staleness_hint: str | None = None


class StockAnalysisExternalToolService:
    def __init__(
        self,
        ashare_provider: Optional[AShareDataProvider] = None,
        short_cycle_data_service: Optional[ShortCycleDataService] = None,
        yfinance_adapter: Optional[YFinanceAdapter] = None,
    ) -> None:
        self.ashare_provider = ashare_provider or AShareDataProvider()
        self.short_cycle_data_service = short_cycle_data_service or ShortCycleDataService()
        self.yfinance_adapter = yfinance_adapter or self._resolve_yfinance_adapter()

    def collect_external_evidence(
        self,
        *,
        missing_context_hints: Sequence[str],
        ticker_refs: Sequence[str],
        theme_refs: Sequence[str],
    ) -> StockAnalysisExternalToolResult:
        result = StockAnalysisExternalToolResult(
            evidence_generated_at=self._now_iso(),
            evidence_staleness_hint="外部补数为当次研究的临时证据，可能随交易日或新闻流变化。",
        )
        hint_set = set(missing_context_hints)
        if "recent_news" in hint_set:
            self._collect_news(
                result=result,
                ticker_refs=ticker_refs,
                theme_refs=theme_refs,
            )
        if "recent_external_confirmation" in hint_set:
            self._collect_external_confirmation(
                result=result,
                ticker_refs=ticker_refs,
            )
        return result

    def _collect_news(
        self,
        *,
        result: StockAnalysisExternalToolResult,
        ticker_refs: Sequence[str],
        theme_refs: Sequence[str],
    ) -> None:
        if not ticker_refs and not theme_refs:
            result.unavailable_tools.append(
                {
                    "tool": "AShareDataProvider.get_recent_news",
                    "reason": "线程缺少 ticker 或 theme refs，无法发起新闻补数。",
                }
            )
            return
        summaries: list[str] = []
        news_blocks: list[dict[str, Any]] = []
        for ticker in list(ticker_refs)[:2]:
            try:
                items = list(self.ashare_provider.get_recent_news(ticker, limit=3) or [])
            except Exception as exc:  # pragma: no cover - defensive
                result.unavailable_tools.append(
                    {
                        "tool": "AShareDataProvider.get_recent_news",
                        "ticker": ticker,
                        "reason": f"新闻 provider 异常: {exc}",
                    }
                )
                continue
            if not items:
                result.unavailable_tools.append(
                    {
                        "tool": "AShareDataProvider.get_recent_news",
                        "ticker": ticker,
                        "reason": "未返回可用新闻摘要。",
                    }
                )
                continue
            top_items = items[:2]
            summary = "；".join(
                f"{str(item.get('title') or '').strip()} ({str(item.get('published_at') or '').strip() or '时间未知'})"
                for item in top_items
                if str(item.get("title") or "").strip()
            )
            if not summary:
                continue
            summaries.append(f"{ticker}: {summary}")
            news_blocks.append(
                {
                    "evidence_id": f"news:{ticker}",
                    "type": "recent_news",
                    "title": f"{ticker} 外部新闻摘要",
                    "summary": summary,
                    "temporary": True,
                    "payload": {"items": top_items},
                    "source_module": "external_news_evidence",
                    "source_label": "AShareDataProvider.get_recent_news",
                    "is_external": True,
                    "generated_at": result.evidence_generated_at,
                    "data_time": str(top_items[0].get("published_at") or result.evidence_generated_at),
                    "staleness_hint": "新闻摘要偏短周期证据，需结合显式上下文核对。",
                    "ticker_refs_json": [ticker],
                    "theme_refs_json": list(theme_refs)[:2],
                }
            )
        if news_blocks:
            self._append_result(
                result=result,
                source="AShareDataProvider.get_recent_news",
                summary="；".join(summaries),
                blocks=news_blocks,
            )

    def _collect_external_confirmation(
        self,
        *,
        result: StockAnalysisExternalToolResult,
        ticker_refs: Sequence[str],
    ) -> None:
        if not ticker_refs:
            result.unavailable_tools.append(
                {
                    "tool": "external_confirmation_provider",
                    "reason": "线程缺少 ticker refs，无法执行外部确认。",
                }
            )
            return
        summaries: list[str] = []
        confirmation_blocks: list[dict[str, Any]] = []
        for ticker in list(ticker_refs)[:2]:
            confirmation = self._fetch_yfinance_confirmation(
                ticker=ticker,
                generated_at=result.evidence_generated_at,
            )
            if confirmation is None:
                confirmation = self._fetch_short_cycle_confirmation(
                    ticker=ticker,
                    generated_at=result.evidence_generated_at,
                )
            if confirmation is None:
                result.unavailable_tools.append(
                    {
                        "tool": "external_confirmation_provider",
                        "ticker": ticker,
                        "reason": "YFinance 与短周期外部确认均未返回可用结果。",
                    }
                )
                continue
            summaries.append(confirmation["summary"])
            confirmation_blocks.append(confirmation)
        if confirmation_blocks:
            self._append_result(
                result=result,
                source="external_confirmation_provider",
                summary="；".join(summaries),
                blocks=confirmation_blocks,
            )

    def _fetch_yfinance_confirmation(
        self,
        *,
        ticker: str,
        generated_at: str | None,
    ) -> dict[str, Any] | None:
        adapter = self.yfinance_adapter
        if adapter is None:
            return None
        if hasattr(adapter, "validate_ticker") and not adapter.validate_ticker(ticker):
            return None
        end_date = dt.datetime.now()
        start_date = end_date - dt.timedelta(days=10)
        try:
            historical = adapter.get_historical_prices(
                ticker,
                start_date=start_date,
                end_date=end_date,
                interval="1d",
            )
        except Exception:  # pragma: no cover - defensive
            return None
        prices = list(historical.get("prices") or []) if isinstance(historical, dict) else []
        if len(prices) < 2:
            return None
        recent = prices[-5:]
        first_close = float(recent[0].get("close_price") or recent[0].get("price") or 0)
        last_close = float(recent[-1].get("close_price") or recent[-1].get("price") or 0)
        if first_close <= 0:
            return None
        pct_change = ((last_close - first_close) / first_close) * 100
        summary = (
            f"{ticker} 外部确认近 5 个交易日约 {pct_change:+.2f}% ，最新收盘约 {last_close:.2f}。"
        )
        return {
            "evidence_id": f"external_confirmation:yfinance:{ticker}",
            "type": "recent_external_confirmation",
            "title": f"{ticker} 外部行情确认",
            "summary": summary,
            "temporary": True,
            "payload": {"recent_prices": recent},
            "source_module": "external_confirmation_evidence",
            "source_label": "YFinanceAdapter",
            "is_external": True,
            "generated_at": generated_at,
            "data_time": str(
                recent[-1].get("timestamp")
                or recent[-1].get("date")
                or generated_at
            ),
            "staleness_hint": "外部行情确认偏日级，盘中状态可能继续变化。",
            "ticker_refs_json": [ticker],
            "theme_refs_json": [],
        }

    def _fetch_short_cycle_confirmation(
        self,
        *,
        ticker: str,
        generated_at: str | None,
    ) -> dict[str, Any] | None:
        end_date = dt.date.today()
        start_date = end_date - dt.timedelta(days=7)
        try:
            bundle = self.short_cycle_data_service.get_stock_observation_data(
                ticker=ticker,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )
        except Exception:  # pragma: no cover - defensive
            return None
        if not bundle.get("available"):
            return None
        observation = bundle.get("observation") or {}
        rows = list(observation.get("items") or [])
        if not rows:
            return None
        latest = rows[-1]
        summary = (
            f"{ticker} 短周期外部确认最新日期 {latest.get('trade_date') or '未知'}，"
            f"收盘 {latest.get('close') or latest.get('close_price') or '未知'}。"
        )
        return {
            "evidence_id": f"external_confirmation:short_cycle:{ticker}",
            "type": "recent_external_confirmation",
            "title": f"{ticker} 短周期外部确认",
            "summary": summary,
            "temporary": True,
            "payload": {"latest": latest, "count": len(rows)},
            "source_module": "external_confirmation_evidence",
            "source_label": "ShortCycleDataService",
            "is_external": True,
            "generated_at": generated_at,
            "data_time": str(latest.get("trade_date") or generated_at),
            "staleness_hint": "短周期确认以最近交易日为准，需关注是否已跨日。",
            "ticker_refs_json": [ticker],
            "theme_refs_json": [],
        }

    @staticmethod
    def _append_result(
        *,
        result: StockAnalysisExternalToolResult,
        source: str,
        summary: str,
        blocks: Sequence[dict[str, Any]],
    ) -> None:
        result.tool_calls.append(
            {
                "source": source,
                "layer": "external",
                "reason": summary,
            }
        )
        result.tool_call_summaries.append(f"{source}: {summary}")
        result.temporary_evidence_blocks.extend(blocks)
        if source not in result.used_external_sources:
            result.used_external_sources.append(source)

    @staticmethod
    def _resolve_yfinance_adapter() -> YFinanceAdapter | None:
        manager = get_adapter_manager()
        raw_adapter = manager.adapters.get(DataSource.YFINANCE)
        return raw_adapter if isinstance(raw_adapter, YFinanceAdapter) else None

    @staticmethod
    def _now_iso() -> str:
        return dt.datetime.now(dt.UTC).isoformat()


_stock_analysis_external_tool_service: StockAnalysisExternalToolService | None = None


def get_stock_analysis_external_tool_service() -> StockAnalysisExternalToolService:
    global _stock_analysis_external_tool_service
    if _stock_analysis_external_tool_service is None:
        _stock_analysis_external_tool_service = StockAnalysisExternalToolService()
    return _stock_analysis_external_tool_service


def reset_stock_analysis_external_tool_service() -> None:
    global _stock_analysis_external_tool_service
    _stock_analysis_external_tool_service = None
