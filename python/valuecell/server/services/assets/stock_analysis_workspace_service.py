from __future__ import annotations

import datetime as dt
from typing import Any, Optional, Sequence

from loguru import logger

from valuecell.server.services.conversation_service import (
    ConversationService as ServerConversationService,
)
from valuecell.server.services.tradingagents_service import TradingAgentsService
from valuecell.utils.uuid import generate_conversation_id

from ...db.repositories.analysis_context_card_repository import (
    AnalysisContextCardRepository,
)
from ...db.repositories.stock_analysis_thread_repository import (
    StockAnalysisThreadRepository,
)

DEFAULT_USER_ID = "default_user"
STOCK_ANALYSIS_AGENT_NAME = "StockAnalysisWorkspace"
TRADINGAGENTS_CONTEXT_TYPE = "tradingagents_run"
SUPPORTED_SOURCE_MODULES = {"tradingagents_run"}
SUPPORTED_FOCUS_TYPES = {
    "ticker",
    "theme",
    "comparison",
    "holding",
    "tradingagents_followup",
    "mixed",
}
SUPPORTED_CONTEXT_TYPES = {TRADINGAGENTS_CONTEXT_TYPE}


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def _clean_refs(values: Sequence[str] | None) -> list[str]:
    deduped: list[str] = []
    for value in values or []:
        text = str(value or "").strip()
        if text and text not in deduped:
            deduped.append(text)
    return deduped


