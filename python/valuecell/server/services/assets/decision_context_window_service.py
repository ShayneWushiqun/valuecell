from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any, Optional

from loguru import logger

from ...db.repositories.decision_context_window_repository import (
    DecisionContextWindowRepository,
)
from ...db.repositories.short_cycle_context_event_repository import (
    ShortCycleContextEventRepository,
)
from .ashare_decision_judge_service import AShareDecisionJudgeService
from .decision_record_service import DecisionRecordService
from .exit_risk_center_service import ExitRiskCenterService
from .holding_lifecycle_service import HoldingLifecycleService
from .short_cycle_context_event_service import ShortCycleContextEventService

WINDOW_SIZES = (10, 20, 40)


class DecisionContextWindowService:
    def __init__(
        self,
        decision_context_window_repository: Optional[DecisionContextWindowRepository] = None,
        short_cycle_context_event_repository: Optional[ShortCycleContextEventRepository] = None,
        short_cycle_context_event_service: Optional[ShortCycleContextEventService] = None,
        holding_lifecycle_service: Optional[HoldingLifecycleService] = None,
        exit_risk_center_service: Optional[ExitRiskCenterService] = None,
        ashare_decision_judge_service: Optional[AShareDecisionJudgeService] = None,
        decision_record_service: Optional[DecisionRecordService] = None,
    ) -> None:
        self.decision_context_window_repository = (
            decision_context_window_repository or DecisionContextWindowRepository()
        )
        self.short_cycle_context_event_repository = (
            short_cycle_context_event_repository or ShortCycleContextEventRepository()
        )
        self.short_cycle_context_event_service = (
            short_cycle_context_event_service or ShortCycleContextEventService()
        )
        self.holding_lifecycle_service = holding_lifecycle_service or HoldingLifecycleService()
        self.exit_risk_center_service = exit_risk_center_service or ExitRiskCenterService()
        self.ashare_decision_judge_service = (
            ashare_decision_judge_service or AShareDecisionJudgeService()
        )
        self.decision_record_service = decision_record_service or DecisionRecordService()

    def list_windows(
        self,
        *,
        user_id: str,
        ticker: str | None = None,
        window_size: int | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        windows = self.decision_context_window_repository.list_windows(
            user_id=user_id,
            ticker=ticker,
            window_size=window_size,
            limit=limit,
        )
        items = [self._normalize_window(window.to_dict()) for window in windows]
        items.sort(key=self._sort_key)
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "items": items,
            "count": len(items),
        }

    def get_window_detail(self, *, user_id: str, window_id: int) -> dict[str, Any] | None:
        window = self.decision_context_window_repository.get_window_by_id(
            user_id=user_id,
            window_id=window_id,
        )
        return self._normalize_window(window.to_dict()) if window else None

    def refresh_windows(
        self,
        *,
        user_id: str,
        ticker: str | None = None,
    ) -> dict[str, Any]:
        event_refresh = self.short_cycle_context_event_service.refresh_events(
            user_id=user_id,
            ticker=ticker,
        )
        target_tickers = self._resolve_target_tickers(event_refresh.get("items") or [], ticker=ticker)
        lifecycle_items = list(self.holding_lifecycle_service.get_overview(user_id).get("items") or [])
        lifecycle_by_ticker = {
            str(item.get("ticker") or ""): item for item in lifecycle_items if str(item.get("ticker") or "")
        }
        exit_risk_items = self._merge_exit_risk_groups(
            self.exit_risk_center_service.get_overview(user_id)
        )
        exit_risk_by_ticker = {
            str(item.get("ticker") or ""): item for item in exit_risk_items if str(item.get("ticker") or "")
        }
        decision_records = list(
            self.decision_record_service.list_records(user_id=user_id, limit=100).get("items") or []
        )
        decision_record_by_ticker: dict[str, dict[str, Any]] = {}
        for item in decision_records:
            ticker_key = str(item.get("ticker") or "")
            if ticker_key and ticker_key not in decision_record_by_ticker:
                decision_record_by_ticker[ticker_key] = item
        saved_items: list[dict[str, Any]] = []
        today = datetime.now().astimezone().date()

        for target_ticker in target_tickers:
            all_events = [
                item.to_dict()
                for item in self.short_cycle_context_event_repository.list_events(
                    user_id=user_id,
                    ticker=target_ticker,
                    limit=200,
                )
            ]
            for current_window_size in WINDOW_SIZES:
                window_start = (today - timedelta(days=current_window_size)).isoformat()
                window_events = self._select_window_events(all_events, window_start=window_start)
                lifecycle_item = lifecycle_by_ticker.get(target_ticker)
                exit_risk_item = exit_risk_by_ticker.get(target_ticker)
                decision_record_item = decision_record_by_ticker.get(target_ticker)
                payload = self._build_window_payload(
                    user_id=user_id,
                    ticker=target_ticker,
                    window_size=current_window_size,
                    window_end=today.isoformat(),
                    window_start=window_start,
                    events=window_events,
                    lifecycle_item=lifecycle_item,
                    exit_risk_item=exit_risk_item,
                    decision_record_item=decision_record_item,
                )
                saved = self._upsert_window(user_id=user_id, payload=payload)
                saved_items.append(saved)

        logger.info(
            "Refreshed decision context windows count={count} tickers={ticker_count}",
            count=len(saved_items),
            ticker_count=len(target_tickers),
        )
        saved_items.sort(key=self._sort_key)
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "items": saved_items,
            "count": len(saved_items),
        }

    def _upsert_window(self, *, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        existing = self.decision_context_window_repository.get_window_by_dedupe_key(
            user_id=user_id,
            dedupe_key=str(payload["dedupe_key"]),
        )
        if existing is None:
            saved = self.decision_context_window_repository.create_window(payload)
        else:
            saved = self.decision_context_window_repository.update_window(
                int(existing.id),
                {key: value for key, value in payload.items() if key not in {"user_id", "dedupe_key"}},
            )
        normalized = self._normalize_window(saved.to_dict()) if saved else self._fallback_window(payload)
        return normalized

    @staticmethod
    def _resolve_target_tickers(events: list[dict[str, Any]], *, ticker: str | None) -> list[str]:
        if ticker:
            return [ticker]
        tickers: list[str] = []
        for event in events:
            ticker_value = str(event.get("ticker") or "").strip()
            if ticker_value and ticker_value not in tickers:
                tickers.append(ticker_value)
        return tickers

    @staticmethod
    def _merge_exit_risk_groups(overview: dict[str, Any]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for key in (
            "high_priority_items",
            "profit_protection_items",
            "discipline_stop_items",
            "watch_items",
        ):
            for item in list(overview.get(key) or []):
                ticker_key = str(item.get("ticker") or "")
                if ticker_key and not any(str(existing.get("ticker") or "") == ticker_key for existing in items):
                    items.append(item)
        return items

    @staticmethod
    def _select_window_events(
        events: list[dict[str, Any]],
        *,
        window_start: str,
    ) -> list[dict[str, Any]]:
        selected: list[dict[str, Any]] = []
        for event in events:
            record_date = str(event.get("record_date") or "")
            if record_date and record_date >= window_start:
                selected.append(event)
        return selected

    def _build_window_payload(
        self,
        *,
        user_id: str,
        ticker: str,
        window_size: int,
        window_end: str,
        window_start: str,
        events: list[dict[str, Any]],
        lifecycle_item: dict[str, Any] | None,
        exit_risk_item: dict[str, Any] | None,
        decision_record_item: dict[str, Any] | None,
    ) -> dict[str, Any]:
        support_events = self._summarize_events(events, category="support")
        opposing_events = self._summarize_events(events, category="opposing")
        risk_events = self._summarize_events(events, category="risk")
        display_name = str(
            (lifecycle_item or {}).get("display_name")
            or (exit_risk_item or {}).get("display_name")
            or (decision_record_item or {}).get("display_name")
            or ticker
        )
        topic_name = (
            (lifecycle_item or {}).get("theme_name")
            or (exit_risk_item or {}).get("theme_name")
            or (decision_record_item or {}).get("theme_name")
        )
        market_state = self._pick_state(events, layer="market", key="market_state")
        position_state = self._resolve_position_state(lifecycle_item, exit_risk_item)
        expectation_state = (
            (lifecycle_item or {}).get("expectation_state")
            or (decision_record_item or {}).get("expectation_state")
        )
        tradeability_state = (
            (lifecycle_item or {}).get("tradeability_state")
            or (decision_record_item or {}).get("tradeability_state")
        )
        role_label = (lifecycle_item or {}).get("role_label") or (decision_record_item or {}).get("role_label")
        trend_quality = (lifecycle_item or {}).get("trend_quality")
        exit_liquidity_plan = self._resolve_exit_liquidity_plan(exit_risk_item, risk_events)
        judge_result = self.ashare_decision_judge_service.judge(
            ticker=ticker,
            user_id=user_id,
            enable_agent=False,
            force_refresh_context=False,
            user_note=None,
        )
        linked_tags = self._build_linked_tags(lifecycle_item, exit_risk_item, decision_record_item, events)
        risk_level = self._resolve_risk_level(risk_events, exit_risk_item)
        disagreement_level = self._resolve_disagreement_level(
            support_events=support_events,
            opposing_events=opposing_events,
            risk_events=risk_events,
        )
        summary = self._build_summary(
            ticker=ticker,
            support_count=len(support_events),
            opposing_count=len(opposing_events),
            risk_count=len(risk_events),
            role_label=str(role_label or ""),
            risk_level=risk_level,
            disagreement_level=disagreement_level,
        )
        dedupe_key = "|".join([user_id, ticker, str(window_size), window_end])
        return {
            "user_id": user_id,
            "ticker": ticker,
            "display_name": display_name,
            "topic_name": topic_name,
            "window_start": window_start,
            "window_end": window_end,
            "window_size": window_size,
            "market_state": market_state,
            "position_state": position_state,
            "expectation_state": expectation_state,
            "tradeability_state": tradeability_state,
            "role_label": role_label,
            "trend_quality": trend_quality,
            "exit_liquidity_plan": exit_liquidity_plan,
            "support_events_json": support_events,
            "opposing_events_json": opposing_events,
            "risk_events_json": risk_events,
            "summary": summary,
            "judgement_snapshot_json": {
                "action": judge_result.get("action"),
                "confidence": judge_result.get("confidence"),
                "summary": judge_result.get("summary"),
                "invalid_conditions": judge_result.get("invalid_conditions") or [],
                "risk_controls": judge_result.get("risk_controls") or [],
                "linked_tags_json": linked_tags,
                "risk_level": risk_level,
                "disagreement_level": disagreement_level,
                "has_holding": "holding" in linked_tags,
                "has_watchlist": "watchlist" in linked_tags,
                "has_opportunity": "opportunity" in linked_tags,
                "support_count": len(support_events),
                "opposing_count": len(opposing_events),
                "risk_count": len(risk_events),
            },
            "available": True,
            "dedupe_key": dedupe_key,
        }

    @staticmethod
    def _summarize_events(events: list[dict[str, Any]], *, category: str) -> list[dict[str, Any]]:
        selected: list[dict[str, Any]] = []
        for event in events:
            direction = str(event.get("direction") or "neutral")
            if category == "support" and direction not in {"bullish", "confirm"}:
                continue
            if category == "opposing" and direction not in {"neutral", "bearish"}:
                continue
            if category == "risk" and direction != "risk":
                continue
            selected.append(
                {
                    "event_id": event.get("event_id"),
                    "event_type": event.get("event_type"),
                    "layer": event.get("layer"),
                    "source": event.get("source"),
                    "direction": direction,
                    "importance_score": event.get("importance_score"),
                    "summary": event.get("summary"),
                    "tradeability_hint": event.get("tradeability_hint"),
                }
            )
        selected.sort(
            key=lambda item: -int(item.get("importance_score") or 0),
        )
        return selected[:6]

    @staticmethod
    def _pick_state(events: list[dict[str, Any]], *, layer: str, key: str) -> str | None:
        for event in events:
            if str(event.get("layer") or "") == layer:
                return (event.get("payload_json") or {}).get(key)
        return None

    @staticmethod
    def _resolve_position_state(
        lifecycle_item: dict[str, Any] | None,
        exit_risk_item: dict[str, Any] | None,
    ) -> str | None:
        if lifecycle_item:
            return str(lifecycle_item.get("lifecycle_stage") or "") or None
        if exit_risk_item:
            return str(exit_risk_item.get("action") or "") or None
        return None

    @staticmethod
    def _resolve_exit_liquidity_plan(
        exit_risk_item: dict[str, Any] | None,
        risk_events: list[dict[str, Any]],
    ) -> str | None:
        if exit_risk_item and exit_risk_item.get("liquidity_warning"):
            return str(exit_risk_item.get("liquidity_warning"))
        for event in risk_events:
            tradeability_hint = str(event.get("tradeability_hint") or "")
            if tradeability_hint:
                return tradeability_hint
        return None

    @staticmethod
    def _build_linked_tags(
        lifecycle_item: dict[str, Any] | None,
        exit_risk_item: dict[str, Any] | None,
        decision_record_item: dict[str, Any] | None,
        events: list[dict[str, Any]],
    ) -> list[str]:
        tags: list[str] = []
        if lifecycle_item:
            tags.append("holding")
        if decision_record_item:
            tags.append("decision_record")
        if exit_risk_item:
            tags.append("risk_center")
        for event in events:
            source = str(event.get("source") or "")
            if source == "watchlist_center" and "watchlist" not in tags:
                tags.append("watchlist")
            if source == "opportunity_pool" and "opportunity" not in tags:
                tags.append("opportunity")
            if source == "decision_alerts" and "alerts" not in tags:
                tags.append("alerts")
        return tags

    @staticmethod
    def _resolve_risk_level(
        risk_events: list[dict[str, Any]],
        exit_risk_item: dict[str, Any] | None,
    ) -> str:
        if exit_risk_item and str(exit_risk_item.get("action") or "") in {"纪律止损", "保护利润", "减仓观察"}:
            return "高"
        if len(risk_events) >= 2:
            return "高"
        if len(risk_events) == 1:
            return "中"
        return "低"

    @staticmethod
    def _resolve_disagreement_level(
        *,
        support_events: list[dict[str, Any]],
        opposing_events: list[dict[str, Any]],
        risk_events: list[dict[str, Any]],
    ) -> str:
        if support_events and (opposing_events or risk_events):
            return "高"
        if opposing_events:
            return "中"
        return "低"

    @staticmethod
    def _build_summary(
        *,
        ticker: str,
        support_count: int,
        opposing_count: int,
        risk_count: int,
        role_label: str,
        risk_level: str,
        disagreement_level: str,
    ) -> str:
        base = f"{ticker} 最近时间窗内支持证据 {support_count} 条，反对证据 {opposing_count} 条，风险证据 {risk_count} 条。"
        if risk_level == "高":
            return f"{base} 当前风险偏强，优先看退出与失效条件，再决定是否继续观察。"
        if disagreement_level == "高":
            role_text = role_label or "当前标的"
            return f"{base} 当前支持与反对并存，需重点确认 {role_text} 的趋势是否继续成立。"
        return f"{base} 当前更适合保持解释型观察，而不是外推成交易指令。"

    @staticmethod
    def _normalize_window(window: dict[str, Any]) -> dict[str, Any]:
        judgement_snapshot = dict(window.get("judgement_snapshot_json") or {})
        linked_tags = list(judgement_snapshot.get("linked_tags_json") or [])
        return {
            **window,
            "linked_tags_json": linked_tags,
            "risk_level": judgement_snapshot.get("risk_level") or "低",
            "disagreement_level": judgement_snapshot.get("disagreement_level") or "低",
            "support_count": int(judgement_snapshot.get("support_count") or len(window.get("support_events_json") or [])),
            "opposing_count": int(judgement_snapshot.get("opposing_count") or len(window.get("opposing_events_json") or [])),
            "risk_count": int(judgement_snapshot.get("risk_count") or len(window.get("risk_events_json") or [])),
            "has_holding": bool(judgement_snapshot.get("has_holding")),
            "has_watchlist": bool(judgement_snapshot.get("has_watchlist")),
            "has_opportunity": bool(judgement_snapshot.get("has_opportunity")),
        }

    @staticmethod
    def _fallback_window(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "window_id": 0,
            **payload,
            "support_events_json": list(payload["support_events_json"]),
            "opposing_events_json": list(payload["opposing_events_json"]),
            "risk_events_json": list(payload["risk_events_json"]),
            "linked_tags_json": list((payload.get("judgement_snapshot_json") or {}).get("linked_tags_json") or []),
            "risk_level": (payload.get("judgement_snapshot_json") or {}).get("risk_level") or "低",
            "disagreement_level": (payload.get("judgement_snapshot_json") or {}).get("disagreement_level") or "低",
            "support_count": len(payload["support_events_json"]),
            "opposing_count": len(payload["opposing_events_json"]),
            "risk_count": len(payload["risk_events_json"]),
            "has_holding": bool((payload.get("judgement_snapshot_json") or {}).get("has_holding")),
            "has_watchlist": bool((payload.get("judgement_snapshot_json") or {}).get("has_watchlist")),
            "has_opportunity": bool((payload.get("judgement_snapshot_json") or {}).get("has_opportunity")),
        }

    @staticmethod
    def _sort_key(item: dict[str, Any]) -> tuple[int, int, int, int, str]:
        risk_priority = {"高": 0, "中": 1, "低": 2}
        disagreement_priority = {"高": 0, "中": 1, "低": 2}
        return (
            risk_priority.get(str(item.get("risk_level") or "低"), 9),
            0 if bool(item.get("has_holding")) else 1,
            disagreement_priority.get(str(item.get("disagreement_level") or "低"), 9),
            -int(item.get("window_size") or 0),
            str(item.get("ticker") or ""),
        )


_decision_context_window_service: Optional[DecisionContextWindowService] = None


def get_decision_context_window_service() -> DecisionContextWindowService:
    global _decision_context_window_service
    if _decision_context_window_service is None:
        _decision_context_window_service = DecisionContextWindowService()
    return _decision_context_window_service


def reset_decision_context_window_service() -> None:
    global _decision_context_window_service
    _decision_context_window_service = None
