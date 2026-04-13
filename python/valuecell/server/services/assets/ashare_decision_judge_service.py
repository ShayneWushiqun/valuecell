from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional, Protocol

from .ashare_decision_context_service import AShareDecisionContextService
from .decision_alert_persistence_service import DecisionAlertPersistenceService

ALLOWED_ACTIONS = {
    "继续观察",
    "接近可参与窗口",
    "等待回踩确认",
    "仅适合持有",
    "暂不参与",
}
FORBIDDEN_TERMS = (
    "推荐买入",
    "最佳买点",
    "必涨",
    "直接买入",
    "立即买入",
    "满仓",
    "梭哈",
)
DEFAULT_TIME_HORIZON = "1-4周"
AGENT_UNAVAILABLE_REASON = (
    "当前仓库没有稳定、低风险、无需新增 API Key 的单次 JSON 裁决入口，"
    "本轮默认使用规则 fallback。"
)


class AShareDecisionAgentProvider(Protocol):
    def judge(self, *, prompt: str, context: dict[str, Any]) -> str: ...


class AShareDecisionJudgeService:
    def __init__(
        self,
        context_service: Optional[AShareDecisionContextService] = None,
        decision_alert_persistence_service: Optional[DecisionAlertPersistenceService] = None,
        agent_provider: Optional[AShareDecisionAgentProvider] = None,
    ) -> None:
        self.context_service = context_service or AShareDecisionContextService()
        self.decision_alert_persistence_service = (
            decision_alert_persistence_service or DecisionAlertPersistenceService()
        )
        self.agent_provider = agent_provider

    def judge(
        self,
        *,
        ticker: str,
        user_id: str = "default_user",
        enable_agent: bool = False,
        force_refresh_context: bool = False,
        user_note: str | None = None,
    ) -> dict[str, Any]:
        if force_refresh_context:
            self.decision_alert_persistence_service.refresh_alerts(user_id=user_id)

        context = self.context_service.get_decision_context(
            ticker=ticker,
            user_id=user_id,
        )
        rule_result = self._build_rule_fallback_result(
            context=context,
            enable_agent=enable_agent,
            user_note=user_note,
        )

        if not enable_agent or self.agent_provider is None:
            return rule_result

        raw_agent_output: str | None = None
        try:
            raw_agent_output = self.agent_provider.judge(
                prompt=str(context.get("agent_prompt_preview") or ""),
                context=context,
            )
        except Exception:
            return {
                **rule_result,
                "mode": "agent_fallback",
                "raw_agent_output": raw_agent_output,
            }

        agent_result = self._validate_agent_result(raw_agent_output)
        if agent_result is None:
            return {
                **rule_result,
                "mode": "agent_fallback",
                "raw_agent_output": raw_agent_output,
            }

        return {
            **rule_result,
            **agent_result,
            "mode": "agent",
            "agent_enabled": True,
            "agent_unavailable_reason": None,
            "raw_agent_output": raw_agent_output,
        }

    def _build_rule_fallback_result(
        self,
        *,
        context: dict[str, Any],
        enable_agent: bool,
        user_note: str | None,
    ) -> dict[str, Any]:
        available = bool(context.get("available"))
        candidate_context = context.get("candidate_context") or {}
        entry_timing_context = context.get("entry_timing_context") or {}
        portfolio_context = context.get("portfolio_context") or {}
        preference_context = context.get("preference_context") or {}
        risk_items = list((context.get("risk_context") or {}).get("items") or [])
        missing_context = list(context.get("missing_context") or [])
        rule_based_judgement = context.get("rule_based_judgement") or {}

        action = self._resolve_action(
            available=available,
            rule_based_action=str(rule_based_judgement.get("action") or ""),
            candidate_context=candidate_context,
            risk_items=risk_items,
            has_position=bool(portfolio_context.get("has_position")),
            missing_context=missing_context,
        )
        confidence = self._resolve_confidence(
            available=available,
            action=action,
            candidate_context=candidate_context,
            entry_timing_context=entry_timing_context,
            risk_items=risk_items,
            missing_context=missing_context,
        )
        evidence = self._build_evidence(
            context=context,
            user_note=user_note,
        )
        disagreement = self._build_disagreement(
            context=context,
            action=action,
        )
        missing_confirmations = self._build_missing_confirmations(
            context=context,
            available=available,
        )
        invalid_conditions = self._build_invalid_conditions(
            context=context,
            action=action,
        )
        risk_controls = self._build_risk_controls(
            context=context,
            action=action,
        )
        summary = self._build_summary(
            action=action,
            available=available,
            has_position=bool(portfolio_context.get("has_position")),
            context=context,
        )
        thesis = self._build_thesis(
            action=action,
            available=available,
            candidate_context=candidate_context,
            preference_context=preference_context,
        )

        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "ticker": context.get("ticker"),
            "available": available,
            "mode": "rule_fallback",
            "agent_enabled": False,
            "agent_unavailable_reason": AGENT_UNAVAILABLE_REASON,
            "action": action,
            "confidence": confidence,
            "summary": self._sanitize_text(summary),
            "thesis": self._sanitize_text(thesis),
            "evidence": self._sanitize_list(evidence),
            "disagreement": self._sanitize_list(disagreement),
            "missing_confirmations": self._sanitize_list(missing_confirmations),
            "invalid_conditions": self._sanitize_list(invalid_conditions),
            "risk_controls": self._sanitize_list(risk_controls),
            "time_horizon": DEFAULT_TIME_HORIZON,
            "context_snapshot": context,
            "raw_agent_output": None,
            "empty_message": None if available else context.get("empty_message"),
        }

    def _validate_agent_result(self, raw_output: str | None) -> dict[str, Any] | None:
        return None

    @staticmethod
    def _resolve_action(
        *,
        available: bool,
        rule_based_action: str,
        candidate_context: dict[str, Any],
        risk_items: list[str],
        has_position: bool,
        missing_context: list[str],
    ) -> str:
        risk_text = " ".join(risk_items)
        candidate_state = str(candidate_context.get("candidate_state") or "")
        tradeability_state = str(candidate_context.get("tradeability_state") or "")

        if not available:
            return "继续观察"
        if any(term in risk_text for term in ("流动性风险", "ST", "退潮", "走弱")):
            return "仅适合持有" if has_position else "暂不参与"
        if tradeability_state == "谨慎追高":
            return "仅适合持有" if has_position else "等待回踩确认"
        if candidate_state == "高优先级买点" and missing_context:
            return "接近可参与窗口"
        if rule_based_action in ALLOWED_ACTIONS:
            return rule_based_action
        if candidate_state in {"高优先级买点", "候选买点"}:
            return "接近可参与窗口"
        return "继续观察"

    @staticmethod
    def _resolve_confidence(
        *,
        available: bool,
        action: str,
        candidate_context: dict[str, Any],
        entry_timing_context: dict[str, Any],
        risk_items: list[str],
        missing_context: list[str],
    ) -> int:
        if not available:
            return 35

        score = 50
        priority_score = candidate_context.get("priority_score")
        if isinstance(priority_score, int):
            score += min(20, max(-10, int((priority_score - 50) / 4)))

        timing_confidence = entry_timing_context.get("confidence")
        if isinstance(timing_confidence, int):
            score += int((timing_confidence - 50) / 5)

        matched_preferences = list(candidate_context.get("matched_preferences") or [])
        score += min(8, len(matched_preferences) * 2)
        score -= min(20, len(risk_items) * 6)
        score -= min(18, len(missing_context) * 5)

        if action == "暂不参与":
            score = min(score, 48)
        elif action == "继续观察":
            score = min(score, 40)
        elif action == "仅适合持有":
            score = min(score, 58)
        elif action == "等待回踩确认":
            score = min(score, 64)

        return max(20, min(85, score))

    def _build_summary(
        self,
        *,
        action: str,
        available: bool,
        has_position: bool,
        context: dict[str, Any],
    ) -> str:
        if not available:
            return "当前上下文仍不完整，先继续观察，不构成买入指令。"
        candidate_context = context.get("candidate_context") or {}
        entry_timing_context = context.get("entry_timing_context") or {}
        topic_name = (context.get("theme_context") or {}).get("topic_name") or "当前方向"
        if action == "暂不参与":
            return f"{topic_name} 方向当前风险优先，先回避，等待条件改善后再评估。"
        if action == "仅适合持有":
            if has_position:
                return "当前更偏向持有观察，不适合把结论外推成新开仓动作。"
            return "当前位置不适合追价，更适合持有观察或继续确认。"
        if action == "等待回踩确认":
            return "当前仍需等待回踩、承接或情绪进一步确认，不适合直接追高。"
        if action == "接近可参与窗口":
            return (
                str(entry_timing_context.get("summary") or "")
                or "当前更接近可参与窗口，但仍需继续确认，不构成买入指令。"
            )
        if str(candidate_context.get("candidate_state") or "") == "高优先级买点":
            return "候选质量较高，但现阶段仍以继续观察和确认失效条件为主。"
        return "当前仍以继续观察为主，先确认题材、承接和可交易性。"

    @staticmethod
    def _build_thesis(
        *,
        action: str,
        available: bool,
        candidate_context: dict[str, Any],
        preference_context: dict[str, Any],
    ) -> str:
        if not available:
            return "当前缺少足够候选、买点或提醒上下文，尚不足以形成更明确裁决。"
        topic_name = str(candidate_context.get("topic_name") or "")
        candidate_state = str(candidate_context.get("candidate_state") or "")
        preference_title = str(preference_context.get("template_title") or "当前偏好")
        if action == "暂不参与":
            return "风险项和可交易性问题优先级高于题材强度，当前更适合先回避。"
        if action == "仅适合持有":
            return "个股逻辑未必失效，但当前位置与节奏更适合持有观察而不是追加动作。"
        if action == "等待回踩确认":
            return "题材和个股仍有跟踪价值，但需要更好的回踩或承接确认来降低节奏风险。"
        if action == "接近可参与窗口":
            return (
                f"{topic_name or '当前方向'} 仍处于可跟踪区间，且与 {preference_title} 偏好较匹配，"
                f"但当前判断仍停留在 {candidate_state or '观察'} 层。"
            )
        return "当前证据仍不足以推高动作强度，继续观察比提前下结论更稳妥。"

    def _build_evidence(
        self,
        *,
        context: dict[str, Any],
        user_note: str | None,
    ) -> list[str]:
        market_context = context.get("market_context") or {}
        theme_context = context.get("theme_context") or {}
        candidate_context = context.get("candidate_context") or {}
        entry_timing_context = context.get("entry_timing_context") or {}
        alert_context = context.get("alert_context") or {}
        preference_context = context.get("preference_context") or {}
        portfolio_context = context.get("portfolio_context") or {}

        evidence: list[str] = []
        if market_context.get("market_state"):
            evidence.append(
                f"市场状态为 {market_context['market_state']}，情绪阶段 {market_context.get('emotion_stage') or '待确认'}。"
            )
        if theme_context.get("topic_name"):
            evidence.append(
                f"题材为 {theme_context['topic_name']}，角色 {theme_context.get('role_label') or '待确认'}，趋势 {theme_context.get('trend_quality') or '待确认'}。"
            )
        if candidate_context.get("priority_score") is not None:
            evidence.append(
                f"机会池优先分 {candidate_context['priority_score']}，状态 {candidate_context.get('candidate_state') or '普通观察'}。"
            )
        if entry_timing_context.get("action"):
            evidence.append(
                f"买点裁决当前给出 {entry_timing_context['action']}，置信度 {entry_timing_context.get('confidence') or 0}。"
            )
        if alert_context.get("active_count"):
            evidence.append(f"当前已有 {alert_context['active_count']} 条 active 提醒可供回看。")
        if preference_context.get("template_title"):
            evidence.append(
                f"用户偏好模板为 {preference_context['template_title']}，买入风格 {preference_context.get('buy_style') or '待确认'}。"
            )
        if portfolio_context.get("has_position"):
            evidence.append(
                f"当前已有持仓摘要：{portfolio_context.get('summary') or '暂无摘要'}。"
            )
        note_text = self._sanitize_text(str(user_note or "").strip())
        if note_text:
            evidence.append(f"用户补充说明：{note_text}")
        return self._unique_list(evidence)

    @staticmethod
    def _build_disagreement(
        *,
        context: dict[str, Any],
        action: str,
    ) -> list[str]:
        candidate_context = context.get("candidate_context") or {}
        theme_context = context.get("theme_context") or {}
        entry_timing_context = context.get("entry_timing_context") or {}
        portfolio_context = context.get("portfolio_context") or {}
        disagreements: list[str] = []

        if (
            str(theme_context.get("trend_quality") or "") == "顺势"
            and str(candidate_context.get("tradeability_state") or "") == "谨慎追高"
        ):
            disagreements.append("题材和趋势偏强，但个股当前位置偏追高，节奏不理想。")
        if (
            str(candidate_context.get("candidate_state") or "") == "高优先级买点"
            and list(entry_timing_context.get("missing_confirmations") or [])
        ):
            disagreements.append("候选排序较高，但仍缺少承接或回踩确认。")
        if portfolio_context.get("has_position") and action in {"接近可参与窗口", "等待回踩确认"}:
            disagreements.append("已有持仓可继续观察，但不代表新开仓也适合同样节奏。")
        if not disagreements:
            disagreements.append("当前主要矛盾集中在确认强度不足，而不是方向完全失效。")
        return disagreements

    @staticmethod
    def _build_missing_confirmations(
        *,
        context: dict[str, Any],
        available: bool,
    ) -> list[str]:
        if not available:
            return list(context.get("missing_context") or [])
        entry_timing_context = context.get("entry_timing_context") or {}
        candidate_context = context.get("candidate_context") or {}
        missing_confirmations = list(entry_timing_context.get("missing_confirmations") or [])
        if not missing_confirmations:
            missing_confirmations = list(candidate_context.get("reasons") or [])[:1]
        if not missing_confirmations:
            missing_confirmations = ["仍需确认承接、量价或情绪是否继续配合。"]
        return AShareDecisionJudgeService._unique_list(missing_confirmations)

    @staticmethod
    def _build_invalid_conditions(
        *,
        context: dict[str, Any],
        action: str,
    ) -> list[str]:
        entry_timing_context = context.get("entry_timing_context") or {}
        candidate_context = context.get("candidate_context") or {}
        invalid_conditions = list(entry_timing_context.get("invalid_conditions") or [])
        invalid_conditions.extend(list(candidate_context.get("invalid_conditions") or []))
        if action in {"接近可参与窗口", "等待回踩确认"}:
            invalid_conditions.append("若承接转弱、量价失真或情绪退潮，当前判断立即失效。")
        if action == "仅适合持有":
            invalid_conditions.append("若已有仓位也失去承接或趋势转弱，应优先收缩风险。")
        if not invalid_conditions:
            invalid_conditions.append("若市场温度快速回落或题材失去持续性，当前观察结论失效。")
        return AShareDecisionJudgeService._unique_list(invalid_conditions)

    @staticmethod
    def _build_risk_controls(
        *,
        context: dict[str, Any],
        action: str,
    ) -> list[str]:
        risk_context = context.get("risk_context") or {}
        portfolio_context = context.get("portfolio_context") or {}
        controls = [
            "不追高，不把当前裁决外推成直接参与指令。",
            "先确认流动性与承接，避免出现涨停买不进或跌停卖不出的被动情况。",
        ]
        if action in {"接近可参与窗口", "等待回踩确认"}:
            controls.append("若无法获得更优回踩或承接确认，宁可继续观察。")
        if portfolio_context.get("has_position"):
            controls.append("已有持仓时优先看减风险与持有节奏，不把持仓观察等同于新开仓。")
        for item in list(risk_context.get("items") or [])[:2]:
            controls.append(str(item))
        return AShareDecisionJudgeService._unique_list(controls)[:5]

    @staticmethod
    def _sanitize_text(text: str) -> str:
        result = str(text or "").strip()
        for term in FORBIDDEN_TERMS:
            result = result.replace(term, "保守观察")
        return result

    @classmethod
    def _sanitize_list(cls, values: list[str]) -> list[str]:
        return [cls._sanitize_text(value) for value in values if cls._sanitize_text(value)]

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


_ashare_decision_judge_service: Optional[AShareDecisionJudgeService] = None


def get_ashare_decision_judge_service() -> AShareDecisionJudgeService:
    global _ashare_decision_judge_service
    if _ashare_decision_judge_service is None:
        _ashare_decision_judge_service = AShareDecisionJudgeService()
    return _ashare_decision_judge_service


def reset_ashare_decision_judge_service() -> None:
    global _ashare_decision_judge_service
    _ashare_decision_judge_service = None
