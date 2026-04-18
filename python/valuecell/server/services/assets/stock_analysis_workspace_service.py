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
from .decision_alert_service import DecisionAlertService
from .decision_context_window_service import DecisionContextWindowService
from .decision_effectiveness_service import DecisionEffectivenessService
from .decision_outcome_review_service import DecisionOutcomeReviewService
from .exit_risk_center_service import ExitRiskCenterService
from .holding_lifecycle_service import HoldingLifecycleService
from .opportunity_pool_service import OpportunityPoolService
from .risk_sizing_service import RiskSizingService
from .theme_radar_service import ThemeRadarService
from .watchlist_center_service import WatchlistCenterService

DEFAULT_USER_ID = "default_user"
STOCK_ANALYSIS_AGENT_NAME = "StockAnalysisWorkspace"
TRADINGAGENTS_CONTEXT_TYPE = "tradingagents_run"
HOLDING_CONTEXT_TYPE = "holding"
OPPORTUNITY_CONTEXT_TYPE = "opportunity"
WATCHLIST_CONTEXT_TYPE = "watchlist"
THEME_CONTEXT_TYPE = "theme"
ALERT_CONTEXT_TYPE = "alert"
TICKER_CONTEXT_TYPE = "ticker"
DECISION_CONTEXT_WINDOW_CONTEXT_TYPE = "decision_context_window"
DECISION_OUTCOME_REVIEW_CONTEXT_TYPE = "decision_outcome_review"
RISK_SIZING_CONTEXT_TYPE = "risk_sizing"
DECISION_EFFECTIVENESS_CONTEXT_TYPE = "decision_effectiveness"
TEMPORARY_EVIDENCE_SAVED_CONTEXT_TYPE = "temporary_evidence_saved"
SUPPORTED_SOURCE_MODULES = {
    "tradingagents_run",
    "holding",
    "opportunity",
    "watchlist",
    "theme",
    "alert",
    "ticker",
    "decision_context_window",
    "decision_outcome_review",
    "risk_sizing",
    "decision_effectiveness",
}
SUPPORTED_FOCUS_TYPES = {
    "ticker",
    "theme",
    "comparison",
    "holding",
    "tradingagents_followup",
    "mixed",
}
SUPPORTED_CONTEXT_TYPES = {
    TRADINGAGENTS_CONTEXT_TYPE,
    HOLDING_CONTEXT_TYPE,
    OPPORTUNITY_CONTEXT_TYPE,
    WATCHLIST_CONTEXT_TYPE,
    THEME_CONTEXT_TYPE,
    ALERT_CONTEXT_TYPE,
    TICKER_CONTEXT_TYPE,
    DECISION_CONTEXT_WINDOW_CONTEXT_TYPE,
    DECISION_OUTCOME_REVIEW_CONTEXT_TYPE,
    RISK_SIZING_CONTEXT_TYPE,
    DECISION_EFFECTIVENESS_CONTEXT_TYPE,
    TEMPORARY_EVIDENCE_SAVED_CONTEXT_TYPE,
}


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
        holding_lifecycle_service: Optional[HoldingLifecycleService] = None,
        exit_risk_center_service: Optional[ExitRiskCenterService] = None,
        opportunity_pool_service: Optional[OpportunityPoolService] = None,
        watchlist_center_service: Optional[WatchlistCenterService] = None,
        theme_radar_service: Optional[ThemeRadarService] = None,
        decision_alert_service: Optional[DecisionAlertService] = None,
        decision_context_window_service: Optional[DecisionContextWindowService] = None,
        decision_outcome_review_service: Optional[DecisionOutcomeReviewService] = None,
        risk_sizing_service: Optional[RiskSizingService] = None,
        decision_effectiveness_service: Optional[DecisionEffectivenessService] = None,
    ) -> None:
        self.stock_analysis_thread_repository = (
            stock_analysis_thread_repository or StockAnalysisThreadRepository()
        )
        self.analysis_context_card_repository = (
            analysis_context_card_repository or AnalysisContextCardRepository()
        )
        self.tradingagents_service = tradingagents_service or TradingAgentsService()
        self.conversation_service = conversation_service or ServerConversationService()
        self.holding_lifecycle_service = (
            holding_lifecycle_service or HoldingLifecycleService()
        )
        self.exit_risk_center_service = exit_risk_center_service or ExitRiskCenterService()
        self.opportunity_pool_service = opportunity_pool_service or OpportunityPoolService()
        self.watchlist_center_service = watchlist_center_service or WatchlistCenterService()
        self.theme_radar_service = theme_radar_service or ThemeRadarService()
        self.decision_alert_service = decision_alert_service or DecisionAlertService()
        self.decision_context_window_service = (
            decision_context_window_service or DecisionContextWindowService()
        )
        self.decision_outcome_review_service = (
            decision_outcome_review_service or DecisionOutcomeReviewService()
        )
        self.risk_sizing_service = risk_sizing_service or RiskSizingService()
        self.decision_effectiveness_service = (
            decision_effectiveness_service or DecisionEffectivenessService()
        )

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
            if source_ref:
                deleted_count = self.analysis_context_card_repository.delete_context_cards_by_filter(
                    user_id=user_id,
                    thread_id=thread_id,
                    context_type=normalized_context_type,
                    source_module=source_module,
                    source_ref=source_ref,
                )
                if deleted_count == 0:
                    self.analysis_context_card_repository.delete_context_cards_by_filter(
                        user_id=user_id,
                        thread_id=thread_id,
                        context_type=normalized_context_type,
                        source_module=source_module,
                    )
            else:
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
            raise ValueError("Unsupported stock analysis context source")

        context_payload = await self._build_context_import_payload(
            user_id=user_id,
            source_module=normalized_source_module,
            source_ref=source_ref,
        )

        thread: dict[str, Any] | None = None
        if create_new_thread:
            thread = await self.create_thread(
                user_id=user_id,
                title=self._build_thread_title_from_context(context_payload),
                focus_type=self._resolve_focus_type_from_context(context_payload),
                ticker_refs_json=list(context_payload.get("ticker_refs_json") or []),
                theme_refs_json=list(context_payload.get("theme_refs_json") or []),
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

    async def _build_context_import_payload(
        self,
        *,
        user_id: str,
        source_module: str,
        source_ref: str,
    ) -> dict[str, Any]:
        if source_module == "tradingagents_run":
            run_data = await self.tradingagents_service.get_run(source_ref)
            if run_data is None:
                raise ValueError("TradingAgents run not found")
            return self._build_tradingagents_context_payload(run_data.model_dump())
        if source_module == "holding":
            return self._build_holding_context_payload(user_id=user_id, source_ref=source_ref)
        if source_module == "opportunity":
            return self._build_opportunity_context_payload(
                user_id=user_id,
                source_ref=source_ref,
            )
        if source_module == "watchlist":
            return self._build_watchlist_context_payload(
                user_id=user_id,
                source_ref=source_ref,
            )
        if source_module == "theme":
            return self._build_theme_context_payload(user_id=user_id, source_ref=source_ref)
        if source_module == "alert":
            return self._build_alert_context_payload(user_id=user_id, source_ref=source_ref)
        if source_module == "ticker":
            return self._build_ticker_context_payload(source_ref=source_ref)
        if source_module == "decision_context_window":
            return self._build_decision_context_window_payload(
                user_id=user_id,
                source_ref=source_ref,
            )
        if source_module == "decision_outcome_review":
            return self._build_decision_outcome_review_payload(
                user_id=user_id,
                source_ref=source_ref,
            )
        if source_module == "risk_sizing":
            return self._build_risk_sizing_payload(user_id=user_id, source_ref=source_ref)
        if source_module == "decision_effectiveness":
            return self._build_decision_effectiveness_payload(
                user_id=user_id,
                source_ref=source_ref,
            )
        raise ValueError("Unsupported stock analysis context source")

    def _build_holding_context_payload(
        self,
        *,
        user_id: str,
        source_ref: str,
    ) -> dict[str, Any]:
        lifecycle_overview = self.holding_lifecycle_service.get_overview(user_id)
        exit_risk_overview = self.exit_risk_center_service.get_overview(user_id)
        item = self._find_by_keys(
            lifecycle_overview.get("items") or [],
            source_ref,
            keys=("holding_id", "ticker"),
        )
        if item is None:
            raise ValueError("Holding context source not found")
        risk_item = self._find_by_keys(
            self._merge_exit_risk_groups(exit_risk_overview),
            str(item.get("ticker") or ""),
            keys=("ticker",),
        )
        display_name = str(item.get("display_name") or item.get("ticker") or "")
        lifecycle_stage = str(item.get("lifecycle_stage") or "待观察")
        action = str(item.get("action") or "持有观察")
        reasons = [
            text
            for text in [
                str((risk_item or {}).get("risk_type") or "").strip(),
                str((risk_item or {}).get("liquidity_warning") or "").strip(),
            ]
            if text
        ][:2]
        summary = (
            f"{display_name} 当前处于 {lifecycle_stage}，主动作偏 {action}。"
            f"{' 风险要点：' + '；'.join(reasons) if reasons else ''}"
        )
        return {
            "context_type": HOLDING_CONTEXT_TYPE,
            "title": f"{display_name} 持仓处理摘要",
            "subtitle": f"{lifecycle_stage} · {action}",
            "ticker_refs_json": [str(item.get('ticker') or '')],
            "theme_refs_json": [str(item.get("theme_name") or "").strip()]
            if str(item.get("theme_name") or "").strip()
            else [],
            "summary": summary,
            "snapshot_payload_json": {
                "ticker": item.get("ticker"),
                "display_name": display_name,
                "lifecycle_stage": lifecycle_stage,
                "action": action,
                "role_label": item.get("role_label"),
                "risk_points": reasons,
            },
            "source_module": "holding",
            "source_ref": str(item.get("holding_id") or item.get("ticker") or ""),
            "staleness_hint": "若持仓阶段或风险中心发生变化，请刷新后重新导入。",
            "is_pinned": False,
        }

    def _build_opportunity_context_payload(
        self,
        *,
        user_id: str,
        source_ref: str,
    ) -> dict[str, Any]:
        opportunity_result = self.opportunity_pool_service.get_opportunity_candidates(user_id)
        item = self._find_by_keys(
            opportunity_result.get("items") or [],
            source_ref,
            keys=("ticker",),
        )
        if item is None:
            raise ValueError("Opportunity context source not found")
        display_name = str(item.get("display_name") or item.get("ticker") or "")
        topic_name = str(item.get("topic_name") or "").strip()
        candidate_state = str(item.get("candidate_state") or "普通观察")
        action_hint = str(item.get("action_hint") or "").strip()
        reason_bits = [
            text
            for text in [
                candidate_state,
                action_hint,
                str(item.get("tradeability_state") or "").strip(),
            ]
            if text
        ]
        summary = f"{display_name} 当前题材为 {topic_name or '未分类'}，{'；'.join(reason_bits[:3])}。"
        return {
            "context_type": OPPORTUNITY_CONTEXT_TYPE,
            "title": f"{display_name} 机会池摘要",
            "subtitle": f"{topic_name or '未分类'} · {candidate_state}",
            "ticker_refs_json": [str(item.get('ticker') or '')],
            "theme_refs_json": [topic_name] if topic_name else [],
            "summary": summary,
            "snapshot_payload_json": {
                "ticker": item.get("ticker"),
                "display_name": display_name,
                "topic_name": topic_name,
                "candidate_state": candidate_state,
                "action_hint": action_hint,
                "role_label": item.get("role_label"),
            },
            "source_module": "opportunity",
            "source_ref": str(item.get("ticker") or ""),
            "staleness_hint": "机会池阶段变化较快，建议结合当日状态复核。",
            "is_pinned": False,
        }

    def _build_watchlist_context_payload(
        self,
        *,
        user_id: str,
        source_ref: str,
    ) -> dict[str, Any]:
        watchlist_result = self.watchlist_center_service.get_overview(user_id)
        item = self._find_by_keys(
            watchlist_result.get("items") or [],
            source_ref,
            keys=("ticker",),
        )
        if item is None:
            raise ValueError("Watchlist context source not found")
        display_name = str(item.get("display_name") or item.get("ticker") or "")
        status = str(item.get("status") or "普通观察")
        reason = str(item.get("reason") or "").strip()
        tradeability_state = str(item.get("tradeability_state") or "").strip()
        expectation_gap = str(item.get("expectation_gap_level") or "").strip()
        summary = (
            f"{display_name} 当前观察状态为 {status}。"
            f"{reason or '暂无额外理由。'}"
            f"{' 可交易性：' + tradeability_state if tradeability_state else ''}"
            f"{'，预期差：' + expectation_gap if expectation_gap else ''}"
        )
        theme_name = str(item.get("theme_name") or "").strip()
        return {
            "context_type": WATCHLIST_CONTEXT_TYPE,
            "title": f"{display_name} 观察池摘要",
            "subtitle": f"{status} · {tradeability_state or '待确认'}",
            "ticker_refs_json": [str(item.get('ticker') or '')],
            "theme_refs_json": [theme_name] if theme_name else [],
            "summary": summary,
            "snapshot_payload_json": {
                "ticker": item.get("ticker"),
                "display_name": display_name,
                "status": status,
                "reason": reason,
                "tradeability_state": tradeability_state,
                "expectation_gap_level": expectation_gap,
                "quick_note": item.get("quick_note"),
            },
            "source_module": "watchlist",
            "source_ref": str(item.get("ticker") or ""),
            "staleness_hint": "观察池标签与优先级可能日级变化，建议结合当前页面状态复核。",
            "is_pinned": False,
        }

    def _build_theme_context_payload(
        self,
        *,
        user_id: str,
        source_ref: str,
    ) -> dict[str, Any]:
        theme_result = self.theme_radar_service.get_overview(user_id)
        item = self._find_by_keys(
            theme_result.get("items") or [],
            source_ref,
            keys=("theme_code", "theme_name"),
        )
        if item is None:
            raise ValueError("Theme context source not found")
        theme_name = str(item.get("theme_name") or source_ref)
        state = str(item.get("theme_state") or "分歧")
        participation_hint = str(item.get("participation_hint") or "").strip()
        representative_tickers = [
            str(ticker).strip()
            for ticker in list(item.get("representative_tickers") or [])[:4]
            if str(ticker).strip()
        ]
        risk_tags = [str(tag).strip() for tag in list(item.get("risk_tags") or []) if str(tag).strip()]
        summary = (
            f"{theme_name} 当前状态为 {state}。"
            f"{str(item.get('observation_summary') or '').strip()}"
            f"{' 风险提示：' + '；'.join(risk_tags[:2]) if risk_tags else ''}"
        )
        return {
            "context_type": THEME_CONTEXT_TYPE,
            "title": f"{theme_name} 题材摘要",
            "subtitle": f"{state} · 代表股 {representative_tickers[0] if representative_tickers else '--'}",
            "ticker_refs_json": representative_tickers,
            "theme_refs_json": [theme_name],
            "summary": summary,
            "snapshot_payload_json": {
                "theme_code": item.get("theme_code"),
                "theme_name": theme_name,
                "theme_state": state,
                "representative_tickers": representative_tickers,
                "participation_hint": participation_hint,
                "risk_tags": risk_tags[:3],
            },
            "source_module": "theme",
            "source_ref": str(item.get("theme_code") or theme_name),
            "staleness_hint": "题材状态与参与边界可能快速变化，建议结合当前题材雷达复核。",
            "is_pinned": False,
        }

    def _build_alert_context_payload(
        self,
        *,
        user_id: str,
        source_ref: str,
    ) -> dict[str, Any]:
        alert_result = self.decision_alert_service.get_decision_alert_summary(user_id)
        normalized_ref = str(source_ref or "").strip()
        alert_items = list(alert_result.get("items") or [])
        item = next(
            (
                entry
                for entry in alert_items
                if normalized_ref
                in {
                    str(entry.get("ticker") or "").strip(),
                    f"{str(entry.get('ticker') or '').strip()}|{str(entry.get('alert_type') or '').strip()}",
                }
            ),
            None,
        )
        if item is None:
            raise ValueError("Alert context source not found")
        display_name = str(item.get("display_name") or item.get("ticker") or "")
        alert_type = str(item.get("alert_type") or "提醒")
        body = str(item.get("body") or "").strip()
        next_action = str(item.get("next_action") or "").strip()
        reasons = [str(text).strip() for text in list(item.get("reasons") or []) if str(text).strip()]
        summary = (
            f"{display_name} 当前提醒类型为 {alert_type}。"
            f"{body}{' 下一步：' + next_action if next_action else ''}"
        )
        topic_name = str(item.get("topic_name") or "").strip()
        return {
            "context_type": ALERT_CONTEXT_TYPE,
            "title": f"{display_name} 提醒摘要",
            "subtitle": f"{alert_type} · {item.get('priority') or 'normal'}",
            "ticker_refs_json": [str(item.get('ticker') or '')] if str(item.get("ticker") or "").strip() else [],
            "theme_refs_json": [topic_name] if topic_name else [],
            "summary": summary,
            "snapshot_payload_json": {
                "ticker": item.get("ticker"),
                "display_name": display_name,
                "alert_type": alert_type,
                "body": body,
                "next_action": next_action,
                "reasons": reasons[:3],
            },
            "source_module": "alert",
            "source_ref": f"{str(item.get('ticker') or '').strip()}|{alert_type}",
            "staleness_hint": "提醒依赖当前时点状态，建议在新一轮判断前复核是否仍有效。",
            "is_pinned": False,
        }

    def _build_ticker_context_payload(self, *, source_ref: str) -> dict[str, Any]:
        ticker = str(source_ref or "").strip()
        if not ticker:
            raise ValueError("Ticker context source is empty")
        return {
            "context_type": TICKER_CONTEXT_TYPE,
            "title": f"{ticker} 基础观察卡",
            "subtitle": "轻量 ticker context",
            "ticker_refs_json": [ticker],
            "theme_refs_json": [],
            "summary": f"当前仅挂入 {ticker} 的轻量 ticker context，若需更完整研究，请继续导入持仓、机会池、观察池或题材上下文。",
            "snapshot_payload_json": {"ticker": ticker},
            "source_module": "ticker",
            "source_ref": ticker,
            "staleness_hint": "该卡片不含自动补数，仅用于建立最轻量研究锚点。",
            "is_pinned": False,
        }

    def _build_decision_context_window_payload(
        self,
        *,
        user_id: str,
        source_ref: str,
    ) -> dict[str, Any]:
        window_result = self.decision_context_window_service.list_windows(
            user_id=user_id,
            limit=120,
        )
        item = self._find_by_keys(
            window_result.get("items") or [],
            source_ref,
            keys=("window_id", "ticker", "theme_name"),
        )
        if item is None:
            raise ValueError("Decision context window source not found")
        ticker = str(item.get("ticker") or "").strip()
        theme_name = str(item.get("theme_name") or "").strip()
        support_points = [str(point).strip() for point in list(item.get("support_points") or []) if str(point).strip()]
        opposing_points = [
            str(point).strip() for point in list(item.get("opposing_points") or []) if str(point).strip()
        ]
        risk_points = [str(point).strip() for point in list(item.get("risk_points") or []) if str(point).strip()]
        title_anchor = ticker or theme_name or "当前研究对象"
        summary = (
            f"{title_anchor} 决策窗口支持点 {support_points[0] if support_points else '待确认'}；"
            f"反对点 {opposing_points[0] if opposing_points else '待确认'}；"
            f"风险提示 {risk_points[0] if risk_points else '待确认'}。"
        )
        return {
            "context_type": DECISION_CONTEXT_WINDOW_CONTEXT_TYPE,
            "title": f"{title_anchor} 决策上下文窗口",
            "subtitle": f"{item.get('action') or '待判断'} · {item.get('window_date') or '--'}",
            "ticker_refs_json": [ticker] if ticker else [],
            "theme_refs_json": [theme_name] if theme_name else [],
            "summary": summary,
            "snapshot_payload_json": {
                "window_id": item.get("window_id"),
                "ticker": ticker or None,
                "theme_name": theme_name or None,
                "action": item.get("action"),
                "support_points": support_points[:3],
                "opposing_points": opposing_points[:3],
                "risk_points": risk_points[:3],
            },
            "source_module": DECISION_CONTEXT_WINDOW_CONTEXT_TYPE,
            "source_ref": str(item.get("window_id") or source_ref),
            "staleness_hint": "决策窗口反映当时判断语境，不等于当前最新事实。",
            "is_pinned": False,
        }

    def _build_decision_outcome_review_payload(
        self,
        *,
        user_id: str,
        source_ref: str,
    ) -> dict[str, Any]:
        review_result = self.decision_outcome_review_service.list_reviews(
            user_id=user_id,
            limit=120,
        )
        item = self._find_by_keys(
            review_result.get("items") or [],
            source_ref,
            keys=("review_id", "ticker"),
        )
        if item is None:
            raise ValueError("Decision outcome review source not found")
        ticker = str(item.get("ticker") or "").strip()
        display_name = str(item.get("display_name") or ticker or "")
        status = str(item.get("outcome_status") or "数据不足")
        summary = (
            f"{display_name} 该条判断结果为 {status}。"
            f"{str(item.get('summary') or '').strip() or str(item.get('what_happened') or '').strip()}"
        )
        return {
            "context_type": DECISION_OUTCOME_REVIEW_CONTEXT_TYPE,
            "title": f"{display_name} 判断结果回看",
            "subtitle": f"{status} · {item.get('review_horizon_days') or '--'} 日",
            "ticker_refs_json": [ticker] if ticker else [],
            "theme_refs_json": [],
            "summary": summary,
            "snapshot_payload_json": {
                "review_id": item.get("review_id"),
                "ticker": ticker or None,
                "display_name": display_name,
                "outcome_status": status,
                "outcome_score": item.get("outcome_score"),
                "review_horizon_days": item.get("review_horizon_days"),
                "what_was_right": item.get("what_was_right"),
                "what_was_wrong": item.get("what_was_wrong"),
            },
            "source_module": DECISION_OUTCOME_REVIEW_CONTEXT_TYPE,
            "source_ref": str(item.get("review_id") or source_ref),
            "staleness_hint": "结果回看是历史复盘证据，建议与当前上下文一起使用。",
            "is_pinned": False,
        }

    def _build_risk_sizing_payload(
        self,
        *,
        user_id: str,
        source_ref: str,
    ) -> dict[str, Any]:
        normalized_ref = str(source_ref or "").strip() or "__portfolio__"
        if normalized_ref == "__portfolio__":
            summary_result = self.risk_sizing_service.get_summary(user_id=user_id)
            if not summary_result.get("available"):
                raise ValueError("Risk sizing summary is not available")
            return {
                "context_type": RISK_SIZING_CONTEXT_TYPE,
                "title": "组合分仓建议",
                "subtitle": f"{summary_result.get('market_risk_level') or '待确认'} · 组合层",
                "ticker_refs_json": [],
                "theme_refs_json": [],
                "summary": (
                    f"当前建议总仓位 {summary_result.get('suggested_total_exposure_range') or '待确认'}，"
                    f"单票建议 {summary_result.get('suggested_single_position_range') or '待确认'}。"
                ),
                "snapshot_payload_json": {
                    "market_risk_level": summary_result.get("market_risk_level"),
                    "suggested_total_exposure_range": summary_result.get(
                        "suggested_total_exposure_range"
                    ),
                    "suggested_single_position_range": summary_result.get(
                        "suggested_single_position_range"
                    ),
                    "position_guidance": summary_result.get("position_guidance"),
                },
                "source_module": RISK_SIZING_CONTEXT_TYPE,
                "source_ref": "__portfolio__",
                "staleness_hint": "分仓建议依赖当前市场环境与风险状态，建议日级复核。",
                "is_pinned": False,
            }
        ticker_result = self.risk_sizing_service.get_ticker_summary(
            user_id=user_id,
            ticker=normalized_ref,
        )
        if not ticker_result.get("available"):
            raise ValueError("Risk sizing ticker summary is not available")
        ticker = str(ticker_result.get("ticker") or normalized_ref)
        display_name = str(ticker_result.get("display_name") or ticker)
        risk_level = str(ticker_result.get("risk_level") or "待确认")
        return {
            "context_type": RISK_SIZING_CONTEXT_TYPE,
            "title": f"{display_name} 分仓建议",
            "subtitle": f"{risk_level} · {ticker_result.get('suggested_position_range') or '待确认'}",
            "ticker_refs_json": [ticker],
            "theme_refs_json": [],
            "summary": (
                f"{display_name} 当前建议仓位 {ticker_result.get('suggested_position_range') or '待确认'}，"
                f"风险等级 {risk_level}。{ticker_result.get('guidance') or ''}"
            ),
            "snapshot_payload_json": {
                "ticker": ticker,
                "display_name": display_name,
                "risk_level": risk_level,
                "suggested_position_range": ticker_result.get("suggested_position_range"),
                "guidance": ticker_result.get("guidance"),
            },
            "source_module": RISK_SIZING_CONTEXT_TYPE,
            "source_ref": ticker,
            "staleness_hint": "单票分仓建议会随市场环境和持仓阶段变化。",
            "is_pinned": False,
        }

    def _build_decision_effectiveness_payload(
        self,
        *,
        user_id: str,
        source_ref: str,
    ) -> dict[str, Any]:
        del source_ref
        summary_result = self.decision_effectiveness_service.get_summary(user_id=user_id)
        if not summary_result.get("available"):
            raise ValueError("Decision effectiveness summary is not available")
        return {
            "context_type": DECISION_EFFECTIVENESS_CONTEXT_TYPE,
            "title": "近期判断有效性摘要",
            "subtitle": f"得分 {summary_result.get('overall_score') or 0} · {summary_result.get('review_count') or 0} 条",
            "ticker_refs_json": [],
            "theme_refs_json": [],
            "summary": str(summary_result.get("overall_summary") or "暂无有效性摘要"),
            "snapshot_payload_json": {
                "overall_summary": summary_result.get("overall_summary"),
                "overall_score": summary_result.get("overall_score"),
                "review_count": summary_result.get("review_count"),
                "effective_count": summary_result.get("effective_count"),
                "failed_count": summary_result.get("failed_count"),
            },
            "source_module": DECISION_EFFECTIVENESS_CONTEXT_TYPE,
            "source_ref": "__summary__",
            "staleness_hint": "有效性摘要反映近期复盘窗口，不等于未来收益保证。",
            "is_pinned": False,
        }

    @staticmethod
    def _build_thread_title_from_context(context_payload: dict[str, Any]) -> str:
        ticker_refs = list(context_payload.get("ticker_refs_json") or [])
        theme_refs = list(context_payload.get("theme_refs_json") or [])
        source_module = str(context_payload.get("source_module") or "")
        if source_module == "tradingagents_run" and ticker_refs:
            return f"追问：{ticker_refs[0]} TradingAgents 分析"
        if source_module == "theme" and theme_refs:
            return f"追问：{theme_refs[0]} 题材研究"
        if ticker_refs:
            return f"追问：{ticker_refs[0]} 研究线程"
        if theme_refs:
            return f"追问：{theme_refs[0]} 研究线程"
        return "新建股票分析线程"

    @staticmethod
    def _resolve_focus_type_from_context(context_payload: dict[str, Any]) -> str:
        source_module = str(context_payload.get("source_module") or "")
        ticker_refs = list(context_payload.get("ticker_refs_json") or [])
        theme_refs = list(context_payload.get("theme_refs_json") or [])
        if source_module == "tradingagents_run":
            return "tradingagents_followup"
        if ticker_refs and theme_refs:
            return "mixed"
        if theme_refs:
            return "theme"
        if source_module == "holding":
            return "holding"
        if ticker_refs:
            return "ticker"
        return "mixed"

    @staticmethod
    def _find_by_keys(
        items: Sequence[dict[str, Any]],
        source_ref: str,
        *,
        keys: Sequence[str],
    ) -> dict[str, Any] | None:
        normalized_ref = str(source_ref or "").strip()
        for item in items:
            for key in keys:
                value = str(item.get(key) or "").strip()
                if value and value == normalized_ref:
                    return item
        return None

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
                action = str(item.get("action") or "")
                if not any(
                    str(existing.get("ticker") or "") == ticker
                    and str(existing.get("action") or "") == action
                    for existing in merged
                ):
                    merged.append(item)
        return merged


_stock_analysis_workspace_service: Optional[StockAnalysisWorkspaceService] = None


def get_stock_analysis_workspace_service() -> StockAnalysisWorkspaceService:
    global _stock_analysis_workspace_service
    if _stock_analysis_workspace_service is None:
        _stock_analysis_workspace_service = StockAnalysisWorkspaceService()
    return _stock_analysis_workspace_service


def reset_stock_analysis_workspace_service() -> None:
    global _stock_analysis_workspace_service
    _stock_analysis_workspace_service = None
