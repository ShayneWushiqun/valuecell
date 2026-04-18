from __future__ import annotations

import datetime as dt
from typing import Any, Optional, Sequence

from pydantic import BaseModel, Field

from .asset_service import AssetService
from .decision_alert_persistence_service import DecisionAlertPersistenceService
from .decision_context_window_service import DecisionContextWindowService
from .decision_effectiveness_service import DecisionEffectivenessService
from .decision_outcome_review_service import DecisionOutcomeReviewService
from .exit_risk_center_service import ExitRiskCenterService
from .holding_lifecycle_service import HoldingLifecycleService
from .homepage_context_service import HomepageContextService
from .opportunity_pool_service import OpportunityPoolService
from .risk_sizing_service import RiskSizingService
from .stock_analysis_external_tool_service import (
    StockAnalysisExternalToolService,
    get_stock_analysis_external_tool_service,
)
from .stock_analysis_tool_planner import (
    EXTERNAL_TOOL_LAYER,
    INTERNAL_TOOL_LAYER,
    MARKET_TOOL_LAYER,
    StockAnalysisToolPlannerResult,
)
from .theme_radar_service import ThemeRadarService
from .watchlist_center_service import WatchlistCenterService


class StockAnalysisToolingResult(BaseModel):
    answer_basis: str = "当前上下文"
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    tool_call_summaries: list[str] = Field(default_factory=list)
    temporary_evidence_blocks: list[dict[str, Any]] = Field(default_factory=list)
    evidence_summary: str | None = None
    unavailable_tools: list[dict[str, Any]] = Field(default_factory=list)
    used_internal_sources: list[str] = Field(default_factory=list)
    used_external_sources: list[str] = Field(default_factory=list)
    evidence_generated_at: str | None = None
    evidence_staleness_hint: str | None = None