class StockAnalysisWorkspaceService:
    def __init__(
        self,
        stock_analysis_thread_repository: Optional[StockAnalysisThreadRepository] = None,
        analysis_context_card_repository: Optional[AnalysisContextCardRepository] = None,
        tradingagents_service: Optional[TradingAgentsService] = None,
        conversation_service: Optional[ServerConversationService] = None,
    ) -> None:
        self.stock_analysis_thread_repository = (
            stock_analysis_thread_repository or StockAnalysisThreadRepository()
        )
        self.analysis_context_card_repository = (
            analysis_context_card_repository or AnalysisContextCardRepository()
        )
        self.tradingagents_service = tradingagents_service or TradingAgentsService()
        self.conversation_service = conversation_service or ServerConversationService()

    async def list_threads(self, *, user_id: str) -> dict[str, Any]:
        threads = self.stock_analysis_thread_repository.list_threads(user_id=user_id)
        items = [self._serialize_thread(item) for item in threads]
        return {
            "generated_at": _utcnow().isoformat(),
            "items": items,
            "count": len(items),
        }

    async def create_thread(
        self,
        *,
        user_id: str,
        title: str,
        focus_type: str,
        ticker_refs_json: Sequence[str] | None = None,
        theme_refs_json: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        normalized_focus_type = self._normalize_focus_type(focus_type)
        conversation_id = generate_conversation_id()
        conversation = await self.conversation_service.conversation_manager.create_conversation(
            user_id=user_id,
            title=title,
            conversation_id=conversation_id,
            agent_name=STOCK_ANALYSIS_AGENT_NAME,
        )
        logger.info(
            "Created stock analysis conversation {conversation_id}",
            conversation_id=conversation.conversation_id,
        )
        created = self.stock_analysis_thread_repository.create_thread(
            {
                "user_id": user_id,
                "title": title.strip(),
                "focus_type": normalized_focus_type,
                "ticker_refs_json": _clean_refs(ticker_refs_json),
                "theme_refs_json": _clean_refs(theme_refs_json),
                "conversation_id": conversation_id,
            }
        )
        if created is None:
            await self.conversation_service.conversation_manager.delete_conversation(
                conversation_id
            )
            raise ValueError("Failed to create stock analysis thread")
        return self._serialize_thread(created)

    async def update_thread(
        self,
        *,
        user_id: str,
        thread_id: int,
        title: str | None = None,
        focus_type: str | None = None,
        ticker_refs_json: Sequence[str] | None = None,
        theme_refs_json: Sequence[str] | None = None,
    ) -> dict[str, Any] | None:
        existing = self.stock_analysis_thread_repository.get_thread_by_id(
            user_id=user_id,
            thread_id=thread_id,
        )
        if existing is None:
            return None
        payload: dict[str, Any] = {}
        if title is not None:
            payload["title"] = title.strip()
        if focus_type is not None:
            payload["focus_type"] = self._normalize_focus_type(focus_type)
        if ticker_refs_json is not None:
            payload["ticker_refs_json"] = _clean_refs(ticker_refs_json)
        if theme_refs_json is not None:
            payload["theme_refs_json"] = _clean_refs(theme_refs_json)
        updated = self.stock_analysis_thread_repository.update_thread(
            user_id=user_id,
            thread_id=thread_id,
            payload=payload,
        )
        if updated is None:
            return None
        if title is not None:
            await self._sync_conversation_title(
                conversation_id=updated.conversation_id,
                title=updated.title,
            )
        return self._serialize_thread(updated)

    async def delete_thread(self, *, user_id: str, thread_id: int) -> dict[str, Any] | None:
        existing = self.stock_analysis_thread_repository.get_thread_by_id(
            user_id=user_id,
            thread_id=thread_id,
        )
        if existing is None:
            return None
        archived = self.stock_analysis_thread_repository.update_thread(
            user_id=user_id,
            thread_id=thread_id,
            payload={"archived_at": _utcnow()},
        )
        if archived is None:
            return None
        await self.conversation_service.conversation_manager.deactivate_conversation(
            archived.conversation_id
        )
        return self._serialize_thread(archived)

    async def duplicate_thread(
        self,
        *,
        user_id: str,
        thread_id: int,
    ) -> dict[str, Any] | None:
        source_thread = self.stock_analysis_thread_repository.get_thread_by_id(
            user_id=user_id,
            thread_id=thread_id,
        )
        if source_thread is None:
            return None
        duplicated = await self.create_thread(
            user_id=user_id,
            title=f"{source_thread.title}（副本）",
            focus_type=source_thread.focus_type,
            ticker_refs_json=list(source_thread.ticker_refs_json or []),
            theme_refs_json=list(source_thread.theme_refs_json or []),
        )
        source_contexts = self.analysis_context_card_repository.list_context_cards(
            user_id=user_id,
            thread_id=thread_id,
        )
        copied_contexts: list[dict[str, Any]] = []
        for item in source_contexts:
            created = self.analysis_context_card_repository.create_context_card(
                {
                    "thread_id": duplicated["thread_id"],
                    "user_id": user_id,
                    "context_type": item.context_type,
                    "title": item.title,
                    "subtitle": item.subtitle,
                    "ticker_refs_json": list(item.ticker_refs_json or []),
                    "theme_refs_json": list(item.theme_refs_json or []),
                    "summary": item.summary,
                    "snapshot_payload_json": item.snapshot_payload_json or {},
                    "source_module": item.source_module,
                    "source_ref": item.source_ref,
                    "staleness_hint": item.staleness_hint,
                    "is_pinned": item.is_pinned,
                }
            )
            if created:
                copied_contexts.append(self._serialize_context_card(created))
        return {
            "thread": duplicated,
            "contexts": copied_contexts,
        }

    async def list_context_cards(
        self,
        *,
        user_id: str,
        thread_id: int,
    ) -> dict[str, Any] | None:
        thread = self.stock_analysis_thread_repository.get_thread_by_id(
            user_id=user_id,
            thread_id=thread_id,
        )
        if thread is None:
            return None
        items = self.analysis_context_card_repository.list_context_cards(
            user_id=user_id,
            thread_id=thread_id,
        )
        contexts = [self._serialize_context_card(item) for item in items]
        return {
            "generated_at": _utcnow().isoformat(),
            "items": contexts,
            "count": len(contexts),
        }

    async def create_context_card(
        self,
        *,
        user_id: str,
        thread_id: int,
        context_type: str,
        title: str,
        subtitle: str | None = None,
        ticker_refs_json: Sequence[str] | None = None,
        theme_refs_json: Sequence[str] | None = None,
        summary: str,
        snapshot_payload_json: dict[str, Any] | None = None,
        source_module: str,
        source_ref: str | None = None,
        staleness_hint: str | None = None,
        is_pinned: bool = False,
        mode: str = "append",
    ) -> dict[str, Any] | None:
        thread = self.stock_analysis_thread_repository.get_thread_by_id(
            user_id=user_id,
            thread_id=thread_id,
        )
        if thread is None:
            return None
        normalized_context_type = self._normalize_context_type(context_type)
        normalized_mode = self._normalize_context_mode(mode)
        if normalized_mode == "replace":
            self.analysis_context_card_repository.delete_context_cards_by_filter(
                user_id=user_id,
                thread_id=thread_id,
                context_type=normalized_context_type,
                source_module=source_module,
            )
        created = self.analysis_context_card_repository.create_context_card(
            {
                "thread_id": thread_id,
                "user_id": user_id,
                "context_type": normalized_context_type,
                "title": title.strip(),
                "subtitle": subtitle.strip() if subtitle else None,
                "ticker_refs_json": _clean_refs(ticker_refs_json),
                "theme_refs_json": _clean_refs(theme_refs_json),
                "summary": summary.strip(),
                "snapshot_payload_json": snapshot_payload_json or {},
                "source_module": source_module,
                "source_ref": source_ref,
                "staleness_hint": staleness_hint,
                "is_pinned": is_pinned,
            }
        )
        if created is None:
            return None
        return self._serialize_context_card(created)

    async def update_context_card(
        self,
        *,
        user_id: str,
        thread_id: int,
        context_id: int,
        title: str | None = None,
        subtitle: str | None = None,
        summary: str | None = None,
        staleness_hint: str | None = None,
        is_pinned: bool | None = None,
    ) -> dict[str, Any] | None:
        payload: dict[str, Any] = {}
        if title is not None:
            payload["title"] = title.strip()
        if subtitle is not None:
            payload["subtitle"] = subtitle.strip()
        if summary is not None:
            payload["summary"] = summary.strip()
        if staleness_hint is not None:
            payload["staleness_hint"] = staleness_hint.strip()
        if is_pinned is not None:
            payload["is_pinned"] = is_pinned
        updated = self.analysis_context_card_repository.update_context_card(
            user_id=user_id,
            thread_id=thread_id,
            context_id=context_id,
            payload=payload,
        )
        if updated is None:
            return None
        return self._serialize_context_card(updated)

    async def delete_context_card(
        self,
        *,
        user_id: str,
        thread_id: int,
        context_id: int,
    ) -> bool:
        return self.analysis_context_card_repository.delete_context_card(
            user_id=user_id,
            thread_id=thread_id,
            context_id=context_id,
        )

    async def import_context(
        self,
        *,
        user_id: str,
        source_module: str,
        source_ref: str,
        target_thread_id: int | None = None,
        create_new_thread: bool = False,
        mode: str = "append",
    ) -> dict[str, Any]:
        normalized_source_module = str(source_module or "").strip()
        if normalized_source_module not in SUPPORTED_SOURCE_MODULES:
            raise ValueError("Only tradingagents_run context import is supported in this phase")
        run_data = await self.tradingagents_service.get_run(source_ref)
        if run_data is None:
            raise ValueError("TradingAgents run not found")

        thread: dict[str, Any] | None = None
        if create_new_thread:
            thread = await self.create_thread(
                user_id=user_id,
                title=f"追问：{run_data.symbol} TradingAgents 分析",
                focus_type="tradingagents_followup",
                ticker_refs_json=[run_data.symbol],
                theme_refs_json=[],
            )
            target_thread_id = int(thread["thread_id"])
        elif target_thread_id is not None:
            thread_obj = self.stock_analysis_thread_repository.get_thread_by_id(
                user_id=user_id,
                thread_id=target_thread_id,
            )
            thread = self._serialize_thread(thread_obj) if thread_obj else None
        if target_thread_id is None or thread is None:
            raise ValueError("A target thread is required for context import")

        context_payload = self._build_tradingagents_context_payload(run_data.model_dump())
        context_card = await self.create_context_card(
            user_id=user_id,
            thread_id=target_thread_id,
            mode=mode,
            **context_payload,
        )
        if context_card is None:
            raise ValueError("Failed to create analysis context card")

        contexts = await self.list_context_cards(
            user_id=user_id,
            thread_id=target_thread_id,
        )
        return {
            "thread": thread,
            "context_card": context_card,
            "contexts": contexts["items"] if contexts else [],
        }

    async def get_workspace_overview(
        self,
        *,
        user_id: str,
        thread_id: int | None = None,
    ) -> dict[str, Any]:
        thread_items = await self.list_threads(user_id=user_id)
        threads = thread_items["items"]
        current_thread = None
        if threads:
            current_thread = (
                next((item for item in threads if item["thread_id"] == thread_id), None)
                if thread_id is not None
                else threads[0]
            )
        context_count = 0
        if current_thread is not None:
            contexts = await self.list_context_cards(
                user_id=user_id,
                thread_id=int(current_thread["thread_id"]),
            )
            context_count = int(contexts["count"]) if contexts else 0
        return {
            "generated_at": _utcnow().isoformat(),
            "threads": threads,
            "current_thread": current_thread,
            "context_count": context_count,
            "available": bool(threads),
            "empty_message": None
            if threads
            else "当前还没有研究线程，先从 TradingAgents 或手动新建一个分析线程开始。",
        }

    async def _sync_conversation_title(self, *, conversation_id: str, title: str) -> None:
        conversation = await self.conversation_service.conversation_manager.get_conversation(
            conversation_id
        )
        if conversation is None:
            return
        conversation.title = title
        await self.conversation_service.conversation_manager.update_conversation(
            conversation
        )

    def _serialize_thread(self, thread: Any | None) -> dict[str, Any] | None:
        if thread is None:
            return None
        data = thread.to_dict()
        contexts = self.analysis_context_card_repository.list_context_cards(
            user_id=thread.user_id,
            thread_id=thread.id,
        )
        data["context_count"] = len(contexts)
        return data

    @staticmethod
    def _serialize_context_card(card: Any) -> dict[str, Any]:
        return card.to_dict()

    @staticmethod
    def _normalize_focus_type(value: str) -> str:
        normalized = str(value or "").strip()
        if normalized not in SUPPORTED_FOCUS_TYPES:
            raise ValueError("Unsupported focus_type")
        return normalized

    @staticmethod
    def _normalize_context_type(value: str) -> str:
        normalized = str(value or "").strip()
        if normalized not in SUPPORTED_CONTEXT_TYPES:
            raise ValueError("Unsupported context_type")
        return normalized

    @staticmethod
    def _normalize_context_mode(value: str) -> str:
        normalized = str(value or "append").strip()
        if normalized not in {"append", "replace"}:
            raise ValueError("Unsupported context mode")
        return normalized

    def _build_tradingagents_context_payload(self, run_data: dict[str, Any]) -> dict[str, Any]:
        symbol = str(run_data.get("symbol") or "")
        summary_payload = run_data.get("summary") or {}
        reports = list(run_data.get("reports") or [])
        final_decision = str(summary_payload.get("final_decision") or "").strip()
        decision_signal = str(run_data.get("decision_signal") or "").strip()
        summary = (
            final_decision
            or decision_signal
            or str(run_data.get("progress_message") or "").strip()
            or f"{symbol} 的 TradingAgents 运行已完成，可作为研究线程上下文继续追问。"
        )
        report_snapshots = [
            {
                "key": item.get("key"),
                "title": item.get("title"),
                "content": str(item.get("content") or "")[:1200],
            }
            for item in reports[:3]
        ]
        subtitle_timestamp = (
            run_data.get("completed_at")
            or run_data.get("updated_at")
            or run_data.get("created_at")
        )
        return {
            "context_type": TRADINGAGENTS_CONTEXT_TYPE,
            "title": f"{symbol} TradingAgents 分析摘要",
            "subtitle": f"{run_data.get('status') or 'unknown'} · {subtitle_timestamp or '--'}",
            "ticker_refs_json": [symbol] if symbol else [],
            "theme_refs_json": [],
            "summary": summary,
            "snapshot_payload_json": {
                "symbol": symbol,
                "run_id": run_data.get("run_id"),
                "status": run_data.get("status"),
                "summary": summary_payload,
                "reports": report_snapshots,
                "final_decision": final_decision or None,
                "decision_signal": decision_signal or None,
            },
            "source_module": "tradingagents_run",
            "source_ref": str(run_data.get("run_id") or ""),
            "staleness_hint": f"请结合 run 时间 {subtitle_timestamp or '--'} 判断该卡片是否仍然新鲜。",
            "is_pinned": True,
        }


_stock_analysis_workspace_service: Optional[StockAnalysisWorkspaceService] = None


def get_stock_analysis_workspace_service() -> StockAnalysisWorkspaceService:
    global _stock_analysis_workspace_service
    if _stock_analysis_workspace_service is None:
        _stock_analysis_workspace_service = StockAnalysisWorkspaceService()
    return _stock_analysis_workspace_service


def reset_stock_analysis_workspace_service() -> None:
    global _stock_analysis_workspace_service
    _stock_analysis_workspace_service = None
