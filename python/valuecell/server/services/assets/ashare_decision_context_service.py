from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional

from ..portfolio.holding_service import HoldingService
from .decision_alert_persistence_service import DecisionAlertPersistenceService
from .entry_timing_service import EntryTimingService
from .homepage_context_service import HomepageContextService
from .opportunity_pool_service import OpportunityPoolService
from .strategy_preference_service import StrategyPreferenceService


class AShareDecisionContextService:
    def __init__(
        self,
        homepage_context_service: Optional[HomepageContextService] = None,
        opportunity_pool_service: Optional[OpportunityPoolService] = None,
        entry_timing_service: Optional[EntryTimingService] = None,
        decision_alert_persistence_service: Optional[DecisionAlertPersistenceService] = None,
        strategy_preference_service: Optional[StrategyPreferenceService] = None,
        holding_service: Optional[HoldingService] = None,
    ) -> None:
        self.homepage_context_service = homepage_context_service or HomepageContextService()
        self.opportunity_pool_service = opportunity_pool_service or OpportunityPoolService()
        self.entry_timing_service = entry_timing_service or EntryTimingService()
        self.decision_alert_persistence_service = (
            decision_alert_persistence_service or DecisionAlertPersistenceService()
        )
        self.strategy_preference_service = (
            strategy_preference_service or StrategyPreferenceService()
        )
        self.holding_service = holding_service or HoldingService()

    def get_decision_context(
        self,
        *,
        ticker: str,
        user_id: str = "default_user",
    ) -> dict[str, Any]:
        normalized_ticker = str(ticker or "").strip()
        homepage_context = self.homepage_context_service.get_homepage_context(user_id)
        opportunity_result = self.opportunity_pool_service.get_opportunity_candidates(user_id=user_id)
        entry_timing_result = self.entry_timing_service.get_entry_timing_signals(user_id=user_id)
        decision_alert_list = self.decision_alert_persistence_service.list_alerts(
            user_id=user_id,
            status="active",
            limit=100,
        )
        preference_profile = self.strategy_preference_service.get_effective_profile(user_id)
        holdings = self.holding_service.list_holdings(user_id)

        candidate = self._find_by_ticker(opportunity_result.get("items") or [], normalized_ticker)
        signal = self._find_by_ticker(entry_timing_result.get("items") or [], normalized_ticker)
        alerts = [
            item
            for item in list(decision_alert_list.get("items") or [])
            if str(item.get("ticker") or "") == normalized_ticker
        ]
        holding = self._find_by_ticker(holdings, normalized_ticker)
        missing_context = self._build_missing_context(candidate, signal, alerts, holding)
        risk_items = self._build_risk_items(candidate, signal, alerts)
        rule_based_judgement = self._build_rule_based_judgement(candidate, signal, risk_items)
        available = candidate is not None

        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "ticker": normalized_ticker,
            "available": available,
            "empty_message": None if available else "当前 ticker 暂无可用裁决上下文",
            "market_context": self._build_market_context(homepage_context),
            "theme_context": self._build_theme_context(candidate),
            "candidate_context": self._build_candidate_context(candidate),
            "entry_timing_context": self._build_entry_timing_context(signal),
            "alert_context": self._build_alert_context(alerts),
            "preference_context": self._build_preference_context(preference_profile),
            "portfolio_context": self._build_portfolio_context(holding),
            "risk_context": {
                "items": risk_items,
            },
            "missing_context": missing_context,
            "rule_based_judgement": rule_based_judgement,
            "agent_prompt_preview": self._build_agent_prompt_preview(
                normalized_ticker=normalized_ticker,
                candidate=candidate,
                signal=signal,
                risk_items=risk_items,
                missing_context=missing_context,
                preference_profile=preference_profile,
                alerts=alerts,
                market_context=homepage_context,
                holding=holding,
                rule_based_judgement=rule_based_judgement,
            ),
        }

    @staticmethod
    def _find_by_ticker(items: list[dict[str, Any]], ticker: str) -> dict[str, Any] | None:
        for item in items:
            if str(item.get("ticker") or "") == ticker:
                return item
        return None

    @staticmethod
    def _build_market_context(homepage_context: dict[str, Any]) -> dict[str, Any]:
        market_overview = homepage_context.get("market_overview") or {}
        emotion_cycle = homepage_context.get("emotion_cycle") or {}
        action_framework = homepage_context.get("action_framework") or {}
        return {
            "market_state": market_overview.get("market_state"),
            "emotion_stage": emotion_cycle.get("cycle_stage"),
            "temperature_score": market_overview.get("score"),
            "action_rhythm": action_framework.get("summary") or market_overview.get("action_hint"),
            "summary": market_overview.get("summary"),
        }

    @staticmethod
    def _build_theme_context(candidate: dict[str, Any] | None) -> dict[str, Any]:
        if candidate is None:
            return {
                "topic_name": None,
                "source_tags": [],
                "role_label": None,
                "trend_quality": None,
            }
        return {
            "topic_name": candidate.get("topic_name"),
            "source_tags": list(candidate.get("source_tags") or []),
            "role_label": candidate.get("role_label"),
            "trend_quality": candidate.get("trend_quality"),
        }

    @staticmethod
    def _build_candidate_context(candidate: dict[str, Any] | None) -> dict[str, Any]:
        if candidate is None:
            return {
                "priority_score": None,
                "candidate_state": None,
                "tradeability_state": None,
                "expectation_gap_level": None,
                "matched_preferences": [],
                "preference_adjustments": [],
                "reasons": [],
                "time_horizon": None,
            }
        return {
            "priority_score": candidate.get("priority_score"),
            "candidate_state": candidate.get("candidate_state"),
            "tradeability_state": candidate.get("tradeability_state"),
            "expectation_gap_level": candidate.get("expectation_gap_level"),
            "matched_preferences": list(candidate.get("matched_preferences") or []),
            "preference_adjustments": list(candidate.get("preference_adjustments") or []),
            "reasons": list(candidate.get("reasons") or []),
            "time_horizon": candidate.get("time_horizon"),
        }

    @staticmethod
    def _build_entry_timing_context(signal: dict[str, Any] | None) -> dict[str, Any]:
        if signal is None:
            return {
                "action": None,
                "confidence": None,
                "summary": None,
                "reasons": [],
                "missing_confirmations": [],
                "invalid_conditions": [],
            }
        return {
            "action": signal.get("action"),
            "confidence": signal.get("confidence"),
            "summary": signal.get("summary"),
            "reasons": list(signal.get("reasons") or []),
            "missing_confirmations": list(signal.get("missing_confirmations") or []),
            "invalid_conditions": list(signal.get("invalid_conditions") or []),
        }

    @staticmethod
    def _build_alert_context(alerts: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "active_count": len(alerts),
            "items": alerts,
        }

    @staticmethod
    def _build_preference_context(profile: dict[str, Any]) -> dict[str, Any]:
        return {
            "template_id": profile.get("template_id"),
            "template_title": profile.get("template_title"),
            "risk_style": profile.get("risk_style"),
            "buy_style": profile.get("buy_style"),
            "preferred_themes": list(profile.get("preferred_themes") or []),
            "avoid_risks": list(profile.get("avoid_risks") or []),
            "accept_high_position": profile.get("accept_high_position"),
            "prefer_expectation_gap": profile.get("prefer_expectation_gap"),
            "prefer_leader_or_core": profile.get("prefer_leader_or_core"),
            "note": profile.get("note"),
        }

    @staticmethod
    def _build_portfolio_context(holding: dict[str, Any] | None) -> dict[str, Any]:
        if holding is None:
            return {
                "has_position": False,
                "summary": None,
                "latest_action": None,
                "risk_level": None,
                "market_snapshot": None,
            }
        latest_diagnosis = holding.get("latest_diagnosis") or {}
        return {
            "has_position": True,
            "summary": latest_diagnosis.get("summary"),
            "latest_action": latest_diagnosis.get("action"),
            "risk_level": latest_diagnosis.get("risk_level"),
            "market_snapshot": holding.get("market_snapshot"),
        }

    @staticmethod
    def _build_missing_context(
        candidate: dict[str, Any] | None,
        signal: dict[str, Any] | None,
        alerts: list[dict[str, Any]],
        holding: dict[str, Any] | None,
    ) -> list[str]:
        missing: list[str] = []
        if candidate is None:
            missing.append("当前 ticker 不在机会池候选内。")
        if signal is None:
            missing.append("当前缺少对应的买点裁决信号。")
        if not alerts:
            missing.append("当前没有已落库的 active 提醒。")
        if holding is None:
            missing.append("当前持仓系统没有该 ticker 的持仓摘要。")
        return missing

    @staticmethod
    def _build_risk_items(
        candidate: dict[str, Any] | None,
        signal: dict[str, Any] | None,
        alerts: list[dict[str, Any]],
    ) -> list[str]:
        items: list[str] = []
        if candidate is not None:
            items.extend(list(candidate.get("invalid_conditions") or []))
            tradeability_state = str(candidate.get("tradeability_state") or "")
            trend_quality = str(candidate.get("trend_quality") or "")
            if tradeability_state == "谨慎追高":
                items.append("当前处于谨慎追高区间，更适合等待回踩确认。")
            if tradeability_state == "流动性风险":
                items.append("存在流动性风险，需优先考虑退出条件。")
            if trend_quality == "走弱":
                items.append("趋势质量偏弱，持续性仍需确认。")
        if signal is not None:
            items.extend(list(signal.get("invalid_conditions") or []))
        for alert in alerts:
            if str(alert.get("alert_type") or "") == "风险回避":
                items.append(str(alert.get("body") or "当前存在风险回避提醒。"))
        return AShareDecisionContextService._unique_list(items)

    @staticmethod
    def _build_rule_based_judgement(
        candidate: dict[str, Any] | None,
        signal: dict[str, Any] | None,
        risk_items: list[str],
    ) -> dict[str, Any]:
        if signal is not None:
            return {
                "action": signal.get("action"),
                "summary": signal.get("summary"),
                "reasons": list(signal.get("reasons") or []),
                "missing_confirmations": list(signal.get("missing_confirmations") or []),
                "invalid_conditions": list(signal.get("invalid_conditions") or []),
            }
        if candidate is None:
            return {
                "action": "继续观察",
                "summary": "当前缺少足够上下文，先观察，不构成买入指令。",
                "reasons": ["机会池里暂未识别到该 ticker 的稳定候选信息。"] + risk_items[:1],
                "missing_confirmations": ["需要补充候选、题材和买点信号后再判断。"],
                "invalid_conditions": [],
            }
        tradeability_state = str(candidate.get("tradeability_state") or "")
        invalid_conditions = list(candidate.get("invalid_conditions") or [])
        if tradeability_state == "流动性风险" or invalid_conditions:
            action = "暂不参与"
        elif tradeability_state == "谨慎追高":
            action = "等待回踩确认"
        elif str(candidate.get("candidate_state") or "") == "仅适合持有":
            action = "仅适合持有"
        elif str(candidate.get("candidate_state") or "") in {"候选买点", "高优先级买点"}:
            action = "接近可参与窗口"
        else:
            action = "继续观察"
        return {
            "action": action,
            "summary": "当前为规则版裁决摘要，仍需结合缺失信息和失效条件继续确认。",
            "reasons": list(candidate.get("reasons") or [])[:3],
            "missing_confirmations": list(candidate.get("missing_confirmations") or []),
            "invalid_conditions": invalid_conditions,
        }

    @staticmethod
    def _build_agent_prompt_preview(
        *,
        normalized_ticker: str,
        candidate: dict[str, Any] | None,
        signal: dict[str, Any] | None,
        risk_items: list[str],
        missing_context: list[str],
        preference_profile: dict[str, Any],
        alerts: list[dict[str, Any]],
        market_context: dict[str, Any],
        holding: dict[str, Any] | None,
        rule_based_judgement: dict[str, Any],
    ) -> str:
        candidate_name = str(
            (candidate or {}).get("display_name")
            or (signal or {}).get("display_name")
            or normalized_ticker
        )
        market_overview = market_context.get("market_overview") or {}
        emotion_cycle = market_context.get("emotion_cycle") or {}
        alert_summary = "；".join(
            [str(item.get("title") or item.get("body") or "") for item in alerts[:3] if item]
        ) or "暂无 active 提醒。"
        holding_text = "当前无持仓摘要。"
        if holding is not None:
            latest_diagnosis = holding.get("latest_diagnosis") or {}
            holding_text = (
                f"已有持仓，最近动作为 {latest_diagnosis.get('action') or '观察'}，"
                f"摘要：{latest_diagnosis.get('summary') or '暂无'}。"
            )
        risk_text = "；".join(risk_items[:5]) or "暂无额外风险提示。"
        missing_text = "；".join(missing_context[:5]) or "当前上下文字段较完整。"
        return (
            f"请围绕 A 股短周期 1 到 4 周视角分析 {candidate_name}（{normalized_ticker}）。"
            f"你只能给出保守动作：继续观察、接近可参与窗口、等待回踩确认、仅适合持有、暂不参与。"
            f"不要给绝对化结论，不构成买入指令。"
            f"请明确说明依据、缺失信息、失效条件，并区分买不了、卖不出和不该追。"
            f"优先关注中军龙头和强趋势核心票。"
            f"市场状态：{market_overview.get('market_state') or '未知'}；"
            f"情绪阶段：{emotion_cycle.get('cycle_stage') or '未知'}。"
            f"当前规则动作：{rule_based_judgement.get('action') or '继续观察'}；"
            f"题材：{(candidate or {}).get('topic_name') or '未知'}；"
            f"偏好模板：{preference_profile.get('template_title') or preference_profile.get('template_id') or '未知'}；"
            f"提醒：{alert_summary}"
            f" 持仓：{holding_text}"
            f" 风险：{risk_text}"
            f" 缺失信息：{missing_text}"
        )

    @staticmethod
    def _unique_list(values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            text = str(value or "").strip()
            if text and text not in seen:
                seen.add(text)
                result.append(text)
        return result


_ashare_decision_context_service: Optional[AShareDecisionContextService] = None


def get_ashare_decision_context_service() -> AShareDecisionContextService:
    global _ashare_decision_context_service
    if _ashare_decision_context_service is None:
        _ashare_decision_context_service = AShareDecisionContextService()
    return _ashare_decision_context_service


def reset_ashare_decision_context_service() -> None:
    global _ashare_decision_context_service
    _ashare_decision_context_service = None
