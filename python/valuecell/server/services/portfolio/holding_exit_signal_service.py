from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional

from ..assets.ashare_decision_context_service import AShareDecisionContextService
from ..assets.ashare_decision_judge_service import AShareDecisionJudgeService
from .diagnosis_service import HoldingDiagnosisService
from .holding_service import HoldingService

ALLOWED_EXIT_ACTIONS = {
    "继续持有",
    "持有观察",
    "减仓观察",
    "保护利润",
    "纪律止损",
}


class HoldingExitSignalService:
    def __init__(
        self,
        holding_service: Optional[HoldingService] = None,
        holding_diagnosis_service: Optional[HoldingDiagnosisService] = None,
        decision_context_service: Optional[AShareDecisionContextService] = None,
        decision_judge_service: Optional[AShareDecisionJudgeService] = None,
    ) -> None:
        self.holding_service = holding_service or HoldingService()
        self.holding_diagnosis_service = (
            holding_diagnosis_service or HoldingDiagnosisService()
        )
        self.decision_context_service = (
            decision_context_service or AShareDecisionContextService()
        )
        self.decision_judge_service = decision_judge_service or AShareDecisionJudgeService()

    def list_exit_signals(self, user_id: str = "default_user") -> dict[str, Any]:
        holdings = self.holding_service.list_holdings(user_id)
        items = [
            self._build_exit_signal_from_holding(holding=holding, user_id=user_id)
            for holding in holdings
        ]
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "items": items,
            "count": len(items),
        }

    def get_exit_signal(
        self,
        *,
        user_id: str,
        holding_id: int,
        force_refresh: bool = False,
    ) -> dict[str, Any] | None:
        if force_refresh:
            self.holding_diagnosis_service.refresh_latest_diagnosis(user_id, holding_id)
        holding = self.holding_service.get_holding(user_id, holding_id)
        if holding is None:
            return None
        return self._build_exit_signal_from_holding(holding=holding, user_id=user_id)

    def _build_exit_signal_from_holding(
        self,
        *,
        holding: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        holding_id = int(holding["id"])
        ticker = str(holding.get("ticker") or "")
        asset_name = holding.get("asset_name") or ticker
        latest_diagnosis = holding.get("latest_diagnosis") or {}
        market_snapshot = holding.get("market_snapshot") or {}
        profit_percent = self._to_float(market_snapshot.get("profit_percent"))
        latest_change_percent = self._to_float(market_snapshot.get("latest_change_percent"))

        decision_context = self.decision_context_service.get_decision_context(
            ticker=ticker,
            user_id=user_id,
        )
        decision_judge = self.decision_judge_service.judge(
            ticker=ticker,
            user_id=user_id,
            enable_agent=False,
            force_refresh_context=False,
            user_note=None,
        )

        candidate_context = decision_context.get("candidate_context") or {}
        theme_context = decision_context.get("theme_context") or {}
        preference_context = decision_context.get("preference_context") or {}
        risk_context = decision_context.get("risk_context") or {}
        buy_side_action = str(decision_judge.get("action") or "")
        risk_items = list(risk_context.get("items") or [])
        invalid_conditions = self._unique_list(
            list(decision_judge.get("invalid_conditions") or [])
            + list(latest_diagnosis.get("invalid_conditions") or [])
        )
        role_label = str(theme_context.get("role_label") or "")
        trend_quality = str(theme_context.get("trend_quality") or "")
        tradeability_state = str(candidate_context.get("tradeability_state") or "")
        risk_style = str(preference_context.get("risk_style") or "balanced")
        diagnosis_action = str(latest_diagnosis.get("action") or "")
        diagnosis_risk = str(latest_diagnosis.get("risk_level") or "")

        action = self._resolve_action(
            available=True,
            profit_percent=profit_percent,
            latest_change_percent=latest_change_percent,
            buy_side_action=buy_side_action,
            role_label=role_label,
            trend_quality=trend_quality,
            tradeability_state=tradeability_state,
            risk_style=risk_style,
            risk_items=risk_items,
            invalid_conditions=invalid_conditions,
            diagnosis_action=diagnosis_action,
            diagnosis_risk=diagnosis_risk,
        )
        confidence = self._resolve_confidence(
            action=action,
            profit_percent=profit_percent,
            latest_change_percent=latest_change_percent,
            risk_items=risk_items,
            invalid_conditions=invalid_conditions,
            role_label=role_label,
            risk_style=risk_style,
        )
        evidence = self._build_evidence(
            holding=holding,
            decision_context=decision_context,
            decision_judge=decision_judge,
            profit_percent=profit_percent,
            latest_change_percent=latest_change_percent,
        )
        disagreement = self._build_disagreement(
            action=action,
            role_label=role_label,
            tradeability_state=tradeability_state,
            trend_quality=trend_quality,
            buy_side_action=buy_side_action,
            profit_percent=profit_percent,
        )
        risk_controls = self._build_risk_controls(
            action=action,
            risk_items=risk_items,
            latest_change_percent=latest_change_percent,
            role_label=role_label,
        )
        profit_protection_view = self._build_profit_protection_view(
            action=action,
            profit_percent=profit_percent,
            tradeability_state=tradeability_state,
            risk_style=risk_style,
        )
        summary = self._build_summary(
            action=action,
            asset_name=str(asset_name),
            profit_percent=profit_percent,
            role_label=role_label,
        )
        thesis = self._build_thesis(
            action=action,
            role_label=role_label,
            trend_quality=trend_quality,
            risk_style=risk_style,
            profit_percent=profit_percent,
        )

        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "holding_id": holding_id,
            "ticker": ticker,
            "asset_name": asset_name,
            "available": True,
            "action": action,
            "confidence": confidence,
            "summary": summary,
            "thesis": thesis,
            "evidence": evidence,
            "disagreement": disagreement,
            "invalid_conditions": self._ensure_default_invalid_conditions(
                invalid_conditions=invalid_conditions,
                action=action,
            ),
            "risk_controls": risk_controls,
            "profit_protection_view": profit_protection_view,
            "time_horizon": "1-4周",
            "context_snapshot": {
                "holding": holding,
                "decision_context": decision_context,
                "decision_judge": decision_judge,
            },
            "empty_message": None,
        }

    @staticmethod
    def _resolve_action(
        *,
        available: bool,
        profit_percent: float | None,
        latest_change_percent: float | None,
        buy_side_action: str,
        role_label: str,
        trend_quality: str,
        tradeability_state: str,
        risk_style: str,
        risk_items: list[str],
        invalid_conditions: list[str],
        diagnosis_action: str,
        diagnosis_risk: str,
    ) -> str:
        if not available:
            return "持有观察"

        risk_text = " ".join(risk_items + invalid_conditions)
        is_leader_or_core = role_label in {"龙头", "中军"}
        strong_risk = any(term in risk_text for term in ("ST", "流动性风险", "退潮", "走弱"))
        extreme_drop = latest_change_percent is not None and latest_change_percent <= -6
        weak_ticket = not is_leader_or_core and (
            trend_quality == "走弱" or buy_side_action == "暂不参与"
        )

        if strong_risk and (weak_ticket or extreme_drop or diagnosis_risk == "高"):
            return "纪律止损"

        if (
            profit_percent is not None
            and profit_percent >= 10
            and (
                tradeability_state == "谨慎追高"
                or buy_side_action in {"暂不参与", "等待回踩确认"}
                or strong_risk
            )
        ):
            return "保护利润"

        if (
            strong_risk
            or trend_quality == "走弱"
            or buy_side_action == "暂不参与"
            or diagnosis_action == "减仓"
        ):
            if is_leader_or_core and not extreme_drop and diagnosis_risk != "高":
                return "减仓观察"
            return "减仓观察"

        if tradeability_state == "谨慎追高" or buy_side_action == "等待回踩确认":
            return "持有观察"

        if risk_style == "steady" and profit_percent is not None and profit_percent >= 6:
            return "保护利润"

        if is_leader_or_core and trend_quality != "走弱" and not strong_risk:
            return "继续持有"

        return "持有观察"

    @staticmethod
    def _resolve_confidence(
        *,
        action: str,
        profit_percent: float | None,
        latest_change_percent: float | None,
        risk_items: list[str],
        invalid_conditions: list[str],
        role_label: str,
        risk_style: str,
    ) -> int:
        score = 55
        if profit_percent is not None:
            score += min(10, max(-10, int(profit_percent / 3)))
        if latest_change_percent is not None and latest_change_percent < 0:
            score += max(-10, int(latest_change_percent))
        score -= min(18, len(risk_items) * 5)
        score -= min(12, len(invalid_conditions) * 4)
        if role_label in {"龙头", "中军"}:
            score += 4
        if risk_style == "steady":
            score += 2

        if action == "纪律止损":
            score = min(score, 74)
        elif action == "保护利润":
            score = min(score, 72)
        elif action == "减仓观察":
            score = min(score, 68)
        elif action == "持有观察":
            score = min(score, 60)

        return max(20, min(85, score))

    @classmethod
    def _build_evidence(
        cls,
        *,
        holding: dict[str, Any],
        decision_context: dict[str, Any],
        decision_judge: dict[str, Any],
        profit_percent: float | None,
        latest_change_percent: float | None,
    ) -> list[str]:
        candidate_context = decision_context.get("candidate_context") or {}
        theme_context = decision_context.get("theme_context") or {}
        portfolio_context = decision_context.get("portfolio_context") or {}
        evidence: list[str] = [
            "当前判断为持仓处理建议，不等于新开仓建议。",
        ]
        if holding.get("asset_name") or holding.get("ticker"):
            evidence.append(
                f"持仓标的为 {holding.get('asset_name') or holding.get('ticker')}，当前已有仓位。"
            )
        if profit_percent is not None:
            evidence.append(f"当前浮盈亏约 {profit_percent:.2f}%。")
        if latest_change_percent is not None:
            evidence.append(f"最近单日变动约 {latest_change_percent:.2f}%。")
        if theme_context.get("topic_name"):
            evidence.append(
                f"所属题材为 {theme_context.get('topic_name')}，角色 {theme_context.get('role_label') or '待确认'}。"
            )
        if candidate_context.get("candidate_state"):
            evidence.append(
                f"机会池状态为 {candidate_context.get('candidate_state')}，可交易状态 {candidate_context.get('tradeability_state') or '待确认'}。"
            )
        if decision_judge.get("summary"):
            evidence.append(f"买入侧规则裁决提示：{decision_judge.get('summary')}")
        if portfolio_context.get("summary"):
            evidence.append(f"阶段一持仓诊断摘要：{portfolio_context.get('summary')}")
        return cls._unique_list(evidence)

    @classmethod
    def _build_disagreement(
        cls,
        *,
        action: str,
        role_label: str,
        tradeability_state: str,
        trend_quality: str,
        buy_side_action: str,
        profit_percent: float | None,
    ) -> list[str]:
        disagreements: list[str] = []
        if role_label in {"龙头", "中军"} and trend_quality != "走弱" and action != "继续持有":
            disagreements.append("龙头/中军仍有一定容错，但当前风险信号要求更偏防守。")
        if tradeability_state == "谨慎追高":
            disagreements.append("个股节奏偏追高，持有可继续观察，但不适合把判断外推成加仓。")
        if profit_percent is not None and profit_percent > 0 and buy_side_action == "暂不参与":
            disagreements.append("已有浮盈可以继续做利润管理，但买入侧并不支持新开仓。")
        if not disagreements:
            disagreements.append("当前主要矛盾在于节奏与风险管理，而不是简单判断方向对错。")
        return cls._unique_list(disagreements)

    @classmethod
    def _build_risk_controls(
        cls,
        *,
        action: str,
        risk_items: list[str],
        latest_change_percent: float | None,
        role_label: str,
    ) -> list[str]:
        controls = [
            "持仓处理建议不构成交易指令，优先收缩风险而不是放大动作。",
            "先确认流动性与盘口承接，避免跌停卖不出或流动性差导致被动。",  # noqa: E501
        ]
        if action in {"保护利润", "减仓观察", "纪律止损"}:
            controls.append("若次日继续转弱或承接明显消失，应进一步降低风险暴露。")
        if latest_change_percent is not None and latest_change_percent < -5:
            controls.append("若短期跌幅继续扩大，应优先控制回撤，不做情绪化加仓。")
        if role_label not in {"龙头", "中军"}:
            controls.append("跟风或弱票容错更低，不宜因为短反抽就忽略风险。")
        controls.extend(risk_items[:2])
        return cls._unique_list(controls)[:5]

    @staticmethod
    def _build_profit_protection_view(
        *,
        action: str,
        profit_percent: float | None,
        tradeability_state: str,
        risk_style: str,
    ) -> str:
        if profit_percent is None:
            return "当前缺少明确浮盈亏数据，利润保护判断以保守观察为主。"
        if action == "保护利润":
            return "当前已有一定浮盈，优先考虑保护利润回撤，而不是继续放大波动暴露。"
        if action == "纪律止损":
            return "当前更重要的是避免逻辑破坏后的进一步回撤，利润保护优先级让位于纪律退出。"
        if tradeability_state == "谨慎追高":
            return "即使仍有利润空间，也不宜把持仓盈利当成继续追高的理由。"
        if risk_style == "steady":
            return "稳健风格下，持仓可优先以利润保护和回撤控制为核心。"
        return "当前可继续持有观察，但仍应提前设定利润回撤和风险收缩边界。"

    @staticmethod
    def _build_summary(
        *,
        action: str,
        asset_name: str,
        profit_percent: float | None,
        role_label: str,
    ) -> str:
        if action == "继续持有":
            return f"{asset_name} 当前逻辑未见明显破坏，节奏仍允许继续持有，但不等于新开仓建议。"
        if action == "持有观察":
            return f"{asset_name} 当前更适合持有观察，先看承接和节奏，不急于加仓或减仓。"
        if action == "减仓观察":
            return f"{asset_name} 当前强度或节奏边际转弱，优先收缩部分风险后继续观察。"
        if action == "保护利润":
            profit_text = f"当前浮盈约 {profit_percent:.2f}%，" if profit_percent is not None else ""
            return f"{profit_text}{asset_name} 更适合以保护利润为主，防止收益明显回撤。"
        tolerance = "即使是龙头/中军也要尊重失效条件。" if role_label in {"龙头", "中军"} else ""
        return f"{asset_name} 当前更偏向纪律止损视角，优先控制逻辑失效后的进一步风险。{tolerance}"

    @staticmethod
    def _build_thesis(
        *,
        action: str,
        role_label: str,
        trend_quality: str,
        risk_style: str,
        profit_percent: float | None,
    ) -> str:
        if action == "继续持有":
            return "题材、趋势和持仓节奏暂未明显失衡，当前更适合继续拿而不是提前打断。"
        if action == "持有观察":
            return "逻辑并未明显破坏，但确认强度不够，持仓侧以观察优先于加速动作。"
        if action == "减仓观察":
            return "风险与节奏开始偏向防守，先减部分风险暴露，再观察是否重新稳定。"
        if action == "保护利润":
            return (
                f"当前已有{profit_percent:.2f}%浮盈，" if profit_percent is not None else ""
            ) + "优先守住已有收益，比继续博弈更符合当前风控目标。"
        role_note = "龙头/中军也不能无脑死扛。" if role_label in {"龙头", "中军"} else ""
        style_note = "稳健风格下应更快收缩风险。" if risk_style == "steady" else ""
        trend_note = "题材或趋势走弱已削弱继续持有的理由。" if trend_quality == "走弱" else ""
        return f"{trend_note}{role_note}{style_note}".strip() or "当前失效条件和风险项已经明显抬升，应优先纪律化处理。"

    @staticmethod
    def _ensure_default_invalid_conditions(
        *,
        invalid_conditions: list[str],
        action: str,
    ) -> list[str]:
        if invalid_conditions:
            return HoldingExitSignalService._unique_list(invalid_conditions)
        default = {
            "继续持有": "若承接转弱、题材退潮或风险项快速增加，继续持有判断失效。",
            "持有观察": "若确认条件继续缺失或风险项增多，持有观察应降级为减仓观察。",
            "减仓观察": "若减仓后仍持续走弱，应进一步收缩风险。",
            "保护利润": "若利润回撤明显扩大或无法确认承接，应继续偏防守处理。",
            "纪律止损": "若风险条件缓解并重新获得确认，再评估是否恢复观察。",
        }
        return [default.get(action, "若风险项继续恶化，当前判断失效。")]

    @staticmethod
    def _to_float(value: Any) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

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


_holding_exit_signal_service: Optional[HoldingExitSignalService] = None


def get_holding_exit_signal_service() -> HoldingExitSignalService:
    global _holding_exit_signal_service
    if _holding_exit_signal_service is None:
        _holding_exit_signal_service = HoldingExitSignalService()
    return _holding_exit_signal_service


def reset_holding_exit_signal_service() -> None:
    global _holding_exit_signal_service
    _holding_exit_signal_service = None
