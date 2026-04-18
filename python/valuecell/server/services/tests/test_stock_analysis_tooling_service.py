from __future__ import annotations

from typing import Any, cast

from valuecell.server.services.assets.stock_analysis_tool_planner import (
    NEED_TOOLING_MODE,
    StockAnalysisToolPlannerResult,
)
from valuecell.server.services.assets.stock_analysis_external_tool_service import (
    StockAnalysisExternalToolResult,
)
from valuecell.server.services.assets.stock_analysis_tooling_service import (
    StockAnalysisToolingService,
)


class FakeHomepageContextService:
    def get_homepage_context(self, user_id: str) -> dict[str, Any]:
        return {
            "market_overview": {"market_state": "修复"},
            "emotion_cycle": {"cycle_stage": "分歧"},
            "risk_control": {"position_suggestion": "建议控制节奏。"},
        }


class FakeAssetService:
    def __init__(self, success: bool = True) -> None:
        self.success = success

    def get_historical_prices(self, **kwargs) -> dict[str, Any]:
        del kwargs
        if not self.success:
            return {"success": False, "error": "provider unavailable"}
        return {
            "success": True,
            "prices": [
                {"close_price": 10.0},
                {"close_price": 10.4},
                {"close_price": 10.8},
                {"close_price": 10.6},
                {"close_price": 11.0},
            ],
        }


class FakeExternalToolService:
    def __init__(self, available: bool = True) -> None:
        self.available = available

    def collect_external_evidence(self, **kwargs) -> StockAnalysisExternalToolResult:
        del kwargs
        if not self.available:
            return StockAnalysisExternalToolResult(
                unavailable_tools=[
                    {
                        "tool": "AShareDataProvider.get_recent_news",
                        "reason": "provider unavailable",
                    }
                ],
                evidence_generated_at="2026-04-18T10:00:00+00:00",
                evidence_staleness_hint="外部补数结果可能已过时。",
            )
        return StockAnalysisExternalToolResult(
            tool_calls=[
                {
                    "source": "AShareDataProvider.get_recent_news",
                    "layer": "external",
                    "reason": "补外部新闻摘要。",
                }
            ],
            tool_call_summaries=["AShareDataProvider.get_recent_news: 中际旭创外部新闻摘要"],
            temporary_evidence_blocks=[
                {
                    "evidence_id": "news:SZSE:300308",
                    "type": "recent_news",
                    "title": "中际旭创外部新闻摘要",
                    "summary": "中际旭创有两条外部新闻。",
                    "temporary": True,
                    "source_module": "external_news_evidence",
                    "source_label": "AShareDataProvider.get_recent_news",
                    "is_external": True,
                    "generated_at": "2026-04-18T10:00:00+00:00",
                    "data_time": "2026-04-18T09:30:00+00:00",
                    "staleness_hint": "新闻补数为短周期证据。",
                    "ticker_refs_json": ["SZSE:300308"],
                    "theme_refs_json": [],
                    "payload": {"items": [{"title": "新闻一"}]},
                }
            ],
            used_external_sources=["AShareDataProvider.get_recent_news"],
            evidence_generated_at="2026-04-18T10:00:00+00:00",
            evidence_staleness_hint="外部补数结果可能已过时。",
        )


def test_stock_analysis_tooling_service_prefers_internal_structured_sources() -> None:
    service = StockAnalysisToolingService(
        homepage_context_service=cast(Any, FakeHomepageContextService()),
        asset_service=cast(Any, FakeAssetService()),
        external_tool_service=cast(Any, FakeExternalToolService()),
    )

    result = service.collect_evidence(
        user_id="default_user",
        thread={"title": "市场问题"},
        context_cards=[],
        planner_result=StockAnalysisToolPlannerResult(
            mode=NEED_TOOLING_MODE,
            missing_context_hints=["latest_market_state"],
            tool_layers_to_use=["internal_structured"],
        ),
        ticker_refs=["SZSE:300308"],
        theme_refs=[],
    )

    assert result.answer_basis == "当前上下文 + 内部结构化补充"
    assert result.used_internal_sources == ["HomepageContextService"]
    assert result.temporary_evidence_blocks


def test_stock_analysis_tooling_service_market_price_gracefully_degrades_when_unavailable() -> None:
    service = StockAnalysisToolingService(
        asset_service=cast(Any, FakeAssetService(success=False)),
        external_tool_service=cast(Any, FakeExternalToolService(available=False)),
    )

    result = service.collect_evidence(
        user_id="default_user",
        thread={"title": "行情问题"},
        context_cards=[],
        planner_result=StockAnalysisToolPlannerResult(
            mode=NEED_TOOLING_MODE,
            missing_context_hints=["latest_price_action", "recent_news"],
            tool_layers_to_use=["market_price", "external_confirmation"],
        ),
        ticker_refs=["SZSE:300308"],
        theme_refs=[],
    )

    assert result.temporary_evidence_blocks == []
    assert result.unavailable_tools
    assert any(item["tool"] == "AssetService.get_historical_prices" for item in result.unavailable_tools)
    assert any(
        item["tool"] == "AShareDataProvider.get_recent_news" for item in result.unavailable_tools
    )


def test_stock_analysis_tooling_service_uses_external_provider_when_available() -> None:
    service = StockAnalysisToolingService(
        external_tool_service=cast(Any, FakeExternalToolService(available=True)),
    )

    result = service.collect_evidence(
        user_id="default_user",
        thread={"title": "新闻问题"},
        context_cards=[],
        planner_result=StockAnalysisToolPlannerResult(
            mode=NEED_TOOLING_MODE,
            missing_context_hints=["recent_news"],
            tool_layers_to_use=["external_confirmation"],
        ),
        ticker_refs=["SZSE:300308"],
        theme_refs=[],
    )

    assert result.answer_basis == "当前上下文 + 外部补充"
    assert result.used_external_sources == ["AShareDataProvider.get_recent_news"]
    assert result.temporary_evidence_blocks[0]["source_module"] == "external_news_evidence"
