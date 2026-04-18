from __future__ import annotations

from typing import Any, Sequence

from pydantic import BaseModel, Field

CONTEXT_ONLY_MODE = "context_only"
NEED_TOOLING_MODE = "need_tooling"
USER_FORCED_TOOLING_MODE = "user_forced_tooling"

INTERNAL_TOOL_LAYER = "internal_structured"
MARKET_TOOL_LAYER = "market_price"
EXTERNAL_TOOL_LAYER = "external_confirmation"

LATEST_KEYWORDS = (
    "最新",
    "现在",
    "当前市场",
    "今天",
    "近期",
    "这两天",
    "最近",
    "盘后",
    "收盘",
)
PRICE_KEYWORDS = ("价格", "走势", "涨跌", "日线", "k线", "新高", "回撤", "承接")
MARKET_KEYWORDS = ("市场", "情绪", "指数", "环境", "风险偏好")
THEME_KEYWORDS = ("题材", "主线", "方向", "分歧", "退潮", "加强")
HOLDING_KEYWORDS = ("持仓", "仓位", "减仓", "止损", "保护利润", "风险")
ALERT_KEYWORDS = ("提醒", "告警", "变化", "异动")
NEWS_KEYWORDS = ("新闻", "公告", "催化", "消息面")
EXTERNAL_CONFIRMATION_KEYWORDS = ("外部", "确认", "验证", "yfinance")
COMPARISON_KEYWORDS = ("比较", "对比", "谁更强", "谁更优先", "哪个更好")
CONTEXT_ONLY_KEYWORDS = ("总结", "解释", "复述", "基于当前上下文", "根据当前卡片")


class StockAnalysisToolPlannerResult(BaseModel):
    mode: str = CONTEXT_ONLY_MODE
    tool_reason: str | None = None
    missing_context_hints: list[str] = Field(default_factory=list)
    tool_plan: list[str] = Field(default_factory=list)
    tool_layers_to_use: list[str] = Field(default_factory=list)


