from __future__ import annotations

from typing import Any, Sequence


class StockAnalysisContextAssembler:
    def assemble(
        self,
        *,
        thread: dict[str, Any],
        context_cards: Sequence[dict[str, Any]],
        user_question: str,
    ) -> dict[str, Any]:
        pinned_cards = [item for item in context_cards if bool(item.get("is_pinned"))]
        ordered_cards = list(pinned_cards) + [
            item for item in context_cards if not bool(item.get("is_pinned"))
        ]
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
        missing_context_hints = self._build_missing_hints(
            thread=thread,
            context_cards=ordered_cards,
            ticker_refs=ticker_refs,
            theme_refs=theme_refs,
        )
        prompt_context = "\n\n".join(
            [
                "Thread Overview",
                self._build_thread_overview(thread=thread),
                "Context Cards",
                self._build_context_cards_block(ordered_cards),
                "Ticker Focus",
                self._build_focus_block("Tickers", ticker_refs),
                "Theme Focus",
                self._build_focus_block("Themes", theme_refs),
                "Current User Question",
                user_question.strip(),
                "Response Rules",
                self._build_response_rules(missing_context_hints),
            ]
        )
        return {
            "prompt_context": prompt_context,
            "used_context_ids": used_context_ids,
            "ticker_refs": ticker_refs,
            "theme_refs": theme_refs,
            "missing_context_hints": missing_context_hints,
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
                        f"  Pinned: {'yes' if item.get('is_pinned') else 'no'}",
                    ]
                )
            )
        return "\n".join(lines)

    @staticmethod
    def _build_focus_block(label: str, refs: Sequence[str]) -> str:
        if not refs:
            return f"{label}: none"
        return f"{label}: {', '.join(refs)}"

    @staticmethod
    def _build_response_rules(missing_context_hints: Sequence[str]) -> str:
        rule_lines = [
            "- Answer only from the explicit context cards and conversation history.",
            "- Do not claim any external market data, news, tool result, or fresh quote that is not in the context.",
            "- If context is insufficient, say what is missing clearly.",
            "- Prefer structured reasoning and comparison over vague narrative.",
            "- When multiple tickers are mentioned, compare them explicitly.",
        ]
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
    ) -> list[str]:
        hints: list[str] = []
        if not context_cards:
            hints.append("当前线程还没有挂载任何上下文卡片")
        if not ticker_refs and thread.get("focus_type") in {"ticker", "holding"}:
            hints.append("缺少明确 ticker 上下文")
        if len(ticker_refs) >= 2 and not theme_refs:
            hints.append("多标的比较时缺少统一题材或主线语境")
        if not any(bool(item.get("is_pinned")) for item in context_cards):
            hints.append("尚未置顶关键上下文卡片")
        return hints

    @staticmethod
    def _unique_list(values) -> list[str]:
        result: list[str] = []
        for value in values:
            text = str(value or "").strip()
            if text and text not in result:
                result.append(text)
        return result
