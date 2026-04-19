from __future__ import annotations

from typing import Any, Sequence


class StockAnalysisContextAssembler:
    def assemble(
        self,
        *,
        thread: dict[str, Any],
        context_cards: Sequence[dict[str, Any]],
        active_memory: dict[str, Any] | None = None,
        active_compression: dict[str, Any] | None = None,
        question_routing: dict[str, Any] | None = None,
        execution_plan: dict[str, Any] | None = None,
        recent_raw_messages: Sequence[dict[str, Any]] | None = None,
        user_question: str,
    ) -> dict[str, Any]:
        pinned_cards = [item for item in context_cards if bool(item.get("is_pinned"))]
        ordered_cards = list(pinned_cards) + [
            item for item in context_cards if not bool(item.get("is_pinned"))
        ]
        compare_targets = self._normalize_compare_targets(
            thread.get("compare_targets_json") or []
        )
        ticker_refs = self._unique_list(
            ref
            for item in ordered_cards
            for ref in list(item.get("ticker_refs_json") or [])
            if str(ref or "").strip()
        )
        theme_refs = self._unique_list(
            ref
            for item in ordered_cards
            for ref in list(item.get("theme_refs_json") or [])
            if str(ref or "").strip()
        )
        used_context_ids = [int(item.get("context_id") or 0) for item in ordered_cards if int(item.get("context_id") or 0) > 0]
        compared_tickers = self._unique_list(
            item["ref"] for item in compare_targets if item["target_type"] == "ticker"
        )
        compared_themes = self._unique_list(
            item["ref"] for item in compare_targets if item["target_type"] == "theme"
        )
        stale_context_ids = [
            int(item.get("context_id") or 0)
            for item in ordered_cards
            if bool(item.get("is_stale")) and int(item.get("context_id") or 0) > 0
        ]
        refresh_recommended_context_ids = [
            int(item.get("context_id") or 0)
            for item in ordered_cards
            if bool(item.get("refresh_recommended")) and int(item.get("context_id") or 0) > 0
        ]
        missing_context_hints = self._build_missing_hints(
            thread=thread,
            context_cards=ordered_cards,
            ticker_refs=ticker_refs,
            theme_refs=theme_refs,
            compare_targets=compare_targets,
        )
        prompt_context = "\n\n".join(
            [
                "Thread Overview",
                self._build_thread_overview(thread=thread),
                "Explicit Context Cards",
                self._build_context_cards_block(ordered_cards),
                "Compare Targets",
                self._build_compare_targets_block(
                    compare_targets=compare_targets,
                    context_cards=ordered_cards,
                ),
                "Ticker Focus",
                self._build_focus_block("Tickers", ticker_refs),
                "Theme Focus",
                self._build_focus_block("Themes", theme_refs),
                "Current Context Refresh Status",
                self._build_freshness_block(ordered_cards),
                "Thread Active Research Memory",
                self._build_active_memory_block(active_memory=active_memory),
                "Thread Active Conversation Compression",
                self._build_active_compression_block(
                    active_compression=active_compression
                ),
                "Question Routing",
                self._build_question_routing_block(
                    question_routing=question_routing
                ),
                "Execution Plan",
                self._build_execution_plan_block(execution_plan=execution_plan),
                "Recent Raw Messages",
                self._build_recent_raw_messages_block(
                    recent_raw_messages=recent_raw_messages or []
                ),
                "Current User Question",
                user_question.strip(),
                "Response Rules",
                self._build_response_rules(
                    missing_context_hints=missing_context_hints,
                    comparison_mode=len(compare_targets) >= 2,
                    stale_context_ids=stale_context_ids,
                    has_active_memory=active_memory is not None,
                    has_active_compression=active_compression is not None,
                    question_routing=question_routing,
                ),
            ]
        )
        return {
            "prompt_context": prompt_context,
            "used_context_ids": used_context_ids,
            "ticker_refs": ticker_refs,
            "theme_refs": theme_refs,
            "missing_context_hints": missing_context_hints,
            "compare_targets": compare_targets,
            "compared_tickers": compared_tickers,
            "compared_themes": compared_themes,
            "comparison_mode": len(compare_targets) >= 2,
            "stale_context_ids": stale_context_ids,
            "refresh_recommended_context_ids": refresh_recommended_context_ids,
            "used_active_memory": active_memory is not None,
            "used_active_compression": active_compression is not None,
            "recent_raw_message_count": len(list(recent_raw_messages or [])),
        }

    @staticmethod
    def _build_thread_overview(*, thread: dict[str, Any]) -> str:
        return (
            f"Title: {thread.get('title') or 'Untitled'}\n"
            f"Focus Type: {thread.get('focus_type') or 'mixed'}\n"
            f"Conversation ID: {thread.get('conversation_id') or '--'}"
        )

    def _build_context_cards_block(self, cards: Sequence[dict[str, Any]]) -> str:
        if not cards:
            return "No context cards are currently attached to this thread."
        lines: list[str] = []
        for item in cards:
            lines.append(
                "\n".join(
                    [
                        f"- Context ID: {item.get('context_id')}",
                        f"  Type: {item.get('context_type') or '--'}",
                        f"  Title: {item.get('title') or '--'}",
                        f"  Subtitle: {item.get('subtitle') or '--'}",
                        f"  Summary: {item.get('summary') or '--'}",
                        f"  Tickers: {', '.join(list(item.get('ticker_refs_json') or [])) or '--'}",
                        f"  Themes: {', '.join(list(item.get('theme_refs_json') or [])) or '--'}",
                        f"  Source: {item.get('source_module') or '--'}",
                        f"  Freshness: {item.get('freshness_label') or '--'}",
                        f"  Refresh Recommended: {'yes' if item.get('refresh_recommended') else 'no'}",
                        f"  Pinned: {'yes' if item.get('is_pinned') else 'no'}",
                    ]
                )
            )
        return "\n".join(lines)

    def _build_compare_targets_block(
        self,
        *,
        compare_targets: Sequence[dict[str, Any]],
        context_cards: Sequence[dict[str, Any]],
    ) -> str:
        if len(compare_targets) < 2:
            return "No explicit comparison targets are currently configured."
        lines: list[str] = []
        for item in compare_targets:
            freshness_label = self._resolve_compare_target_freshness(
                target=item,
                context_cards=context_cards,
            )
            lines.append(
                (
                    f"- {item.get('label') or item.get('ref')} "
                    f"[{item.get('target_type')}/{item.get('role')}] "
                    f"ref={item.get('ref')} source={item.get('source_module')} "
                    f"freshness={freshness_label}"
                )
            )
        return "\n".join(lines)

    @staticmethod
    def _build_freshness_block(cards: Sequence[dict[str, Any]]) -> str:
        if not cards:
            return "No context cards."
        stale_cards = [item for item in cards if bool(item.get("is_stale"))]
        refresh_cards = [
            item for item in cards if bool(item.get("refresh_recommended"))
        ]
        lines = [
            (
                "Current refresh state: some contexts should be refreshed before strong conclusions."
                if stale_cards or refresh_cards
                else "Current refresh state: explicit contexts are relatively fresh."
            ),
            (
                "Stale contexts: "
                + ", ".join(
                    str(item.get("title") or item.get("context_id")) for item in stale_cards
                )
                if stale_cards
                else "Stale contexts: none"
            ),
            (
                "Refresh recommended: "
                + ", ".join(
                    str(item.get("title") or item.get("context_id"))
                    for item in refresh_cards
                )
                if refresh_cards
                else "Refresh recommended: none"
            ),
        ]
        return "\n".join(lines)

    @staticmethod
    def _build_focus_block(label: str, refs: Sequence[str]) -> str:
        if not refs:
            return f"{label}: none"
        return f"{label}: {', '.join(refs)}"

    @staticmethod
    def _build_response_rules(
        *,
        missing_context_hints: Sequence[str],
        comparison_mode: bool,
        stale_context_ids: Sequence[int],
        has_active_memory: bool,
        has_active_compression: bool,
        question_routing: dict[str, Any] | None,
    ) -> str:
        rule_lines = [
            "- Answer from the explicit context cards first, then use active memory, active compression, and recent raw messages as supporting layers.",
            "- Do not claim any external market data, news, tool result, or fresh quote that is not in the context.",
            "- If context is insufficient, say what is missing clearly.",
            "- Prefer structured reasoning and comparison over vague narrative.",
            "- When multiple tickers are mentioned, compare them explicitly.",
        ]
        if has_active_memory:
            rule_lines.append(
                "- Active research memory is a thread-level summary only. Explicit context cards and current comparison targets override it when conflicts appear."
            )
        if has_active_compression:
            rule_lines.append(
                "- Active conversation compression summarizes older message history. Use recent raw messages for the latest details."
            )
        if question_routing:
            strategy = str(question_routing.get("response_strategy") or "").strip()
            if strategy == "answer_with_compare_focus":
                rule_lines.append(
                    "- Question routing requests compare focus. Organize the answer by comparison axes, primary vs secondary, and invalidation conditions."
                )
            elif strategy == "refresh_then_answer":
                rule_lines.append(
                    "- Question routing requests refresh awareness. Explain what should be refreshed before drawing stronger conclusions."
                )
            elif strategy == "tooling_then_answer":
                rule_lines.append(
                    "- Question routing signals evidence gap. Clarify which newer evidence is still required."
                )
            elif strategy == "restate_and_recheck":
                rule_lines.append(
                    "- Question routing requests thesis recheck. Restate the current thesis first, then challenge it with counterpoints."
                )
            elif strategy == "highlight_context_gap":
                rule_lines.append(
                    "- Question routing requests explicit gap handling. Lead with what context is missing before giving a tentative answer."
                )
            elif strategy == "suggest_research_tasks":
                rule_lines.append(
                    "- Question routing requests next-step organization. End with explicit next research tasks."
                )
        if comparison_mode:
            rule_lines.append(
                "- This thread is in explicit comparison mode. State which objects are being compared and their sources."
            )
        if stale_context_ids:
            rule_lines.append(
                "- Some referenced contexts are stale. Mention that stronger conclusions should wait until refresh."
            )
        if missing_context_hints:
            rule_lines.append(
                f"- Known missing context hints: {'; '.join(missing_context_hints)}."
            )
        return "\n".join(rule_lines)

    @staticmethod
    def _build_missing_hints(
        *,
        thread: dict[str, Any],
        context_cards: Sequence[dict[str, Any]],
        ticker_refs: Sequence[str],
        theme_refs: Sequence[str],
        compare_targets: Sequence[dict[str, Any]],
    ) -> list[str]:
        hints: list[str] = []
        if not context_cards:
            hints.append("当前线程还没有挂载任何上下文卡片")
        if not ticker_refs and thread.get("focus_type") in {"ticker", "holding"}:
            hints.append("缺少明确 ticker 上下文")
        if len(compare_targets) >= 2 and not theme_refs:
            hints.append("多标的比较时缺少统一题材或主线语境")
        if not any(bool(item.get("is_pinned")) for item in context_cards):
            hints.append("尚未置顶关键上下文卡片")
        if any(bool(item.get("is_stale")) for item in context_cards):
            hints.append("本轮比较对象中存在较旧上下文，建议刷新后再做强结论")
        return hints

    @staticmethod
    def _build_active_memory_block(*, active_memory: dict[str, Any] | None) -> str:
        if active_memory is None:
            return "No active research memory."
        return "\n".join(
            [
                f"Memory ID: {active_memory.get('memory_id')}",
                f"Version: {active_memory.get('version') or '--'}",
                f"Title: {active_memory.get('title') or '--'}",
                f"Updated At: {active_memory.get('updated_at') or '--'}",
                f"Stance: {active_memory.get('stance') or '--'}",
                f"Confidence: {active_memory.get('confidence') or '--'}",
                f"Time Horizon: {active_memory.get('time_horizon') or '--'}",
                f"Summary: {active_memory.get('summary') or '--'}",
                "Support Points: "
                + (
                    "; ".join(list(active_memory.get("support_points_json") or [])[:4])
                    or "--"
                ),
                "Opposing Points: "
                + (
                    "; ".join(list(active_memory.get("opposing_points_json") or [])[:3])
                    or "--"
                ),
                "Risk Points: "
                + (
                    "; ".join(list(active_memory.get("risk_points_json") or [])[:4]) or "--"
                ),
                "Key Uncertainties: "
                + (
                    "; ".join(
                        list(active_memory.get("key_uncertainties_json") or [])[:4]
                    )
                    or "--"
                ),
                "Invalidation Conditions: "
                + (
                    "; ".join(
                        list(active_memory.get("invalidation_conditions_json") or [])[:4]
                    )
                    or "--"
                ),
                "Next Questions: "
                + (
                    "; ".join(list(active_memory.get("next_questions_json") or [])[:4])
                    or "--"
                ),
                "Next Data To Check: "
                + (
                    "; ".join(
                        list(active_memory.get("next_data_to_check_json") or [])[:4]
                    )
                    or "--"
                ),
            ]
        )

    @staticmethod
    def _build_execution_plan_block(
        *, execution_plan: dict[str, Any] | None
    ) -> str:
        if execution_plan is None:
            return "No explicit execution planning guidance."
        steps = list(execution_plan.get("steps") or [])
        return "\n".join(
            [
                f"Plan Summary: {execution_plan.get('plan_summary') or '--'}",
                f"Planning Reason: {execution_plan.get('planning_reason') or '--'}",
                "Focus Tickers: "
                + (", ".join(list(execution_plan.get("focus_tickers") or [])) or "--"),
                "Focus Themes: "
                + (", ".join(list(execution_plan.get("focus_themes") or [])) or "--"),
                "Related Task IDs: "
                + (
                    ", ".join(str(item) for item in list(execution_plan.get("related_task_ids") or []))
                    or "--"
                ),
                f"Requires Refresh: {'yes' if execution_plan.get('requires_refresh') else 'no'}",
                f"Requires Tooling: {'yes' if execution_plan.get('requires_tooling') else 'no'}",
                f"Requires Validation: {'yes' if execution_plan.get('requires_validation') else 'no'}",
                "Planned Steps: "
                + (
                    "; ".join(
                        f"{item.get('step_type')}[{item.get('status')}]"
                        for item in steps[:8]
                    )
                    or "--"
                ),
            ]
        )

    @staticmethod
    def _build_active_compression_block(
        *, active_compression: dict[str, Any] | None
    ) -> str:
        if active_compression is None:
            return "No active conversation compression."
        return "\n".join(
            [
                f"Compression ID: {active_compression.get('compression_id')}",
                f"Version: {active_compression.get('version') or '--'}",
                f"Title: {active_compression.get('title') or '--'}",
                f"Updated At: {active_compression.get('updated_at') or '--'}",
                f"Current Focus: {active_compression.get('current_focus') or '--'}",
                f"Covered Until Message ID: {active_compression.get('covered_until_message_id') or '--'}",
                f"Covered Message Count: {active_compression.get('covered_message_count') or 0}",
                f"Summary: {active_compression.get('summary') or '--'}",
                "Resolved Topics: "
                + (
                    "; ".join(list(active_compression.get("resolved_topics_json") or [])[:4])
                    or "--"
                ),
                "Open Questions: "
                + (
                    "; ".join(list(active_compression.get("open_questions_json") or [])[:4])
                    or "--"
                ),
                "Recent Compare Notes: "
                + (
                    "; ".join(
                        list(active_compression.get("recent_compare_notes_json") or [])[:3]
                    )
                    or "--"
                ),
                "Recent Refresh Notes: "
                + (
                    "; ".join(
                        list(active_compression.get("recent_refresh_notes_json") or [])[:3]
                    )
                    or "--"
                ),
                "Recent Tooling Notes: "
                + (
                    "; ".join(
                        list(active_compression.get("recent_tooling_notes_json") or [])[:3]
                    )
                    or "--"
                ),
                "Recent Evidence Notes: "
                + (
                    "; ".join(
                        list(active_compression.get("recent_evidence_notes_json") or [])[:3]
                    )
                    or "--"
                ),
            ]
        )

    @staticmethod
    def _build_recent_raw_messages_block(
        *, recent_raw_messages: Sequence[dict[str, Any]]
    ) -> str:
        if not recent_raw_messages:
            return "No recent raw messages."
        lines: list[str] = []
        for item in recent_raw_messages:
            lines.append(
                f"- {item.get('role') or '--'}[{item.get('item_id') or '--'}]: {item.get('content') or '--'}"
            )
        return "\n".join(lines)

    @staticmethod
    def _build_question_routing_block(
        *, question_routing: dict[str, Any] | None
    ) -> str:
        if question_routing is None:
            return "No explicit question routing guidance."
        return "\n".join(
            [
                f"Question Intent: {question_routing.get('question_intent') or '--'}",
                f"Response Strategy: {question_routing.get('response_strategy') or '--'}",
                f"Routing Reason: {question_routing.get('routing_reason') or '--'}",
                "Recommended Next Action: "
                + str(question_routing.get("recommended_next_action") or "--"),
                "Followup Candidates: "
                + (
                    "; ".join(list(question_routing.get("followup_candidates") or [])[:4])
                    or "--"
                ),
                "Suggested Task Titles: "
                + (
                    "; ".join(list(question_routing.get("suggested_task_titles") or [])[:4])
                    or "--"
                ),
            ]
        )

    @staticmethod
    def _unique_list(values) -> list[str]:
        result: list[str] = []
        for value in values:
            text = str(value or "").strip()
            if text and text not in result:
                result.append(text)
        return result

    @staticmethod
    def _normalize_compare_targets(values: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()
        for index, item in enumerate(values):
            target_type = str(item.get("target_type") or "ticker").strip()
            ref = str(item.get("ref") or "").strip()
            if target_type not in {"ticker", "theme"} or not ref:
                continue
            source_module = str(item.get("source_module") or "manual").strip() or "manual"
            dedupe_key = (target_type, ref, source_module)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            result.append(
                {
                    "target_type": target_type,
                    "ref": ref,
                    "label": str(item.get("label") or ref).strip() or ref,
                    "source_module": source_module,
                    "source_ref": str(item.get("source_ref") or ref).strip() or ref,
                    "role": str(
                        item.get("role") or ("primary" if index == 0 else "secondary")
                    ).strip()
                    or "secondary",
                    "order": int(item.get("order") or index),
                }
            )
        return sorted(
            result,
            key=lambda item: (int(item.get("order") or 0), str(item.get("label") or "")),
        )

    @staticmethod
    def _resolve_compare_target_freshness(
        *,
        target: dict[str, Any],
        context_cards: Sequence[dict[str, Any]],
    ) -> str:
        matches: list[dict[str, Any]] = []
        for item in context_cards:
            if (
                target.get("target_type") == "ticker"
                and str(target.get("ref") or "") in list(item.get("ticker_refs_json") or [])
            ):
                matches.append(item)
            if (
                target.get("target_type") == "theme"
                and str(target.get("ref") or "") in list(item.get("theme_refs_json") or [])
            ):
                matches.append(item)
        if not matches:
            return "unknown"
        if any(bool(item.get("is_stale")) for item in matches):
            return "stale"
        if any(bool(item.get("refresh_recommended")) for item in matches):
            return "refresh_recommended"
        freshness_labels = [
            str(item.get("freshness_label") or "").strip()
            for item in matches
            if str(item.get("freshness_label") or "").strip()
        ]
        return freshness_labels[0] if freshness_labels else "available"
