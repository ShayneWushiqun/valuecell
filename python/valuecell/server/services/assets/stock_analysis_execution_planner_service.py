from __future__ import annotations

import uuid
from typing import Any, Optional, Sequence

from ...api.schemas.stock_analysis_execution_plan import (
    StockAnalysisExecutionPlanData,
    StockAnalysisExecutionStepData,
    StockAnalysisTaskUpdateSuggestionData,
    StockAnalysisValidationSummaryData,
)

STEP_ORDER = [
    "inspect_context_cards",
    "inspect_compare_targets",
    "inspect_active_memory",
    "inspect_active_compression",
    "inspect_open_tasks",
    "refresh_stale_contexts",
    "collect_internal_structured_evidence",
    "collect_market_price_evidence",
    "collect_external_evidence",
    "validate_thesis",
    "synthesize_answer",
    "suggest_task_updates",
]


def _clean_text(value: Any, *, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def _unique_str_list(values: Sequence[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = _clean_text(value)
        if text and text not in result:
            result.append(text)
    return result


def _unique_int_list(values: Sequence[Any]) -> list[int]:
    result: list[int] = []
    for value in values:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            continue
        if parsed > 0 and parsed not in result:
            result.append(parsed)
    return result


class StockAnalysisExecutionPlannerService:
    def build_execution_plan(
        self,
        *,
        thread: dict[str, Any],
        context_cards: Sequence[dict[str, Any]],
        active_memory: dict[str, Any] | None,
        active_compression: dict[str, Any] | None,
        open_tasks: Sequence[dict[str, Any]],
        question_routing: dict[str, Any],
        user_message: str,
        force_tooling: bool = False,
        refresh_before_answer: bool = False,
        research_task: dict[str, Any] | None = None,
    ) -> StockAnalysisExecutionPlanData:
        compare_targets = list(thread.get("compare_targets_json") or [])
        primary_compare_targets = [
            _clean_text(item.get("label") or item.get("ref"))
            for item in compare_targets[:2]
            if _clean_text(item.get("label") or item.get("ref"))
        ]
        stale_contexts = [
            item
            for item in context_cards
            if bool(item.get("is_stale")) or bool(item.get("refresh_recommended"))
        ]
        focus_tickers = self._build_focus_tickers(
            thread=thread,
            context_cards=context_cards,
            research_task=research_task,
            compare_targets=compare_targets,
        )
        focus_themes = self._build_focus_themes(
            thread=thread,
            context_cards=context_cards,
            research_task=research_task,
        )
        related_tasks = self._match_related_tasks(
            open_tasks=open_tasks,
            user_message=user_message,
            focus_tickers=focus_tickers,
            focus_themes=focus_themes,
            question_routing=question_routing,
            research_task=research_task,
        )
        related_task_ids = [int(item.get("task_id") or 0) for item in related_tasks]
        requires_refresh = refresh_before_answer or bool(stale_contexts)
        requires_tooling = force_tooling or (
            _clean_text(question_routing.get("response_strategy"))
            in {"tooling_then_answer", "restate_and_recheck"}
        ) or (
            _clean_text(question_routing.get("question_intent"))
            in {"external_evidence_check", "challenge_conclusion", "update_thesis"}
        )
        requires_validation = _clean_text(question_routing.get("question_intent")) in {
            "compare_targets",
            "challenge_conclusion",
            "update_thesis",
            "define_next_step",
            "explain_reasoning",
        } or bool(related_task_ids)
        steps = self._build_plan_steps(
            question_routing=question_routing,
            context_cards=context_cards,
            active_memory=active_memory,
            active_compression=active_compression,
            open_tasks=open_tasks,
            related_task_ids=related_task_ids,
            primary_compare_targets=primary_compare_targets,
            focus_tickers=focus_tickers,
            focus_themes=focus_themes,
            requires_refresh=requires_refresh,
            requires_tooling=requires_tooling,
            requires_validation=requires_validation,
        )
        plan_summary = self._build_plan_summary(
            question_routing=question_routing,
            requires_refresh=requires_refresh,
            requires_tooling=requires_tooling,
            requires_validation=requires_validation,
            related_task_ids=related_task_ids,
            primary_compare_targets=primary_compare_targets,
        )
        planning_reason = self._build_planning_reason(
            question_routing=question_routing,
            stale_contexts=stale_contexts,
            related_task_ids=related_task_ids,
            research_task=research_task,
            requires_tooling=requires_tooling,
        )
        return StockAnalysisExecutionPlanData(
            plan_id=f"plan_{uuid.uuid4().hex[:12]}",
            question_intent=_clean_text(question_routing.get("question_intent"), fallback="general_followup"),
            response_strategy=_clean_text(question_routing.get("response_strategy"), fallback="answer_from_context"),
            plan_summary=plan_summary,
            planning_reason=planning_reason,
            focus_tickers=focus_tickers,
            focus_themes=focus_themes,
            related_task_ids=related_task_ids,
            primary_compare_targets=primary_compare_targets,
            requires_refresh=requires_refresh,
            requires_tooling=requires_tooling,
            requires_validation=requires_validation,
            steps=steps,
        )

    def build_validation_summary(
        self,
        *,
        question_routing: dict[str, Any],
        active_memory: dict[str, Any] | None,
        active_compression: dict[str, Any] | None,
        planner_mode: str,
        refresh_run: dict[str, Any] | None,
        previous_validation_summary: dict[str, Any] | None,
        related_tasks: Sequence[dict[str, Any]],
    ) -> StockAnalysisValidationSummaryData:
        support_points = list((active_memory or {}).get("support_points_json") or [])[:3]
        opposing_points = list((active_memory or {}).get("opposing_points_json") or [])[:3]
        risk_points = list((active_memory or {}).get("risk_points_json") or [])[:3]
        risk_points.extend(list((active_memory or {}).get("key_uncertainties_json") or [])[:2])
        risk_points = _unique_str_list(risk_points)[:4]
        question_intent = _clean_text(question_routing.get("question_intent"))
        has_refresh = bool((refresh_run or {}).get("refreshed_context_ids"))
        previous_status = _clean_text((previous_validation_summary or {}).get("thesis_status"))

        if question_intent in {"challenge_conclusion", "update_thesis"} and (
            risk_points or not has_refresh
        ):
            thesis_status = "thesis_recheck_needed"
        elif planner_mode != "context_only" or has_refresh:
            thesis_status = "thesis_improved"
        elif risk_points:
            thesis_status = "thesis_weakened"
        else:
            thesis_status = "thesis_maintained"

        summary = {
            "thesis_maintained": "当前 thesis 基本延续，本轮主要是在已有上下文上补充确认。",
            "thesis_weakened": "当前 thesis 仍可继续参考，但风险和不确定性较上一轮更突出。",
            "thesis_recheck_needed": "当前 thesis 需要重审，现有上下文不足以支撑更强结论。",
            "thesis_improved": "当前 thesis 获得了更多支持，本轮结论相对上一轮更完整。",
        }[thesis_status]

        if related_tasks:
            summary += f" 本轮还关联了 {len(related_tasks)} 条 research tasks。"

        thesis_change_hint = self._build_thesis_change_hint(
            previous_status=previous_status,
            current_status=thesis_status,
        )

        return StockAnalysisValidationSummaryData(
            thesis_status=thesis_status,
            summary=summary,
            support_points=support_points,
            opposing_points=opposing_points,
            risk_points=risk_points,
            thesis_change_hint=thesis_change_hint,
        )

    def build_task_update_suggestions(
        self,
        *,
        related_tasks: Sequence[dict[str, Any]],
        validation_summary: StockAnalysisValidationSummaryData,
        requires_refresh: bool,
        requires_tooling: bool,
        question_routing: dict[str, Any],
    ) -> list[StockAnalysisTaskUpdateSuggestionData]:
        suggestions: list[StockAnalysisTaskUpdateSuggestionData] = []
        question_intent = _clean_text(question_routing.get("question_intent"))
        for task in related_tasks:
            task_id = int(task.get("task_id") or 0)
            if task_id <= 0:
                continue
            if requires_refresh:
                suggestion = "convert_to_refresh_check"
                reason = "当前线程仍存在 stale / refresh recommended 上下文，建议先转成 refresh check 再继续。"
            elif validation_summary.thesis_status in {
                "thesis_improved",
                "thesis_maintained",
            } and question_intent in {"compare_targets", "explain_reasoning"}:
                suggestion = "complete"
                reason = "本轮已经围绕该任务完成核心验证，可考虑手动完成。"
            elif question_intent == "define_next_step":
                suggestion = "split_new_task"
                reason = "当前问题已经转入下一步研究规划，建议把该任务拆出更具体子问题。"
            elif requires_tooling:
                suggestion = "keep_open"
                reason = "仍需继续补证据，本轮只推进了任务而不适合自动关闭。"
            else:
                suggestion = "keep_open"
                reason = "本轮与该任务相关，但建议继续保留为 open 后续追踪。"
            suggestions.append(
                StockAnalysisTaskUpdateSuggestionData(
                    task_id=task_id,
                    suggestion=suggestion,
                    reason=reason,
                    suggested_title=(
                        f"{_clean_text(task.get('title'))}：拆成更具体验证问题"
                        if suggestion == "split_new_task"
                        else None
                    ),
                )
            )
        return suggestions

    def build_execution_trace(
        self,
        *,
        execution_plan: StockAnalysisExecutionPlanData,
        refresh_run: dict[str, Any] | None,
        planner_mode: str,
        tool_layers_to_use: Sequence[str],
        tool_call_summaries: Sequence[str],
        validation_summary: StockAnalysisValidationSummaryData | None,
        task_update_suggestions: Sequence[StockAnalysisTaskUpdateSuggestionData],
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[dict[str, Any]],
    ]:
        executed: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []
        refresh_failed = bool((refresh_run or {}).get("failed_context_ids"))
        refresh_happened = bool(refresh_run)
        for step in execution_plan.steps:
            step_data = step.model_copy(deep=True)
            if step.step_type.startswith("inspect_"):
                step_data.status = "executed"
                step_data.result_summary = "本轮已纳入该层研究输入。"
                executed.append(step_data.model_dump())
                continue
            if step.step_type == "refresh_stale_contexts":
                if refresh_happened and refresh_failed:
                    step_data.status = "failed"
                    step_data.result_summary = _clean_text(
                        (refresh_run or {}).get("summary"),
                        fallback="刷新阶段存在失败项。",
                    )
                    failed.append(step_data.model_dump())
                elif refresh_happened:
                    step_data.status = "executed"
                    step_data.result_summary = _clean_text(
                        (refresh_run or {}).get("summary"),
                        fallback="已在回答前执行 refresh。",
                    )
                    executed.append(step_data.model_dump())
                else:
                    step_data.status = "skipped"
                    step_data.result_summary = "本轮未触发 refresh。"
                    skipped.append(step_data.model_dump())
                continue
            if step.step_type == "collect_internal_structured_evidence":
                self._collect_tool_step(
                    step_data=step_data,
                    target_layer="internal_structured",
                    planner_mode=planner_mode,
                    tool_layers_to_use=tool_layers_to_use,
                    tool_call_summaries=tool_call_summaries,
                    executed=executed,
                    skipped=skipped,
                )
                continue
            if step.step_type == "collect_market_price_evidence":
                self._collect_tool_step(
                    step_data=step_data,
                    target_layer="market_price",
                    planner_mode=planner_mode,
                    tool_layers_to_use=tool_layers_to_use,
                    tool_call_summaries=tool_call_summaries,
                    executed=executed,
                    skipped=skipped,
                )
                continue
            if step.step_type == "collect_external_evidence":
                self._collect_tool_step(
                    step_data=step_data,
                    target_layer="external_confirmation",
                    planner_mode=planner_mode,
                    tool_layers_to_use=tool_layers_to_use,
                    tool_call_summaries=tool_call_summaries,
                    executed=executed,
                    skipped=skipped,
                )
                continue
            if step.step_type == "validate_thesis":
                if validation_summary is not None:
                    step_data.status = "executed"
                    step_data.result_summary = validation_summary.summary
                    executed.append(step_data.model_dump())
                else:
                    step_data.status = "skipped"
                    step_data.result_summary = "本轮未形成额外 thesis validation。"
                    skipped.append(step_data.model_dump())
                continue
            if step.step_type == "suggest_task_updates":
                if task_update_suggestions:
                    step_data.status = "executed"
                    step_data.result_summary = (
                        f"已形成 {len(task_update_suggestions)} 条 task update 建议。"
                    )
                    executed.append(step_data.model_dump())
                else:
                    step_data.status = "skipped"
                    step_data.result_summary = "本轮没有相关 research task 建议。"
                    skipped.append(step_data.model_dump())
                continue
            if step.step_type == "synthesize_answer":
                step_data.status = "executed"
                step_data.result_summary = "已完成本轮 answer synthesis。"
                executed.append(step_data.model_dump())
                continue
            skipped.append(step_data.model_dump())
        return executed, skipped, failed

    def _build_plan_steps(
        self,
        *,
        question_routing: dict[str, Any],
        context_cards: Sequence[dict[str, Any]],
        active_memory: dict[str, Any] | None,
        active_compression: dict[str, Any] | None,
        open_tasks: Sequence[dict[str, Any]],
        related_task_ids: Sequence[int],
        primary_compare_targets: Sequence[str],
        focus_tickers: Sequence[str],
        focus_themes: Sequence[str],
        requires_refresh: bool,
        requires_tooling: bool,
        requires_validation: bool,
    ) -> list[StockAnalysisExecutionStepData]:
        steps: list[StockAnalysisExecutionStepData] = []
        steps.append(
            self._make_step(
                step_type="inspect_context_cards",
                title="先读取当前显式上下文卡片",
                reason="本轮回答仍以 explicit context cards 为第一依据。",
                source="context_cards",
                target_refs=[str(len(context_cards))],
            )
        )
        if primary_compare_targets:
            steps.append(
                self._make_step(
                    step_type="inspect_compare_targets",
                    title="检查 compare targets",
                    reason="当前线程存在显式对比主线，需要先确认主次和比较轴。",
                    source="compare_targets",
                    target_refs=list(primary_compare_targets),
                )
            )
        if active_memory:
            steps.append(
                self._make_step(
                    step_type="inspect_active_memory",
                    title="回看 active memory",
                    reason="线程研究记忆可提供 thesis、风险和下一步问题。",
                    source="active_memory",
                    target_refs=[str(active_memory.get("memory_id") or "")],
                )
            )
        if active_compression:
            steps.append(
                self._make_step(
                    step_type="inspect_active_compression",
                    title="回看 active compression",
                    reason="较早历史已被压缩，需要快速确认未完成问题和最近补数记录。",
                    source="active_compression",
                    target_refs=[str(active_compression.get("compression_id") or "")],
                )
            )
        if open_tasks:
            steps.append(
                self._make_step(
                    step_type="inspect_open_tasks",
                    title="检查 open research tasks",
                    reason="本轮需要判断哪些 task 与当前问题相关，并把 task 变成研究锚点。",
                    source="research_tasks",
                    target_refs=[str(item) for item in related_task_ids[:4]],
                )
            )
        if requires_refresh:
            steps.append(
                self._make_step(
                    step_type="refresh_stale_contexts",
                    title="优先 refresh stale contexts",
                    reason="当前线程存在 stale / refresh recommended 上下文，先刷新再做强结论更稳。",
                    source="refresh",
                    target_refs=[str(item.get("context_id") or "") for item in context_cards if bool(item.get("is_stale")) or bool(item.get("refresh_recommended"))][:6],
                )
            )
        if requires_tooling:
            steps.append(
                self._make_step(
                    step_type="collect_internal_structured_evidence",
                    title="先看内部结构化证据",
                    reason="优先复用系统内已有结构化结果，避免直接跳外部补数。",
                    source="tooling",
                    target_refs=list(focus_tickers[:4] or focus_themes[:4]),
                )
            )
            if focus_tickers:
                steps.append(
                    self._make_step(
                        step_type="collect_market_price_evidence",
                        title="再补行情价格证据",
                        reason="当前问题涉及 ticker 或比较主线，需要确认最近价格动作。",
                        source="tooling",
                        target_refs=list(focus_tickers[:4]),
                    )
                )
            if _clean_text(question_routing.get("question_intent")) in {
                "external_evidence_check",
                "challenge_conclusion",
                "update_thesis",
            }:
                steps.append(
                    self._make_step(
                        step_type="collect_external_evidence",
                        title="必要时补外部证据",
                        reason="当前问题指向外部验证或结论重审，需要保守补充外部证据。",
                        source="tooling",
                        target_refs=list(focus_tickers[:4] or focus_themes[:4]),
                    )
                )
        if requires_validation:
            steps.append(
                self._make_step(
                    step_type="validate_thesis",
                    title="做 thesis validation",
                    reason="本轮需要判断 thesis 是延续、弱化还是需要重审。",
                    source="validation",
                    target_refs=list(primary_compare_targets[:2] or focus_tickers[:2]),
                )
            )
        steps.append(
            self._make_step(
                step_type="synthesize_answer",
                title="整合回答",
                reason="将上下文、任务、补数和 validation 汇总成最终回答。",
                source="answer",
                target_refs=list(focus_tickers[:2] or focus_themes[:2]),
            )
        )
        if related_task_ids or _clean_text(question_routing.get("response_strategy")) == "suggest_research_tasks":
            steps.append(
                self._make_step(
                    step_type="suggest_task_updates",
                    title="给出 research task 处理建议",
                    reason="本轮需要说明相关任务是否接近完成、继续保留还是应拆分。",
                    source="research_tasks",
                    target_refs=[str(item) for item in related_task_ids[:4]],
                )
            )
        return sorted(
            steps,
            key=lambda item: STEP_ORDER.index(item.step_type)
            if item.step_type in STEP_ORDER
            else len(STEP_ORDER),
        )

    def _match_related_tasks(
        self,
        *,
        open_tasks: Sequence[dict[str, Any]],
        user_message: str,
        focus_tickers: Sequence[str],
        focus_themes: Sequence[str],
        question_routing: dict[str, Any],
        research_task: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        message = _clean_text(user_message).lower()
        matched: list[dict[str, Any]] = []
        explicit_task_id = int((research_task or {}).get("task_id") or 0)
        for task in open_tasks:
            task_id = int(task.get("task_id") or 0)
            if task_id <= 0:
                continue
            if explicit_task_id and task_id == explicit_task_id:
                matched.append(task)
                continue
            task_title = _clean_text(task.get("title")).lower()
            task_summary = _clean_text(task.get("summary")).lower()
            task_tickers = set(list(task.get("related_tickers_json") or []))
            task_themes = set(list(task.get("related_themes_json") or []))
            if task_tickers & set(focus_tickers):
                matched.append(task)
                continue
            if task_themes & set(focus_themes):
                matched.append(task)
                continue
            if task_title and task_title in message:
                matched.append(task)
                continue
            if task_summary and any(token in message for token in task_summary.split()[:3]):
                matched.append(task)
                continue
            if _clean_text(question_routing.get("question_intent")) == "define_next_step" and task.get("priority") == "high":
                matched.append(task)
        deduped: list[dict[str, Any]] = []
        seen: set[int] = set()
        for item in matched:
            task_id = int(item.get("task_id") or 0)
            if task_id <= 0 or task_id in seen:
                continue
            seen.add(task_id)
            deduped.append(item)
        return deduped[:4]

    @staticmethod
    def _make_step(
        *,
        step_type: str,
        title: str,
        reason: str,
        source: str,
        target_refs: Sequence[str],
        required: bool = True,
    ) -> StockAnalysisExecutionStepData:
        return StockAnalysisExecutionStepData(
            step_id=f"step_{step_type}",
            step_type=step_type,
            title=title,
            reason=reason,
            required=required,
            status="planned",
            source=source,
            target_refs=_unique_str_list(target_refs),
            result_summary=None,
        )

    @staticmethod
    def _build_focus_tickers(
        *,
        thread: dict[str, Any],
        context_cards: Sequence[dict[str, Any]],
        research_task: dict[str, Any] | None,
        compare_targets: Sequence[dict[str, Any]],
    ) -> list[str]:
        return _unique_str_list(
            list((research_task or {}).get("related_tickers_json") or [])
            + [
                _clean_text(item.get("ref"))
                for item in compare_targets
                if _clean_text(item.get("target_type")) == "ticker"
            ]
            + list(thread.get("ticker_refs_json") or [])
            + [ref for card in context_cards for ref in list(card.get("ticker_refs_json") or [])]
        )[:6]

    @staticmethod
    def _build_focus_themes(
        *,
        thread: dict[str, Any],
        context_cards: Sequence[dict[str, Any]],
        research_task: dict[str, Any] | None,
    ) -> list[str]:
        return _unique_str_list(
            list((research_task or {}).get("related_themes_json") or [])
            + list(thread.get("theme_refs_json") or [])
            + [ref for card in context_cards for ref in list(card.get("theme_refs_json") or [])]
        )[:6]

    @staticmethod
    def _build_plan_summary(
        *,
        question_routing: dict[str, Any],
        requires_refresh: bool,
        requires_tooling: bool,
        requires_validation: bool,
        related_task_ids: Sequence[int],
        primary_compare_targets: Sequence[str],
    ) -> str:
        parts: list[str] = [
            f"先按 {question_routing.get('question_intent') or 'general_followup'} 的研究语义读取显式上下文。"
        ]
        if primary_compare_targets:
            parts.append(f"当前优先围绕 {' / '.join(primary_compare_targets[:2])} 展开比较。")
        if requires_refresh:
            parts.append("存在 refresh 需求，优先检查并刷新较旧卡片。")
        if requires_tooling:
            parts.append("若上下文仍不足，则继续补内部/行情/外部证据。")
        if requires_validation:
            parts.append("最后补一个 thesis validation，避免只给结论不说明变化。")
        if related_task_ids:
            parts.append(f"本轮还会参考 {len(related_task_ids)} 条相关 research task。")
        return " ".join(parts)

    @staticmethod
    def _build_planning_reason(
        *,
        question_routing: dict[str, Any],
        stale_contexts: Sequence[dict[str, Any]],
        related_task_ids: Sequence[int],
        research_task: dict[str, Any] | None,
        requires_tooling: bool,
    ) -> str:
        reasons: list[str] = [
            _clean_text(question_routing.get("routing_reason"), fallback="已完成 question routing。")
        ]
        if research_task:
            reasons.append(
                f"本轮显式锚定 research task #{int(research_task.get('task_id') or 0)}。"
            )
        if stale_contexts:
            reasons.append("线程里存在 stale / refresh recommended 上下文。")
        if related_task_ids:
            reasons.append("当前问题与线程中的 open tasks 有明确重叠。")
        if requires_tooling:
            reasons.append("仅靠当前显式上下文不足以覆盖全部证据缺口。")
        return " ".join(reasons)

    @staticmethod
    def _build_thesis_change_hint(
        *,
        previous_status: str,
        current_status: str,
    ) -> str | None:
        if not previous_status:
            return "当前是线程内第一条显式 thesis validation。"
        if previous_status == current_status:
            return "与上一轮 validation 基本一致。"
        mapping = {
            ("thesis_maintained", "thesis_improved"): "相对上一轮，当前 thesis 获得更多支持。",
            ("thesis_improved", "thesis_weakened"): "相对上一轮，当前 thesis 支撑变弱。",
            ("thesis_weakened", "thesis_recheck_needed"): "相对上一轮，当前 thesis 已转入需要重审。",
        }
        return mapping.get(
            (previous_status, current_status),
            f"相对上一轮，thesis 状态由 {previous_status} 变为 {current_status}。",
        )

    @staticmethod
    def _collect_tool_step(
        *,
        step_data: StockAnalysisExecutionStepData,
        target_layer: str,
        planner_mode: str,
        tool_layers_to_use: Sequence[str],
        tool_call_summaries: Sequence[str],
        executed: list[dict[str, Any]],
        skipped: list[dict[str, Any]],
    ) -> None:
        if planner_mode != "context_only" and target_layer in list(tool_layers_to_use):
            step_data.status = "executed"
            step_data.result_summary = (
                tool_call_summaries[0] if tool_call_summaries else "已执行对应补数步骤。"
            )
            executed.append(step_data.model_dump())
        else:
            step_data.status = "skipped"
            step_data.result_summary = "本轮未进入该层补数。"
            skipped.append(step_data.model_dump())


_stock_analysis_execution_planner_service: Optional[
    StockAnalysisExecutionPlannerService
] = None


def get_stock_analysis_execution_planner_service() -> (
    StockAnalysisExecutionPlannerService
):
    global _stock_analysis_execution_planner_service
    if _stock_analysis_execution_planner_service is None:
        _stock_analysis_execution_planner_service = (
            StockAnalysisExecutionPlannerService()
        )
    return _stock_analysis_execution_planner_service


def reset_stock_analysis_execution_planner_service() -> None:
    global _stock_analysis_execution_planner_service
    _stock_analysis_execution_planner_service = None
