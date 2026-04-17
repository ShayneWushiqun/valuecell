from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from .ashare_decision_judge_service import AShareDecisionJudgeService
from .exit_risk_center_service import ExitRiskCenterService
from .holding_lifecycle_service import HoldingLifecycleService
from .homepage_context_service import HomepageContextService
from .opportunity_pool_service import OpportunityPoolService
from .strategy_preference_service import StrategyPreferenceService

SUMMARY_TICKER_LIMIT = 6


class RiskSizingService:
    def __init__(
        self,
        homepage_context_service: Optional[HomepageContextService] = None,
        holding_lifecycle_service: Optional[HoldingLifecycleService] = None,
        exit_risk_center_service: Optional[ExitRiskCenterService] = None,
        opportunity_pool_service: Optional[OpportunityPoolService] = None,
        ashare_decision_judge_service: Optional[AShareDecisionJudgeService] = None,
        strategy_preference_service: Optional[StrategyPreferenceService] = None,
    ) -> None:
        self.homepage_context_service = homepage_context_service or HomepageContextService()
        self.holding_lifecycle_service = holding_lifecycle_service or HoldingLifecycleService()
        self.exit_risk_center_service = exit_risk_center_service or ExitRiskCenterService()
        self.opportunity_pool_service = opportunity_pool_service or OpportunityPoolService()
        self.ashare_decision_judge_service = (
            ashare_decision_judge_service or AShareDecisionJudgeService()
        )
        self.strategy_preference_service = (
            strategy_preference_service or StrategyPreferenceService()
        )

    def get_summary(self, *, user_id: str) -> dict[str, Any]:
        homepage_context = self.homepage_context_service.get_homepage_context(user_id)
        lifecycle_overview = self.holding_lifecycle_service.get_overview(user_id)
        exit_risk_overview = self.exit_risk_center_service.get_overview(user_id)
        opportunities = self.opportunity_pool_service.get_opportunity_candidates(user_id)
        preference = self.strategy_preference_service.get_effective_profile(user_id)

        lifecycle_items = list(lifecycle_overview.get("items") or [])
        exit_risk_items = self._merge_exit_risk_groups(exit_risk_overview)
        opportunity_items = list(opportunities.get("items") or [])
        market_risk_level = self._resolve_market_risk_level(
            homepage_context=homepage_context,
            lifecycle_items=lifecycle_items,
            exit_risk_items=exit_risk_items,
            preference=preference,
        )
        ticker_suggestions = self._build_ticker_suggestions(
            user_id=user_id,
            lifecycle_items=lifecycle_items,
            exit_risk_items=exit_risk_items,
            opportunity_items=opportunity_items,
            market_risk_level=market_risk_level,
            preference=preference,
        )
        available = any(
            [
                bool(homepage_context),
                bool(lifecycle_items),
                bool(exit_risk_items),
                bool(opportunity_items),
            ]
        )
        if not available:
            return {
                "generated_at": dt.datetime.now(dt.UTC).isoformat(),
                "available": False,
                "empty_message": "当前缺少可用市场、持仓或机会数据，先保持轻量观察。",
                "market_risk_level": "中性",
                "suggested_total_exposure_range": "20% - 30%",
                "suggested_new_position_range": "3% - 5%",
                "suggested_add_position_range": "2% - 4%",
                "holding_risk_note": "暂无持仓数据时，优先控制总暴露，不急于扩张。",
                "entry_risk_note": "暂无机会样本时，先观察主线和承接是否稳定。",
                "portfolio_balance_note": "暂无可用组合结构数据，先避免方向过散。",
                "action_queue_note": "先补齐快照和持仓语境，再生成更细建议。",
                "ticker_suggestions": [],
            }
        return {
            "generated_at": dt.datetime.now(dt.UTC).isoformat(),
            "available": True,
            "empty_message": None,
            "market_risk_level": market_risk_level,
            "suggested_total_exposure_range": self._resolve_total_exposure_range(
                homepage_context=homepage_context,
                market_risk_level=market_risk_level,
                preference=preference,
            ),
            "suggested_new_position_range": self._resolve_new_position_range(
                market_risk_level=market_risk_level,
                holding_count=len(lifecycle_items),
                preference=preference,
            ),
            "suggested_add_position_range": self._resolve_add_position_range(
                market_risk_level=market_risk_level,
                exit_risk_items=exit_risk_items,
                preference=preference,
            ),
            "holding_risk_note": self._build_holding_risk_note(
                lifecycle_items=lifecycle_items,
                exit_risk_items=exit_risk_items,
            ),
            "entry_risk_note": self._build_entry_risk_note(
                market_risk_level=market_risk_level,
                opportunity_items=opportunity_items,
            ),
            "portfolio_balance_note": self._build_portfolio_balance_note(
                lifecycle_items=lifecycle_items,
                opportunity_items=opportunity_items,
            ),
            "action_queue_note": self._build_action_queue_note(
                exit_risk_items=exit_risk_items,
                opportunity_items=opportunity_items,
            ),
            "ticker_suggestions": ticker_suggestions,
        }

    def get_ticker_summary(self, *, user_id: str, ticker: str) -> dict[str, Any]:
        normalized_ticker = str(ticker or "").strip()
        if not normalized_ticker:
            return self._empty_ticker_result(ticker="")

        homepage_context = self.homepage_context_service.get_homepage_context(user_id)
        lifecycle_overview = self.holding_lifecycle_service.get_overview(user_id)
        exit_risk_overview = self.exit_risk_center_service.get_overview(user_id)
        opportunities = self.opportunity_pool_service.get_opportunity_candidates(user_id)
        preference = self.strategy_preference_service.get_effective_profile(user_id)

        lifecycle_items = list(lifecycle_overview.get("items") or [])
        exit_risk_items = self._merge_exit_risk_groups(exit_risk_overview)
        opportunity_items = list(opportunities.get("items") or [])
        market_risk_level = self._resolve_market_risk_level(
            homepage_context=homepage_context,
            lifecycle_items=lifecycle_items,
            exit_risk_items=exit_risk_items,
            preference=preference,
        )
        lifecycle_item = self._find_by_ticker(lifecycle_items, normalized_ticker)
        exit_risk_item = self._find_by_ticker(exit_risk_items, normalized_ticker)
        opportunity_item = self._find_by_ticker(opportunity_items, normalized_ticker)
        if not any([lifecycle_item, exit_risk_item, opportunity_item]):
            return self._empty_ticker_result(ticker=normalized_ticker)

        judge_result = self.ashare_decision_judge_service.judge(
            ticker=normalized_ticker,
            user_id=user_id,
            enable_agent=False,
            force_refresh_context=False,
            user_note=None,
        )
        return self._build_ticker_suggestion(
            ticker=normalized_ticker,
            lifecycle_item=lifecycle_item,
            exit_risk_item=exit_risk_item,
            opportunity_item=opportunity_item,
            market_risk_level=market_risk_level,
            preference=preference,
            lifecycle_items=lifecycle_items,
            judge_result=judge_result,
        )

    def _build_ticker_suggestions(
        self,
        *,
        user_id: str,
        lifecycle_items: list[dict[str, Any]],
        exit_risk_items: list[dict[str, Any]],
        opportunity_items: list[dict[str, Any]],
        market_risk_level: str,
        preference: dict[str, Any],
    ) -> list[dict[str, Any]]:
        ordered_tickers: list[str] = []
        for source_items in (
            exit_risk_items,
            lifecycle_items,
            opportunity_items[: SUMMARY_TICKER_LIMIT * 2],
        ):
            for item in source_items:
                ticker = str(item.get("ticker") or "").strip()
                if ticker and ticker not in ordered_tickers:
                    ordered_tickers.append(ticker)
        result: list[dict[str, Any]] = []
        for ticker in ordered_tickers[:SUMMARY_TICKER_LIMIT]:
            judge_result = self.ashare_decision_judge_service.judge(
                ticker=ticker,
                user_id=user_id,
                enable_agent=False,
                force_refresh_context=False,
                user_note=None,
            )
            result.append(
                self._build_ticker_suggestion(
                    ticker=ticker,
                    lifecycle_item=self._find_by_ticker(lifecycle_items, ticker),
                    exit_risk_item=self._find_by_ticker(exit_risk_items, ticker),
                    opportunity_item=self._find_by_ticker(opportunity_items, ticker),
                    market_risk_level=market_risk_level,
                    preference=preference,
                    lifecycle_items=lifecycle_items,
                    judge_result=judge_result,
                )
            )
        return result

    def _build_ticker_suggestion(
        self,
        *,
        ticker: str,
        lifecycle_item: dict[str, Any] | None,
        exit_risk_item: dict[str, Any] | None,
        opportunity_item: dict[str, Any] | None,
        market_risk_level: str,
        preference: dict[str, Any],
        lifecycle_items: list[dict[str, Any]],
        judge_result: dict[str, Any],
    ) -> dict[str, Any]:
        display_name = (
            str((lifecycle_item or {}).get("display_name") or "")
            or str((exit_risk_item or {}).get("display_name") or "")
            or str((opportunity_item or {}).get("display_name") or "")
            or ticker
        )
        role_label = (
            str((lifecycle_item or {}).get("role_label") or "")
            or str((opportunity_item or {}).get("role_label") or "")
        )
        tradeability_state = (
            str((lifecycle_item or {}).get("tradeability_state") or "")
            or str((opportunity_item or {}).get("tradeability_state") or "")
        )
        action = str((exit_risk_item or {}).get("action") or (lifecycle_item or {}).get("action") or "")
        crowded = self._is_theme_crowded(lifecycle_items=lifecycle_items, current_item=lifecycle_item)
        risk_level = self._resolve_ticker_risk_level(
            market_risk_level=market_risk_level,
            action=action,
            tradeability_state=tradeability_state,
            role_label=role_label,
            liquidity_warning=str((exit_risk_item or {}).get("liquidity_warning") or ""),
        )
        reasons = self._build_ticker_reasons(
            lifecycle_item=lifecycle_item,
            exit_risk_item=exit_risk_item,
            opportunity_item=opportunity_item,
            judge_result=judge_result,
            crowded=crowded,
        )
        return {
            "ticker": ticker,
            "display_name": display_name,
            "available": True,
            "risk_level": risk_level,
            "suggested_position_range": self._resolve_single_position_range(
                risk_level=risk_level,
                role_label=role_label,
                tradeability_state=tradeability_state,
                crowded=crowded,
                preference=preference,
            ),
            "suggested_first_entry_range": self._resolve_first_entry_range(
                risk_level=risk_level,
                role_label=role_label,
                tradeability_state=tradeability_state,
                crowded=crowded,
                preference=preference,
            ),
            "suggested_add_range": self._resolve_add_range(
                risk_level=risk_level,
                role_label=role_label,
                tradeability_state=tradeability_state,
                crowded=crowded,
                preference=preference,
            ),
            "stop_loss_style": self._build_stop_loss_style(
                risk_level=risk_level,
                tradeability_state=tradeability_state,
            ),
            "profit_protection_style": self._build_profit_protection_style(
                risk_level=risk_level,
                action=action,
            ),
            "liquidity_warning": str((exit_risk_item or {}).get("liquidity_warning") or "")
            or ("当前更适合优先确认流动性与承接。" if tradeability_state == "流动性风险" else None),
            "summary": self._build_ticker_summary_text(
                display_name=display_name,
                risk_level=risk_level,
                role_label=role_label,
                tradeability_state=tradeability_state,
                crowded=crowded,
            ),
            "reasons": reasons,
            "empty_message": None,
        }

    @staticmethod
    def _resolve_market_risk_level(
        *,
        homepage_context: dict[str, Any],
        lifecycle_items: list[dict[str, Any]],
        exit_risk_items: list[dict[str, Any]],
        preference: dict[str, Any],
    ) -> str:
        market_state = str((homepage_context.get("market_overview") or {}).get("market_state") or "")
        cycle_stage = str((homepage_context.get("emotion_cycle") or {}).get("cycle_stage") or "")
        high_risk_count = len(
            [
                item
                for item in lifecycle_items
                if str(item.get("lifecycle_stage") or "")
                in {"破逻辑退出期", "退潮减仓期"}
            ]
        )
        urgent_count = len(
            [
                item
                for item in exit_risk_items
                if str(item.get("action") or "") in {"纪律止损", "保护利润"}
            ]
        )
        if market_state in {"退潮", "震荡"} or urgent_count >= 2 or high_risk_count >= 2:
            return "偏高"
        if market_state in {"修复", "轮动"} or cycle_stage in {"修复试错", "分歧"}:
            return "中性"
        if str(preference.get("risk_style") or "") == "steady":
            return "中性"
        return "偏低"

    @staticmethod
    def _resolve_total_exposure_range(
        *,
        homepage_context: dict[str, Any],
        market_risk_level: str,
        preference: dict[str, Any],
    ) -> str:
        total_position_range = str(
            ((homepage_context.get("risk_control") or {}).get("total_position_range") or "")
        )
        mapping = {
            "2-3成": "20% - 30%",
            "3-5成": "30% - 50%",
            "5-7成": "50% - 70%",
        }
        if total_position_range in mapping:
            result = mapping[total_position_range]
        elif market_risk_level == "偏低":
            result = "45% - 60%"
        elif market_risk_level == "中性":
            result = "30% - 45%"
        else:
            result = "15% - 30%"
        if str(preference.get("risk_style") or "") == "steady" and result == "50% - 70%":
            return "40% - 55%"
        return result

    @staticmethod
    def _resolve_new_position_range(
        *,
        market_risk_level: str,
        holding_count: int,
        preference: dict[str, Any],
    ) -> str:
        if market_risk_level == "偏低":
            result = "6% - 10%"
        elif market_risk_level == "中性":
            result = "4% - 7%"
        else:
            result = "2% - 4%"
        if holding_count >= 5:
            return "2% - 5%"
        if str(preference.get("risk_style") or "") == "steady" and result == "6% - 10%":
            return "5% - 8%"
        return result

    @staticmethod
    def _resolve_add_position_range(
        *,
        market_risk_level: str,
        exit_risk_items: list[dict[str, Any]],
        preference: dict[str, Any],
    ) -> str:
        urgent_count = len(
            [
                item
                for item in exit_risk_items
                if str(item.get("action") or "") in {"纪律止损", "保护利润"}
            ]
        )
        if market_risk_level == "偏低":
            result = "3% - 6%"
        elif market_risk_level == "中性":
            result = "2% - 4%"
        else:
            result = "1% - 3%"
        if urgent_count:
            return "1% - 3%"
        if str(preference.get("risk_style") or "") == "steady" and result == "3% - 6%":
            return "2% - 4%"
        return result

    @staticmethod
    def _build_holding_risk_note(
        *,
        lifecycle_items: list[dict[str, Any]],
        exit_risk_items: list[dict[str, Any]],
    ) -> str:
        high_risk_count = len(
            [
                item
                for item in lifecycle_items
                if str(item.get("lifecycle_stage") or "")
                in {"破逻辑退出期", "退潮减仓期"}
            ]
        )
        if high_risk_count or exit_risk_items:
            return (
                f"当前有 {len(exit_risk_items)} 个持仓进入风险处理语境，"
                "更适合先处理纪律止损、保护利润和减仓观察，再考虑新增暴露。"
            )
        return "当前持仓压力不算重，但也更适合先小后大，避免一次性放开。"

    @staticmethod
    def _build_entry_risk_note(
        *,
        market_risk_level: str,
        opportunity_items: list[dict[str, Any]],
    ) -> str:
        if not opportunity_items:
            return "当前暂无清晰机会池前排，先看主线是否继续强化，不急于新开仓。"
        if market_risk_level == "偏高":
            return "市场风险仍偏高，新开仓以轻仓试错和分批参与为主，优先核心票。"
        return "新开仓更适合优先看主线核心和流动性较好的方向，避免一次性打满。"

    @staticmethod
    def _build_portfolio_balance_note(
        *,
        lifecycle_items: list[dict[str, Any]],
        opportunity_items: list[dict[str, Any]],
    ) -> str:
        holding_themes = {
            str(item.get("theme_name") or "").strip()
            for item in lifecycle_items
            if str(item.get("theme_name") or "").strip()
        }
        opportunity_themes = {
            str(item.get("topic_name") or "").strip()
            for item in opportunity_items[:5]
            if str(item.get("topic_name") or "").strip()
        }
        if len(holding_themes) <= 1 and lifecycle_items:
            return "当前组合方向较集中，新增仓位更适合控制在少量补充，不要把题材拥挤度继续抬高。"
        if holding_themes and opportunity_themes and holding_themes.isdisjoint(opportunity_themes):
            return "持仓与机会池方向分离度较高，新增前先确认是否会把组合拉得过散。"
        return "组合层面更适合围绕 1 到 2 个主线方向展开，兼顾已有持仓与新机会的节奏。"

    @staticmethod
    def _build_action_queue_note(
        *,
        exit_risk_items: list[dict[str, Any]],
        opportunity_items: list[dict[str, Any]],
    ) -> str:
        if exit_risk_items:
            first_item = exit_risk_items[0]
            return (
                f"今天先处理 {first_item.get('display_name') or first_item.get('ticker')} 这类风险项，"
                "再回头看机会池前排的低风险参与窗口。"
            )
        if opportunity_items:
            first_item = opportunity_items[0]
            return (
                f"今天可以先看 {first_item.get('display_name') or first_item.get('ticker')} 等前排候选，"
                "但节奏仍以轻仓试错和等待确认优先。"
            )
        return "今天更适合先观察市场与主线，再决定是否需要补仓或新开仓。"

    @staticmethod
    def _merge_exit_risk_groups(overview: dict[str, Any]) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        for key in (
            "high_priority_items",
            "profit_protection_items",
            "discipline_stop_items",
            "watch_items",
        ):
            for item in list(overview.get(key) or []):
                ticker = str(item.get("ticker") or "")
                if ticker and not any(str(existing.get("ticker") or "") == ticker for existing in merged):
                    merged.append(item)
        return merged

    @staticmethod
    def _find_by_ticker(items: list[dict[str, Any]], ticker: str) -> dict[str, Any] | None:
        for item in items:
            if str(item.get("ticker") or "") == ticker:
                return item
        return None

    @staticmethod
    def _resolve_ticker_risk_level(
        *,
        market_risk_level: str,
        action: str,
        tradeability_state: str,
        role_label: str,
        liquidity_warning: str,
    ) -> str:
        if action in {"纪律止损", "保护利润"} or liquidity_warning:
            return "高"
        if tradeability_state in {"谨慎追高", "流动性风险"}:
            return "高"
        if market_risk_level == "偏高":
            return "中"
        if role_label in {"龙头", "中军"}:
            return "中"
        return "低"

    @staticmethod
    def _is_theme_crowded(
        *,
        lifecycle_items: list[dict[str, Any]],
        current_item: dict[str, Any] | None,
    ) -> bool:
        theme_name = str((current_item or {}).get("theme_name") or "").strip()
        if not theme_name:
            return False
        same_theme_count = len(
            [
                item
                for item in lifecycle_items
                if str(item.get("theme_name") or "").strip() == theme_name
            ]
        )
        return same_theme_count >= 2

    def _build_ticker_reasons(
        self,
        *,
        lifecycle_item: dict[str, Any] | None,
        exit_risk_item: dict[str, Any] | None,
        opportunity_item: dict[str, Any] | None,
        judge_result: dict[str, Any],
        crowded: bool,
    ) -> list[str]:
        reasons: list[str] = []
        if lifecycle_item:
            reasons.append(
                f"当前生命周期为 {lifecycle_item.get('lifecycle_stage') or '待观察'}，"
                f"动作语义偏 {lifecycle_item.get('action') or '持有观察'}。"
            )
        if exit_risk_item:
            reasons.append(
                f"卖点与风险中心当前提示 {exit_risk_item.get('action') or '观察'}，"
                f"风险类型为 {exit_risk_item.get('risk_type') or '节奏管理'}。"
            )
        if opportunity_item:
            reasons.append(
                f"机会池状态为 {opportunity_item.get('candidate_state') or '普通观察'}，"
                f"可交易性为 {opportunity_item.get('tradeability_state') or '待确认'}。"
            )
        if judge_result.get("summary"):
            reasons.append(str(judge_result.get("summary")))
        if crowded:
            reasons.append("当前题材在组合里已有一定集中度，新开或加仓都更适合再收敛一些。")
        deduped: list[str] = []
        seen: set[str] = set()
        for item in reasons:
            text = str(item or "").strip()
            if text and text not in seen:
                seen.add(text)
                deduped.append(text)
        return deduped[:5]

    @staticmethod
    def _resolve_single_position_range(
        *,
        risk_level: str,
        role_label: str,
        tradeability_state: str,
        crowded: bool,
        preference: dict[str, Any],
    ) -> str:
        if risk_level == "高":
            result = "3% - 6%"
        elif role_label in {"龙头", "中军"} and tradeability_state not in {"谨慎追高", "流动性风险"}:
            result = "6% - 10%"
        else:
            result = "4% - 7%"
        if crowded or str(preference.get("risk_style") or "") == "steady":
            return "3% - 6%"
        return result

    @staticmethod
    def _resolve_first_entry_range(
        *,
        risk_level: str,
        role_label: str,
        tradeability_state: str,
        crowded: bool,
        preference: dict[str, Any],
    ) -> str:
        if risk_level == "高" or tradeability_state in {"谨慎追高", "流动性风险"}:
            result = "1% - 2%"
        elif role_label in {"龙头", "中军"}:
            result = "2% - 4%"
        else:
            result = "1% - 3%"
        if crowded or str(preference.get("buy_style") or "") in {"pullback", "low_absorb"}:
            return "1% - 3%"
        return result

    @staticmethod
    def _resolve_add_range(
        *,
        risk_level: str,
        role_label: str,
        tradeability_state: str,
        crowded: bool,
        preference: dict[str, Any],
    ) -> str:
        if risk_level == "高":
            result = "0% - 2%"
        elif role_label in {"龙头", "中军"} and tradeability_state == "可低吸":
            result = "2% - 4%"
        else:
            result = "1% - 3%"
        if crowded or not bool(preference.get("accept_high_position")):
            return "1% - 2%"
        return result

    @staticmethod
    def _build_stop_loss_style(*, risk_level: str, tradeability_state: str) -> str:
        if risk_level == "高" or tradeability_state == "流动性风险":
            return "止损风格更适合偏紧，先确认流动性，再按纪律分批收缩。"
        return "止损风格以预设失效条件为主，先小后大，不把一次波动放大成重动作。"

    @staticmethod
    def _build_profit_protection_style(*, risk_level: str, action: str) -> str:
        if action == "保护利润":
            return "已有浮盈时更适合边走边看，先保留利润垫，再考虑是否继续拿。"
        if risk_level == "高":
            return "利润保护以先收缩风险为主，避免回撤把主动权交出去。"
        return "利润保护以分批抬高保护位为主，不一次性把节奏推得太激进。"

    @staticmethod
    def _build_ticker_summary_text(
        *,
        display_name: str,
        risk_level: str,
        role_label: str,
        tradeability_state: str,
        crowded: bool,
    ) -> str:
        crowded_text = "当前方向略拥挤，" if crowded else ""
        role_text = role_label or "当前标的"
        return (
            f"{display_name} 当前风险等级为 {risk_level}，{crowded_text}"
            f"更适合围绕 {role_text} 的定位做轻仓试错、分批参与和先小后大的节奏。"
            f" 若可交易性为 {tradeability_state or '待确认'}，则单次动作宜更保守。"
        )

    @staticmethod
    def _empty_ticker_result(*, ticker: str) -> dict[str, Any]:
        return {
            "ticker": ticker,
            "display_name": ticker or "未知标的",
            "available": False,
            "risk_level": "中",
            "suggested_position_range": "3% - 5%",
            "suggested_first_entry_range": "1% - 2%",
            "suggested_add_range": "0% - 2%",
            "stop_loss_style": "数据不足时更适合先轻仓观察，不放大单次动作。",
            "profit_protection_style": "若已有仓位，优先以保守保护方式管理，不急于放大操作。",
            "liquidity_warning": None,
            "summary": "当前缺少该标的的持仓、机会或风险语境，暂不外推更细分仓建议。",
            "reasons": ["缺少持仓周期、机会池或风险中心的直接引用样本。"],
            "empty_message": "Ticker risk sizing context is not available.",
        }


_risk_sizing_service: Optional[RiskSizingService] = None


def get_risk_sizing_service() -> RiskSizingService:
    global _risk_sizing_service
    if _risk_sizing_service is None:
        _risk_sizing_service = RiskSizingService()
    return _risk_sizing_service


def reset_risk_sizing_service() -> None:
    global _risk_sizing_service
    _risk_sizing_service = None
