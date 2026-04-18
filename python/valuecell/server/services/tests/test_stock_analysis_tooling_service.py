from __future__ import annotations

from typing import Any, cast

from valuecell.server.services.assets.stock_analysis_tool_planner import (
    NEED_TOOLING_MODE,
    StockAnalysisToolPlannerResult,
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


def test_stock_analysis_tooling_service_prefers_internal_structured_sources() -> None:
    service = StockAnalysisToolingService(
        homepage_context_service=cast(Any, FakeHomepageContextService()),
        asset_service=cast(Any, FakeAssetService()),
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
    assert any(item["tool"] == "external_news_provider" for item in result.unavailable_tools)
