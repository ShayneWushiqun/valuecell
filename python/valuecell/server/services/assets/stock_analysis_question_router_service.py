from __future__ import annotations

import re
from typing import Any, Optional, Sequence

from ...api.schemas.stock_analysis_question_router import (
    StockAnalysisQuestionRoutingData,
)


def _clean_text(value: Any, *, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def _contains_any(text: str, patterns: Sequence[str]) -> bool:
    return any(pattern in text for pattern in patterns)


def _unique_list(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = _clean_text(value)
        if text and text not in result:
            result.append(text)
    return result


class StockAnalysisQuestionRouterService:
    def route_question(
        self,
        *,
        thread: dict[str, Any],
        context_cards: Sequence[dict[str, Any]],
        active_memory: dict[str, Any] | None,
        active_compression: dict[str, Any] | None,
        conversation_history: Sequence[dict[str, Any]],
        user_message: str,
        force_tooling: bool = False,
        refresh_before_answer: bool = False,
    ) -> StockAnalysisQuestionRoutingData:
        message = _clean_text(user_message)
        lowered = message.lower()
        compare_targets = list(thread.get("compare_targets_json") or [])
        stale_contexts = [
            item
            for item in context_cards
            if bool(item.get("is_stale")) or bool(item.get("refresh_recommended"))
        ]
        has_compare_targets = len(compare_targets) >= 2
        has_active_memory = active_memory is not None
        has_active_compression = active_compression is not None

        question_intent = self._detect_intent(
            message=message,
            lowered=lowered,
            has_compare_targets=has_compare_targets,
        )
        response_strategy = self._resolve_strategy(
            question_intent=question_intent,
            has_compare_targets=has_compare_targets,
            has_stale_contexts=bool(stale_contexts),
            force_tooling=force_tooling,
            refresh_before_answer=refresh_before_answer,
        )
        followup_candidates = self._build_followups(
            question_intent=question_intent,
            compare_targets=compare_targets,
            stale_contexts=stale_contexts,
            active_memory=active_memory,
            active_compression=active_compression,
        )
        suggested_task_titles = self._build_suggested_task_titles(
            question_intent=question_intent,
            compare_targets=compare_targets,
            stale_contexts=stale_contexts,
            active_memory=active_memory,
            active_compression=active_compression,
            conversation_history=conversation_history,
        )
        should_focus_compare_targets = has_compare_targets and question_intent in {
            "compare_targets",
            "challenge_conclusion",
            "update_thesis",
            "define_next_step",
        }
        should_revisit_active_memory = has_active_memory and question_intent in {
            "explain_reasoning",
            "challenge_conclusion",
            "update_thesis",
            "define_next_step",
        }
        should_revisit_active_compression = has_active_compression and question_intent in {
            "summarize_context",
            "challenge_conclusion",
            "define_next_step",
            "general_followup",
        }
        routing_reason = self._build_routing_reason(
            question_intent=question_intent,
            response_strategy=response_strategy,
            has_compare_targets=has_compare_targets,
            stale_contexts=stale_contexts,
            force_tooling=force_tooling,
            refresh_before_answer=refresh_before_answer,
        )
        recommended_next_action = self._build_recommended_action(
            response_strategy=response_strategy,
            question_intent=question_intent,
            stale_contexts=stale_contexts,
            has_compare_targets=has_compare_targets,
        )
        return StockAnalysisQuestionRoutingData(
            question_intent=question_intent,
            response_strategy=response_strategy,
            routing_reason=routing_reason,
            recommended_next_action=recommended_next_action,
            followup_candidates=followup_candidates,
            suggested_task_titles=suggested_task_titles,
            should_focus_compare_targets=should_focus_compare_targets,
            should_revisit_active_memory=should_revisit_active_memory,
            should_revisit_active_compression=should_revisit_active_compression,
        )

    @staticmethod
    def _detect_intent(
        *,
        message: str,
        lowered: str,
        has_compare_targets: bool,
    ) -> str:
        if _contains_any(message, ["总结", "梳理", "回顾", "概括", "摘要"]):
            return "summarize_context"
        if _contains_any(message, ["重新判断", "重做判断", "更新观点", "改判", "修正结论", "重估"]):
            return "update_thesis"
        if _contains_any(message, ["为什么", "依据", "逻辑", "原因", "怎么得出", "凭什么"]):
            return "explain_reasoning"
        if has_compare_targets and _contains_any(
            message,
            ["比较", "对比", "谁更", "哪个更", "优先级", "强弱", "胜率"],
        ):
            return "compare_targets"
        if _contains_any(message, ["刷新", "更新一下", "过期", "最新状态", "重新看", "旧了没"]):
            return "refresh_state_check"
        if _contains_any(
            message,
            ["补数据", "查一下", "公告", "新闻", "外部", "财报", "证据", "成交", "验证一下"],
        ):
            return "external_evidence_check"
        if _contains_any(message, ["不对", "不认同", "质疑", "站不住", "靠谱吗", "有问题", "你错"]):
            return "challenge_conclusion"
        if _contains_any(message, ["下一步", "接下来", "研究计划", "待办", "还要看什么", "下一阶段"]):
            return "define_next_step"
        if _contains_any(message, ["缺什么", "信息不足", "上下文不够", "还差什么", "需要哪些"]):
            return "context_gap"
        if has_compare_targets and re.search(r"(谁|哪个).*(更|优先)", lowered):
            return "compare_targets"
        return "general_followup"

    @staticmethod
    def _resolve_strategy(
        *,
        question_intent: str,
        has_compare_targets: bool,
        has_stale_contexts: bool,
        force_tooling: bool,
        refresh_before_answer: bool,
    ) -> str:
        if refresh_before_answer:
            return "refresh_then_answer"
        if force_tooling:
            return "tooling_then_answer"
        if question_intent == "compare_targets":
            return "answer_with_compare_focus" if has_compare_targets else "highlight_context_gap"
        if question_intent == "refresh_state_check":
            return "refresh_then_answer" if has_stale_contexts else "answer_from_context"
        if question_intent == "external_evidence_check":
            return "tooling_then_answer"
        if question_intent in {"challenge_conclusion", "update_thesis"}:
            return "restate_and_recheck"
        if question_intent == "define_next_step":
            return "suggest_research_tasks"
        if question_intent == "context_gap":
            return "highlight_context_gap"
        return "answer_from_context"

    @staticmethod
    def _build_followups(
        *,
        question_intent: str,
        compare_targets: Sequence[dict[str, Any]],
        stale_contexts: Sequence[dict[str, Any]],
        active_memory: dict[str, Any] | None,
        active_compression: dict[str, Any] | None,
    ) -> list[str]:
        candidates: list[str] = []
        if question_intent == "compare_targets" and len(compare_targets) >= 2:
            labels = [
                _clean_text(item.get("label") or item.get("ref")) for item in compare_targets[:3]
            ]
            candidates.append(f"明确 {' / '.join(labels)} 的主次和触发条件")
        if stale_contexts:
            candidates.append("刷新关键上下文后再复核当前判断")
        if active_memory:
            candidates.extend(list(active_memory.get("next_questions_json") or [])[:2])
        if active_compression:
            candidates.extend(list(active_compression.get("open_questions_json") or [])[:2])
        if question_intent == "define_next_step":
            candidates.append("从当前线程生成显式研究任务")
        return _unique_list(candidates)[:5]

    @staticmethod
    def _build_suggested_task_titles(
        *,
        question_intent: str,
        compare_targets: Sequence[dict[str, Any]],
        stale_contexts: Sequence[dict[str, Any]],
        active_memory: dict[str, Any] | None,
        active_compression: dict[str, Any] | None,
        conversation_history: Sequence[dict[str, Any]],
    ) -> list[str]:
        titles: list[str] = []
        if len(compare_targets) >= 2:
            labels = [
                _clean_text(item.get("label") or item.get("ref"))
                for item in compare_targets[:2]
            ]
            if all(labels):
                titles.append(f"补充比较：{labels[0]} vs {labels[1]} 的优先级确认")
        if stale_contexts:
            stale_title = _clean_text(stale_contexts[0].get("title"), fallback="关键上下文")
            titles.append(f"刷新 {stale_title} 后重看当前结论")
        if active_memory:
            titles.extend(list(active_memory.get("next_questions_json") or [])[:2])
        if active_compression:
            titles.extend(list(active_compression.get("open_questions_json") or [])[:2])
        if question_intent in {"challenge_conclusion", "update_thesis"}:
            titles.append("重验当前 thesis 与关键反例")
        if question_intent == "define_next_step":
            titles.append("梳理当前线程的下一步研究清单")
        latest_assistant = next(
            (
                item
                for item in reversed(list(conversation_history))
                if "assistant" in _clean_text(item.get("role")).lower()
                or "agent" in _clean_text(item.get("role")).lower()
            ),
            None,
        )
        if latest_assistant:
            titles.extend(list(latest_assistant.get("suggested_task_titles") or [])[:2])
        return _unique_list(titles)[:5]

    @staticmethod
    def _build_routing_reason(
        *,
        question_intent: str,
        response_strategy: str,
        has_compare_targets: bool,
        stale_contexts: Sequence[dict[str, Any]],
        force_tooling: bool,
        refresh_before_answer: bool,
    ) -> str:
        reasons: list[str] = [f"识别为 {question_intent}"]
        if has_compare_targets:
            reasons.append("线程已存在显式 compare targets")
        if stale_contexts:
            reasons.append("当前线程存在 stale/建议刷新的上下文")
        if force_tooling:
            reasons.append("用户显式要求先补数据")
        if refresh_before_answer:
            reasons.append("用户显式要求先刷新再回答")
        reasons.append(f"因此采用 {response_strategy}")
        return "；".join(reasons)

    @staticmethod
    def _build_recommended_action(
        *,
        response_strategy: str,
        question_intent: str,
        stale_contexts: Sequence[dict[str, Any]],
        has_compare_targets: bool,
    ) -> str:
        if response_strategy == "refresh_then_answer":
            if stale_contexts:
                stale_title = _clean_text(stale_contexts[0].get("title"), fallback="关键上下文")
                return f"先刷新 {stale_title} 等关键卡片，再回到当前问题。"
            return "先基于现有上下文确认刷新必要性，再给出更新判断。"
        if response_strategy == "tooling_then_answer":
            return "先补充最新外部或行情证据，再回答当前问题。"
        if response_strategy == "restate_and_recheck":
            return "先重述当前 thesis 和反例，再逐项复核。"
        if response_strategy == "highlight_context_gap":
            return "先补齐显式上下文卡片或刷新过期卡片，再继续追问。"
        if response_strategy == "answer_with_compare_focus" and has_compare_targets:
            return "围绕 compare targets 给出主次、依据和失效条件。"
        if question_intent == "define_next_step":
            return "把下一步研究问题显式加入 research tasks。"
        return "先基于当前显式上下文直接回答，并保留下一步建议。"


_stock_analysis_question_router_service: Optional[
    StockAnalysisQuestionRouterService
] = None


def get_stock_analysis_question_router_service() -> (
    StockAnalysisQuestionRouterService
):
    global _stock_analysis_question_router_service
    if _stock_analysis_question_router_service is None:
        _stock_analysis_question_router_service = StockAnalysisQuestionRouterService()
    return _stock_analysis_question_router_service


def reset_stock_analysis_question_router_service() -> None:
    global _stock_analysis_question_router_service
    _stock_analysis_question_router_service = None