class StockAnalysisToolPlanner:
    def plan(
        self,
        *,
        thread: dict[str, Any],
        context_cards: Sequence[dict[str, Any]],
        conversation_history: Sequence[dict[str, Any]],
        user_message: str,
        force_tooling: bool,
        ticker_refs: Sequence[str] | None = None,
        theme_refs: Sequence[str] | None = None,
    ) -> StockAnalysisToolPlannerResult:
        del conversation_history
        normalized_message = str(user_message or "").strip()
        ticker_list = list(ticker_refs or [])
        theme_list = list(theme_refs or [])
        missing_context_hints = self._build_missing_context_hints(
            thread=thread,
            context_cards=context_cards,
            user_message=normalized_message,
            ticker_refs=ticker_list,
            theme_refs=theme_list,
        )
        if force_tooling:
            effective_missing_hints = (
                missing_context_hints
                or self._build_forced_tooling_hints(
                    ticker_refs=ticker_list,
                    theme_refs=theme_list,
                )
            )
            return StockAnalysisToolPlannerResult(
                mode=USER_FORCED_TOOLING_MODE,
                tool_reason="用户显式要求补数据后再回答，本轮进入强制补数模式。",
                missing_context_hints=effective_missing_hints,
                tool_plan=self._build_tool_plan(effective_missing_hints),
                tool_layers_to_use=self._resolve_tool_layers(effective_missing_hints),
            )

        if self._can_answer_from_context_only(
            user_message=normalized_message,
            missing_context_hints=missing_context_hints,
        ):
            return StockAnalysisToolPlannerResult(
                mode=CONTEXT_ONLY_MODE,
                tool_reason="当前问题主要是在解释、总结或比较现有上下文，暂不需要额外补数。",
                missing_context_hints=missing_context_hints,
                tool_plan=[],
                tool_layers_to_use=[],
            )

        if missing_context_hints:
            return StockAnalysisToolPlannerResult(
                mode=NEED_TOOLING_MODE,
                tool_reason="当前问题依赖最新状态或补充证据，而显式上下文不足，因此触发按需补数。",
                missing_context_hints=missing_context_hints,
                tool_plan=self._build_tool_plan(missing_context_hints),
                tool_layers_to_use=self._resolve_tool_layers(missing_context_hints),
            )

        return StockAnalysisToolPlannerResult(
            mode=CONTEXT_ONLY_MODE,
            tool_reason="当前上下文足以回答，本轮保持 context_only。",
            missing_context_hints=[],
            tool_plan=[],
            tool_layers_to_use=[],
        )

    def _can_answer_from_context_only(
        self,
        *,
        user_message: str,
        missing_context_hints: Sequence[str],
    ) -> bool:
        if not user_message:
            return True
        if any(keyword in user_message for keyword in CONTEXT_ONLY_KEYWORDS):
            return True
        if not missing_context_hints:
            latest_related = any(
                keyword in user_message
                for keyword in (
                    *LATEST_KEYWORDS,
                    *PRICE_KEYWORDS,
                    *MARKET_KEYWORDS,
                    *THEME_KEYWORDS,
                    *HOLDING_KEYWORDS,
                    *ALERT_KEYWORDS,
                    *NEWS_KEYWORDS,
                    *EXTERNAL_CONFIRMATION_KEYWORDS,
                )
            )
            return not latest_related
        return False

    def _build_missing_context_hints(
        self,
        *,
        thread: dict[str, Any],
        context_cards: Sequence[dict[str, Any]],
        user_message: str,
        ticker_refs: Sequence[str],
        theme_refs: Sequence[str],
    ) -> list[str]:
        hints: list[str] = []
        if not context_cards:
            hints.append("insufficient_comparison_basis")
            return hints
        if any(keyword in user_message for keyword in PRICE_KEYWORDS + LATEST_KEYWORDS) and ticker_refs:
            hints.append("latest_price_action")
        if any(keyword in user_message for keyword in MARKET_KEYWORDS):
            hints.append("latest_market_state")
        if any(keyword in user_message for keyword in THEME_KEYWORDS) and theme_refs:
            hints.append("latest_theme_status")
        if any(keyword in user_message for keyword in HOLDING_KEYWORDS) and (
            thread.get("focus_type") == "holding"
            or any(str(item.get("context_type") or "") == "holding" for item in context_cards)
        ):
            hints.append("latest_holding_risk")
        if any(keyword in user_message for keyword in ALERT_KEYWORDS):
            hints.append("latest_alert_change")
        if any(keyword in user_message for keyword in NEWS_KEYWORDS):
            hints.append("recent_news")
        if any(keyword in user_message for keyword in EXTERNAL_CONFIRMATION_KEYWORDS):
            hints.append("recent_external_confirmation")
        if any(keyword in user_message for keyword in COMPARISON_KEYWORDS) and len(ticker_refs) < 2:
            hints.append("insufficient_comparison_basis")
        deduped: list[str] = []
        for hint in hints:
            if hint not in deduped:
                deduped.append(hint)
        return deduped

    @staticmethod
    def _build_tool_plan(missing_context_hints: Sequence[str]) -> list[str]:
        plan_map = {
            "latest_price_action": "补最近日线价格与阶段涨跌，确认当前承接和波动。",
            "latest_market_state": "补市场与情绪摘要，确认当前风险偏好是否变化。",
            "latest_theme_status": "补题材雷达与主线状态，确认方向是否仍然成立。",
            "latest_holding_risk": "补持仓周期与卖点风险结果，确认当前处理边界。",
            "latest_alert_change": "补提醒中心当前 active alerts，确认是否有新增变化。",
            "recent_news": "尝试补最新新闻或公告摘要；若不可用则明确降级。",
            "recent_external_confirmation": "尝试补外部确认信息；若不可用则明确降级。",
            "insufficient_comparison_basis": "补可比较的结构化研究对象，避免只凭单卡片强行对比。",
        }
        return [plan_map[item] for item in missing_context_hints if item in plan_map]

    @staticmethod
    def _resolve_tool_layers(missing_context_hints: Sequence[str]) -> list[str]:
        layers: list[str] = []
        internal_hints = {
            "latest_market_state",
            "latest_theme_status",
            "latest_holding_risk",
            "latest_alert_change",
            "insufficient_comparison_basis",
        }
        market_hints = {"latest_price_action"}
        external_hints = {"recent_news", "recent_external_confirmation"}
        if any(item in internal_hints for item in missing_context_hints):
            layers.append(INTERNAL_TOOL_LAYER)
        if any(item in market_hints for item in missing_context_hints):
            layers.append(MARKET_TOOL_LAYER)
        if any(item in external_hints for item in missing_context_hints):
            layers.append(EXTERNAL_TOOL_LAYER)
        return layers

    @staticmethod
    def _build_forced_tooling_hints(
        *,
        ticker_refs: Sequence[str],
        theme_refs: Sequence[str],
    ) -> list[str]:
        if ticker_refs:
            return ["latest_price_action"]
        if theme_refs:
            return ["latest_theme_status"]
        return ["latest_market_state"]


_stock_analysis_tool_planner: StockAnalysisToolPlanner | None = None


def get_stock_analysis_tool_planner() -> StockAnalysisToolPlanner:
    global _stock_analysis_tool_planner
    if _stock_analysis_tool_planner is None:
        _stock_analysis_tool_planner = StockAnalysisToolPlanner()
    return _stock_analysis_tool_planner


def reset_stock_analysis_tool_planner() -> None:
    global _stock_analysis_tool_planner
    _stock_analysis_tool_planner = None