class StockAnalysisToolingService:
    def __init__(
        self,
        decision_context_window_service: Optional[DecisionContextWindowService] = None,
        decision_outcome_review_service: Optional[DecisionOutcomeReviewService] = None,
        decision_effectiveness_service: Optional[DecisionEffectivenessService] = None,
        risk_sizing_service: Optional[RiskSizingService] = None,
        holding_lifecycle_service: Optional[HoldingLifecycleService] = None,
        exit_risk_center_service: Optional[ExitRiskCenterService] = None,
        homepage_context_service: Optional[HomepageContextService] = None,
        opportunity_pool_service: Optional[OpportunityPoolService] = None,
        theme_radar_service: Optional[ThemeRadarService] = None,
        watchlist_center_service: Optional[WatchlistCenterService] = None,
        decision_alert_persistence_service: Optional[DecisionAlertPersistenceService] = None,
        asset_service: Optional[AssetService] = None,
        external_tool_service: Optional[StockAnalysisExternalToolService] = None,
    ) -> None:
        self.decision_context_window_service = (
            decision_context_window_service or DecisionContextWindowService()
        )
        self.decision_outcome_review_service = (
            decision_outcome_review_service or DecisionOutcomeReviewService()
        )
        self.decision_effectiveness_service = (
            decision_effectiveness_service or DecisionEffectivenessService()
        )
        self.risk_sizing_service = risk_sizing_service or RiskSizingService()
        self.holding_lifecycle_service = (
            holding_lifecycle_service or HoldingLifecycleService()
        )
        self.exit_risk_center_service = (
            exit_risk_center_service or ExitRiskCenterService()
        )
        self.homepage_context_service = homepage_context_service or HomepageContextService()
        self.opportunity_pool_service = (
            opportunity_pool_service or OpportunityPoolService()
        )
        self.theme_radar_service = theme_radar_service or ThemeRadarService()
        self.watchlist_center_service = (
            watchlist_center_service or WatchlistCenterService()
        )
        self.decision_alert_persistence_service = (
            decision_alert_persistence_service or DecisionAlertPersistenceService()
        )
        self.asset_service = asset_service or AssetService()
        self.external_tool_service = (
            external_tool_service or get_stock_analysis_external_tool_service()
        )

    def collect_evidence(
        self,
        *,
        user_id: str,
        thread: dict[str, Any],
        context_cards: Sequence[dict[str, Any]],
        planner_result: StockAnalysisToolPlannerResult,
        ticker_refs: Sequence[str],
        theme_refs: Sequence[str],
    ) -> StockAnalysisToolingResult:
        del context_cards
        result = StockAnalysisToolingResult(
            evidence_generated_at=dt.datetime.now(dt.UTC).isoformat(),
            evidence_staleness_hint="临时证据仅用于本轮回答，可能已随交易日变化。",
        )
        if planner_result.mode == "context_only":
            return result

        if INTERNAL_TOOL_LAYER in planner_result.tool_layers_to_use:
            self._collect_internal_sources(
                result=result,
                user_id=user_id,
                planner_result=planner_result,
                ticker_refs=ticker_refs,
                theme_refs=theme_refs,
            )
        if MARKET_TOOL_LAYER in planner_result.tool_layers_to_use:
            self._collect_market_sources(
                result=result,
                planner_result=planner_result,
                ticker_refs=ticker_refs,
            )
        if EXTERNAL_TOOL_LAYER in planner_result.tool_layers_to_use:
            self._collect_external_sources(
                result=result,
                planner_result=planner_result,
                ticker_refs=ticker_refs,
                theme_refs=theme_refs,
            )
        result.answer_basis = self._build_answer_basis(result=result)
        result.evidence_summary = self._build_evidence_summary(
            thread=thread,
            result=result,
        )
        return result

    def _collect_internal_sources(
        self,
        *,
        result: StockAnalysisToolingResult,
        user_id: str,
        planner_result: StockAnalysisToolPlannerResult,
        ticker_refs: Sequence[str],
        theme_refs: Sequence[str],
    ) -> None:
        hints = set(planner_result.missing_context_hints)
        if "latest_market_state" in hints:
            homepage_context = self.homepage_context_service.get_homepage_context(user_id)
            summary = self._summarize_homepage_context(homepage_context)
            self._append_tool_result(
                result=result,
                source="HomepageContextService",
                layer="internal",
                reason="补最新市场状态与情绪框架。",
                summary=summary,
                block={
                    "type": "market_state",
                    "title": "市场状态补充",
                    "summary": summary,
                    "payload": {
                        "market_overview": homepage_context.get("market_overview"),
                        "emotion_cycle": homepage_context.get("emotion_cycle"),
                        "risk_control": homepage_context.get("risk_control"),
                    },
                    "temporary": True,
                    "source_module": "tooling_evidence",
                    "ticker_refs_json": [],
                    "theme_refs_json": [],
                    "data_time": result.evidence_generated_at,
                    "staleness_hint": "市场状态按日级更新，盘中可能继续变化。",
                },
            )
        if "latest_theme_status" in hints and theme_refs:
            overview = self.theme_radar_service.get_overview(user_id)
            items = list(overview.get("items") or [])
            matched = [
                item
                for item in items
                if str(item.get("theme_name") or "") in theme_refs
                or str(item.get("theme_code") or "") in theme_refs
            ][:3]
            if matched:
                summary = "；".join(
                    f"{item.get('theme_name')}: {item.get('theme_state')}，{item.get('participation_hint')}"
                    for item in matched
                )
                self._append_tool_result(
                    result=result,
                    source="ThemeRadarService",
                    layer="internal",
                    reason="补线程涉及题材的最新状态。",
                    summary=summary,
                    block={
                        "type": "theme_status",
                        "title": "题材状态补充",
                        "summary": summary,
                        "payload": {"items": matched},
                        "temporary": True,
                        "source_module": "tooling_evidence",
                        "ticker_refs_json": [],
                        "theme_refs_json": list(theme_refs)[:3],
                        "data_time": result.evidence_generated_at,
                        "staleness_hint": "题材状态偏短周期，建议结合最新盘面观察。",
                    },
                )
        if "latest_holding_risk" in hints:
            lifecycle = self.holding_lifecycle_service.get_overview(user_id)
            exit_risk = self.exit_risk_center_service.get_overview(user_id)
            lifecycle_items = self._filter_items_by_ticker(
                lifecycle.get("items") or [],
                ticker_refs,
            )[:3]
            risk_items = self._merge_exit_risk_groups(exit_risk)
            risk_matched = self._filter_items_by_ticker(risk_items, ticker_refs)[:3]
            summary = self._summarize_holding_risk(
                lifecycle_items=lifecycle_items,
                risk_items=risk_matched,
            )
            self._append_tool_result(
                result=result,
                source="HoldingLifecycleService+ExitRiskCenterService",
                layer="internal",
                reason="补持仓周期与卖点风险边界。",
                summary=summary,
                block={
                    "type": "holding_risk",
                    "title": "持仓风险补充",
                    "summary": summary,
                    "payload": {
                        "lifecycle_items": lifecycle_items,
                        "risk_items": risk_matched,
                    },
                    "temporary": True,
                        "source_module": "tooling_evidence",
                        "ticker_refs_json": list(ticker_refs)[:3],
                        "theme_refs_json": [],
                        "data_time": result.evidence_generated_at,
                        "staleness_hint": "持仓风险结论会随价格和提醒变化而调整。",
                },
            )
        if "latest_alert_change" in hints:
            alerts = self.decision_alert_persistence_service.list_alerts(
                user_id=user_id,
                status="all",
                limit=20,
            )
            alert_items = self._filter_items_by_ticker(alerts.get("items") or [], ticker_refs)[:4]
            summary = self._summarize_alerts(alert_items)
            self._append_tool_result(
                result=result,
                source="DecisionAlertPersistenceService",
                layer="internal",
                reason="补当前 active alerts 与最近提醒变化。",
                summary=summary,
                block={
                    "type": "alert_change",
                    "title": "提醒变化补充",
                    "summary": summary,
                    "payload": {"items": alert_items, "unread_count": alerts.get("unread_count")},
                    "temporary": True,
                        "source_module": "tooling_evidence",
                        "ticker_refs_json": list(ticker_refs)[:4],
                        "theme_refs_json": [],
                        "data_time": result.evidence_generated_at,
                        "staleness_hint": "提醒变化通常以当日有效为主。",
                },
            )
        if "insufficient_comparison_basis" in hints:
            context_windows = self.decision_context_window_service.list_windows(
                user_id=user_id,
                limit=20,
            )
            reviews = self.decision_outcome_review_service.list_reviews(
                user_id=user_id,
                limit=12,
            )
            effectiveness = self.decision_effectiveness_service.get_summary(user_id=user_id)
            risk_sizing = self.risk_sizing_service.get_summary(user_id=user_id)
            summary = self._summarize_comparison_basis(
                windows=context_windows.get("items") or [],
                reviews=reviews.get("items") or [],
                effectiveness=effectiveness,
                risk_sizing=risk_sizing,
                ticker_refs=ticker_refs,
            )
            self._append_tool_result(
                result=result,
                source="DecisionContextWindowService+DecisionOutcomeReviewService+DecisionEffectivenessService+RiskSizingService",
                layer="internal",
                reason="补结构化研究对象，增强多标的比较依据。",
                summary=summary,
                block={
                    "type": "comparison_basis",
                    "title": "比较依据补充",
                    "summary": summary,
                    "payload": {
                        "window_items": self._filter_items_by_ticker(
                            context_windows.get("items") or [],
                            ticker_refs,
                        )[:3],
                        "review_items": self._filter_items_by_ticker(
                            reviews.get("items") or [],
                            ticker_refs,
                        )[:3],
                        "effectiveness": {
                            "overall_summary": effectiveness.get("overall_summary"),
                            "overall_score": effectiveness.get("overall_score"),
                        },
                        "risk_sizing": {
                            "market_risk_level": risk_sizing.get("market_risk_level"),
                            "suggested_total_exposure_range": risk_sizing.get(
                                "suggested_total_exposure_range"
                            ),
                        },
                    },
                    "temporary": True,
                    "source_module": "tooling_evidence",
                    "ticker_refs_json": list(ticker_refs)[:3],
                    "theme_refs_json": [],
                    "data_time": result.evidence_generated_at,
                    "staleness_hint": "比较依据包含历史复盘与当前摘要，需区分时点。",
                },
            )
        if not result.tool_calls:
            watchlist = self.watchlist_center_service.get_overview(user_id)
            opportunities = self.opportunity_pool_service.get_opportunity_candidates(user_id)
            summary = self._summarize_fallback_internal(
                watchlist_items=self._filter_items_by_ticker(
                    watchlist.get("items") or [],
                    ticker_refs,
                )[:2],
                opportunity_items=self._filter_items_by_ticker(
                    opportunities.get("items") or [],
                    ticker_refs,
                )[:2],
            )
            self._append_tool_result(
                result=result,
                source="WatchlistCenterService+OpportunityPoolService",
                layer="internal",
                reason="补线程相关的观察池与机会池结构化状态。",
                summary=summary,
                block={
                    "type": "structured_fallback",
                    "title": "结构化补充",
                    "summary": summary,
                    "payload": {
                        "watchlist_items": self._filter_items_by_ticker(
                            watchlist.get("items") or [],
                            ticker_refs,
                        )[:2],
                        "opportunity_items": self._filter_items_by_ticker(
                            opportunities.get("items") or [],
                            ticker_refs,
                        )[:2],
                    },
                    "temporary": True,
                    "source_module": "tooling_evidence",
                    "ticker_refs_json": list(ticker_refs)[:2],
                    "theme_refs_json": [],
                    "data_time": result.evidence_generated_at,
                    "staleness_hint": "观察池和机会池状态为短周期参考。",
                },
            )

    def _collect_market_sources(
        self,
        *,
        result: StockAnalysisToolingResult,
        planner_result: StockAnalysisToolPlannerResult,
        ticker_refs: Sequence[str],
    ) -> None:
        if not ticker_refs:
            result.unavailable_tools.append(
                {
                    "tool": "AssetService.get_historical_prices",
                    "reason": "线程缺少 ticker refs，无法执行日线价格确认。",
                }
            )
            return
        end_date = dt.datetime.now()
        start_date = end_date - dt.timedelta(days=30)
        summaries: list[str] = []
        blocks: list[dict[str, Any]] = []
        for ticker in list(ticker_refs)[:3]:
            response = self.asset_service.get_historical_prices(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                interval="1d",
            )
            if not response.get("success"):
                result.unavailable_tools.append(
                    {
                        "tool": "AssetService.get_historical_prices",
                        "ticker": ticker,
                        "reason": response.get("error") or "行情数据暂不可用。",
                    }
                )
                continue
            prices = list(response.get("prices") or [])
            if len(prices) < 2:
                result.unavailable_tools.append(
                    {
                        "tool": "AssetService.get_historical_prices",
                        "ticker": ticker,
                        "reason": "历史价格点不足，无法做阶段确认。",
                    }
                )
                continue
            recent = prices[-5:]
            first_close = float(recent[0].get("close_price") or recent[0].get("price") or 0)
            last_close = float(recent[-1].get("close_price") or recent[-1].get("price") or 0)
            if first_close <= 0:
                continue
            pct_change = ((last_close - first_close) / first_close) * 100
            summary = (
                f"{ticker} 最近 5 个交易日约 {pct_change:+.2f}% ，"
                f"最新收盘约 {last_close:.2f}。"
            )
            summaries.append(summary)
            blocks.append(
                {
                    "type": "latest_price_action",
                    "title": f"{ticker} 日线价格补充",
                    "summary": summary,
                    "payload": {
                        "ticker": ticker,
                        "recent_prices": recent,
                    },
                    "temporary": True,
                    "source_module": "tooling_evidence",
                    "ticker_refs_json": [ticker],
                    "theme_refs_json": [],
                    "data_time": str(
                        recent[-1].get("timestamp")
                        or recent[-1].get("date")
                        or result.evidence_generated_at
                    ),
                    "staleness_hint": "日线价格补充按最近交易日确认，盘中状态可能不同。",
                }
            )
        if summaries:
            self._append_tool_result(
                result=result,
                source="AssetService.get_historical_prices",
                layer="market",
                reason="补最近日线行情，确认价格动作和波动节奏。",
                summary="；".join(summaries),
                block={
                    "type": "market_price_bundle",
                    "title": "行情补充",
                    "summary": "；".join(summaries),
                    "payload": {"items": blocks},
                    "temporary": True,
                    "source_module": "tooling_evidence",
                    "ticker_refs_json": list(ticker_refs)[:3],
                    "theme_refs_json": [],
                    "data_time": result.evidence_generated_at,
                    "staleness_hint": "行情补充偏日级确认，需留意是否已跨交易日。",
                },
            )
        elif "latest_price_action" in planner_result.missing_context_hints:
            result.unavailable_tools.append(
                {
                    "tool": "AssetService.get_historical_prices",
                    "reason": "当前日线价格补充未返回可用结果。",
                }
            )

    def _collect_external_sources(
        self,
        *,
        result: StockAnalysisToolingResult,
        planner_result: StockAnalysisToolPlannerResult,
        ticker_refs: Sequence[str],
        theme_refs: Sequence[str],
    ) -> None:
        external_result = self.external_tool_service.collect_external_evidence(
            missing_context_hints=planner_result.missing_context_hints,
            ticker_refs=ticker_refs,
            theme_refs=theme_refs,
        )
        result.tool_calls.extend(external_result.tool_calls)
        result.tool_call_summaries.extend(external_result.tool_call_summaries)
        result.temporary_evidence_blocks.extend(external_result.temporary_evidence_blocks)
        result.unavailable_tools.extend(external_result.unavailable_tools)
        for source in external_result.used_external_sources:
            if source not in result.used_external_sources:
                result.used_external_sources.append(source)
        if external_result.evidence_generated_at:
            result.evidence_generated_at = external_result.evidence_generated_at
        if external_result.evidence_staleness_hint:
            result.evidence_staleness_hint = external_result.evidence_staleness_hint

    @staticmethod
    def _append_tool_result(
        *,
        result: StockAnalysisToolingResult,
        source: str,
        layer: str,
        reason: str,
        summary: str,
        block: dict[str, Any],
    ) -> None:
        result.tool_calls.append(
            {
                "source": source,
                "layer": layer,
                "reason": reason,
            }
        )
        result.tool_call_summaries.append(f"{source}: {summary}")
        normalized_block = {
            "evidence_id": block.get("evidence_id")
            or f"evidence_{len(result.temporary_evidence_blocks)}",
            "type": block.get("type") or "tooling_evidence",
            "title": block.get("title") or source,
            "summary": block.get("summary") or summary,
            "temporary": bool(block.get("temporary", True)),
            "payload": block.get("payload") or {},
            "source_module": block.get("source_module") or "tooling_evidence",
            "source_label": block.get("source_label") or source,
            "is_external": bool(block.get("is_external", layer == "external")),
            "generated_at": block.get("generated_at") or result.evidence_generated_at,
            "data_time": block.get("data_time") or result.evidence_generated_at,
            "staleness_hint": block.get("staleness_hint")
            or result.evidence_staleness_hint
            or "临时证据可能已过时，请结合当前显式上下文判断。",
            "ticker_refs_json": list(block.get("ticker_refs_json") or []),
            "theme_refs_json": list(block.get("theme_refs_json") or []),
        }
        result.temporary_evidence_blocks.append(normalized_block)
        if layer == "internal":
            if source not in result.used_internal_sources:
                result.used_internal_sources.append(source)
        if layer == "external":
            if source not in result.used_external_sources:
                result.used_external_sources.append(source)

    @staticmethod
    def _build_answer_basis(*, result: StockAnalysisToolingResult) -> str:
        if result.used_external_sources:
            return "当前上下文 + 外部补充"
        if any(call.get("layer") == "market" for call in result.tool_calls):
            return "当前上下文 + 行情补充"
        if result.tool_calls:
            return "当前上下文 + 内部结构化补充"
        return "当前上下文"

    @staticmethod
    def _build_evidence_summary(
        *,
        thread: dict[str, Any],
        result: StockAnalysisToolingResult,
    ) -> str | None:
        if not result.tool_call_summaries and not result.unavailable_tools:
            return None
        parts = [f"线程 {thread.get('title') or '未命名线程'} 本轮按需补了临时证据。"]
        if result.tool_call_summaries:
            parts.append("已补数据：" + "；".join(result.tool_call_summaries[:4]))
        if result.unavailable_tools:
            parts.append(
                "不可用工具："
                + "；".join(
                    f"{item.get('tool')}: {item.get('reason')}" for item in result.unavailable_tools[:3]
                )
            )
        parts.append("这些证据仅用于本轮回答，未自动保存为长期上下文。")
        return " ".join(parts)

    @staticmethod
    def _filter_items_by_ticker(
        items: Sequence[dict[str, Any]],
        ticker_refs: Sequence[str],
    ) -> list[dict[str, Any]]:
        if not ticker_refs:
            return list(items)
        ticker_set = {str(item) for item in ticker_refs}
        return [
            item
            for item in items
            if str(item.get("ticker") or "") in ticker_set
            or any(str(ref or "") in ticker_set for ref in list(item.get("ticker_refs_json") or []))
        ]

    @staticmethod
    def _merge_exit_risk_groups(overview: dict[str, Any]) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        for key in (
            "high_priority_items",
            "profit_protection_items",
            "discipline_stop_items",
            "watch_items",
        ):
            merged.extend(list(overview.get(key) or []))
        return merged

    @staticmethod
    def _summarize_homepage_context(homepage_context: dict[str, Any]) -> str:
        market_overview = homepage_context.get("market_overview") or {}
        emotion_cycle = homepage_context.get("emotion_cycle") or {}
        risk_control = homepage_context.get("risk_control") or {}
        return (
            f"市场概览：{market_overview.get('market_state') or '待确认'}；"
            f"情绪阶段：{emotion_cycle.get('cycle_stage') or '待确认'}；"
            f"风险控制：{risk_control.get('position_suggestion') or '暂无建议'}"
        )

    @staticmethod
    def _summarize_holding_risk(
        *,
        lifecycle_items: Sequence[dict[str, Any]],
        risk_items: Sequence[dict[str, Any]],
    ) -> str:
        parts: list[str] = []
        for item in lifecycle_items[:2]:
            parts.append(
                f"{item.get('display_name') or item.get('ticker')}: {item.get('lifecycle_stage')} / {item.get('action')}"
            )
        for item in risk_items[:2]:
            parts.append(
                f"{item.get('ticker')}: {item.get('risk_type') or item.get('action')} / {item.get('liquidity_warning') or '无额外流动性提示'}"
            )
        return "；".join(parts) or "当前未找到更细的持仓风险补充。"

    @staticmethod
    def _summarize_alerts(alert_items: Sequence[dict[str, Any]]) -> str:
        if not alert_items:
            return "当前没有匹配线程 ticker 的提醒变化。"
        return "；".join(
            f"{item.get('display_name') or item.get('ticker')}: {item.get('alert_type')} / {item.get('next_action') or item.get('body')}"
            for item in alert_items[:3]
        )

    @staticmethod
    def _summarize_comparison_basis(
        *,
        windows: Sequence[dict[str, Any]],
        reviews: Sequence[dict[str, Any]],
        effectiveness: dict[str, Any],
        risk_sizing: dict[str, Any],
        ticker_refs: Sequence[str],
    ) -> str:
        parts: list[str] = []
        if ticker_refs:
            parts.append(f"线程当前 ticker 数量 {len(ticker_refs)}。")
        if windows:
            parts.append(f"可补 {min(len(windows), 3)} 条决策时间窗。")
        if reviews:
            parts.append(f"可补 {min(len(reviews), 3)} 条结果回看。")
        if effectiveness.get("available"):
            parts.append(
                f"近期有效性得分 {effectiveness.get('overall_score')}。"
            )
        if risk_sizing.get("available"):
            parts.append(
                f"当前组合风险 {risk_sizing.get('market_risk_level')}，总仓位建议 {risk_sizing.get('suggested_total_exposure_range')}。"
            )
        return " ".join(parts) or "当前缺少足够的可比较结构化对象。"

    @staticmethod
    def _summarize_fallback_internal(
        *,
        watchlist_items: Sequence[dict[str, Any]],
        opportunity_items: Sequence[dict[str, Any]],
    ) -> str:
        parts: list[str] = []
        if watchlist_items:
            parts.append(
                "观察池："
                + "；".join(
                    f"{item.get('display_name')}: {item.get('status') or item.get('tradeability_state')}"
                    for item in watchlist_items
                )
            )
        if opportunity_items:
            parts.append(
                "机会池："
                + "；".join(
                    f"{item.get('display_name')}: {item.get('candidate_state')} / {item.get('action_hint')}"
                    for item in opportunity_items
                )
            )
        return " ".join(parts) or "当前没有更多结构化补充。"


_stock_analysis_tooling_service: StockAnalysisToolingService | None = None


def get_stock_analysis_tooling_service() -> StockAnalysisToolingService:
    global _stock_analysis_tooling_service
    if _stock_analysis_tooling_service is None:
        _stock_analysis_tooling_service = StockAnalysisToolingService()
    return _stock_analysis_tooling_service


def reset_stock_analysis_tooling_service() -> None:
    global _stock_analysis_tooling_service
    _stock_analysis_tooling_service = None
