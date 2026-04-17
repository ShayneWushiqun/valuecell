from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional

from loguru import logger

from ...db.repositories.short_cycle_context_event_repository import (
    ShortCycleContextEventRepository,
)
from .decision_alert_persistence_service import DecisionAlertPersistenceService
from .decision_record_service import DecisionRecordService
from .exit_risk_center_service import ExitRiskCenterService
from .holding_lifecycle_service import HoldingLifecycleService
from .homepage_context_service import HomepageContextService
from .opportunity_pool_service import OpportunityPoolService
from .theme_radar_service import ThemeRadarService
from .watchlist_center_service import WatchlistCenterService


class ShortCycleContextEventService:
    def __init__(
        self,
        short_cycle_context_event_repository: Optional[ShortCycleContextEventRepository] = None,
        holding_lifecycle_service: Optional[HoldingLifecycleService] = None,
        exit_risk_center_service: Optional[ExitRiskCenterService] = None,
        decision_record_service: Optional[DecisionRecordService] = None,
        opportunity_pool_service: Optional[OpportunityPoolService] = None,
        theme_radar_service: Optional[ThemeRadarService] = None,
        watchlist_center_service: Optional[WatchlistCenterService] = None,
        decision_alert_persistence_service: Optional[DecisionAlertPersistenceService] = None,
        homepage_context_service: Optional[HomepageContextService] = None,
    ) -> None:
        self.short_cycle_context_event_repository = (
            short_cycle_context_event_repository or ShortCycleContextEventRepository()
        )
        self.holding_lifecycle_service = holding_lifecycle_service or HoldingLifecycleService()
        self.exit_risk_center_service = exit_risk_center_service or ExitRiskCenterService()
        self.decision_record_service = decision_record_service or DecisionRecordService()
        self.opportunity_pool_service = opportunity_pool_service or OpportunityPoolService()
        self.theme_radar_service = theme_radar_service or ThemeRadarService()
        self.watchlist_center_service = watchlist_center_service or WatchlistCenterService()
        self.decision_alert_persistence_service = (
            decision_alert_persistence_service or DecisionAlertPersistenceService()
        )
        self.homepage_context_service = homepage_context_service or HomepageContextService()

    def list_events(
        self,
        *,
        user_id: str,
        ticker: str | None = None,
        limit: int = 200,
    ) -> dict[str, Any]:
        events = self.short_cycle_context_event_repository.list_events(
            user_id=user_id,
            ticker=ticker,
            limit=limit,
        )
        items = [event.to_dict() for event in events]
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "items": items,
            "count": len(items),
        }

    def get_event_detail(self, *, user_id: str, event_id: int) -> dict[str, Any] | None:
        event = self.short_cycle_context_event_repository.get_event_by_id(
            user_id=user_id,
            event_id=event_id,
        )
        return event.to_dict() if event else None

    def refresh_events(
        self,
        *,
        user_id: str,
        ticker: str | None = None,
    ) -> dict[str, Any]:
        focus_tickers = [ticker] if ticker else self._build_focus_universe(user_id)
        if not focus_tickers:
            return {
                "generated_at": datetime.now(UTC).isoformat(),
                "items": [],
                "count": 0,
            }
        opportunity_items = list(
            self.opportunity_pool_service.get_opportunity_candidates(user_id).get("items") or []
        )
        opportunity_by_ticker = {
            str(item.get("ticker") or ""): item
            for item in opportunity_items
            if str(item.get("ticker") or "")
        }
        lifecycle_items = list(self.holding_lifecycle_service.get_overview(user_id).get("items") or [])
        lifecycle_by_ticker = {
            str(item.get("ticker") or ""): item for item in lifecycle_items if str(item.get("ticker") or "")
        }
        exit_risk_overview = self.exit_risk_center_service.get_overview(user_id)
        exit_risk_items = self._merge_exit_risk_groups(exit_risk_overview)
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
        watchlist_items = list(self.watchlist_center_service.get_overview(user_id).get("items") or [])
        watchlist_by_ticker = {
            str(item.get("ticker") or ""): item for item in watchlist_items if str(item.get("ticker") or "")
        }
        theme_items = list(self.theme_radar_service.get_overview(user_id).get("items") or [])
        theme_by_name = {
            str(item.get("theme_name") or ""): item for item in theme_items if str(item.get("theme_name") or "")
        }
        alert_items = list(
            self.decision_alert_persistence_service.list_alerts(
                user_id=user_id,
                status="active",
                limit=200,
            ).get("items")
            or []
        )
        alerts_by_ticker: dict[str, list[dict[str, Any]]] = {}
        for item in alert_items:
            ticker_key = str(item.get("ticker") or "")
            if not ticker_key:
                continue
            alerts_by_ticker.setdefault(ticker_key, []).append(item)
        homepage_context = self.homepage_context_service.get_homepage_context(user_id)
        market_digest = self._extract_market_digest(homepage_context)
        record_date = datetime.now().astimezone().date().isoformat()
        saved_items: list[dict[str, Any]] = []

        for focus_ticker in focus_tickers:
            lifecycle_item = lifecycle_by_ticker.get(focus_ticker)
            opportunity_item = opportunity_by_ticker.get(focus_ticker)
            watchlist_item = watchlist_by_ticker.get(focus_ticker)
            exit_risk_item = exit_risk_by_ticker.get(focus_ticker)
            decision_record_item = decision_record_by_ticker.get(focus_ticker)
            theme_name = self._resolve_theme_name(lifecycle_item, opportunity_item, watchlist_item)
            theme_item = theme_by_name.get(theme_name or "")
            candidate_events = self._build_events_for_ticker(
                ticker=focus_ticker,
                user_id=user_id,
                record_date=record_date,
                market_digest=market_digest,
                lifecycle_item=lifecycle_item,
                exit_risk_item=exit_risk_item,
                decision_record_item=decision_record_item,
                opportunity_item=opportunity_item,
                watchlist_item=watchlist_item,
                theme_item=theme_item,
                alerts=alerts_by_ticker.get(focus_ticker, []),
            )
            for payload in candidate_events:
                saved = self._upsert_event(user_id=user_id, payload=payload)
                saved_items.append(saved)

        logger.info(
            "Refreshed short cycle context events count={count} tickers={ticker_count}",
            count=len(saved_items),
            ticker_count=len(focus_tickers),
        )
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "items": saved_items,
            "count": len(saved_items),
        }

    def _upsert_event(self, *, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        existing = self.short_cycle_context_event_repository.get_event_by_dedupe_key(
            user_id=user_id,
            dedupe_key=str(payload["dedupe_key"]),
        )
        if existing is None:
            saved = self.short_cycle_context_event_repository.create_event(payload)
        else:
            saved = self.short_cycle_context_event_repository.update_event(
                int(existing.id),
                {key: value for key, value in payload.items() if key not in {"user_id", "dedupe_key"}},
            )
        return saved.to_dict() if saved else self._fallback_event(payload)

    def _build_focus_universe(self, user_id: str) -> list[str]:
        tickers: list[str] = []
        lifecycle_items = list(self.holding_lifecycle_service.get_overview(user_id).get("items") or [])
        watchlist_items = list(self.watchlist_center_service.get_overview(user_id).get("items") or [])
        opportunity_items = list(
            self.opportunity_pool_service.get_opportunity_candidates(user_id).get("items") or []
        )
        alert_items = list(
            self.decision_alert_persistence_service.list_alerts(
                user_id=user_id,
                status="active",
                limit=200,
            ).get("items")
            or []
        )
        for item in lifecycle_items + watchlist_items + opportunity_items + alert_items:
            ticker_value = str(item.get("ticker") or "").strip()
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
    def _extract_market_digest(homepage_context: dict[str, Any]) -> dict[str, Any]:
        market_overview = dict(homepage_context.get("market_overview") or {})
        emotion_cycle = dict(homepage_context.get("emotion_cycle") or {})
        return {
            "market_state": market_overview.get("market_state"),
            "summary": market_overview.get("summary"),
            "emotion_stage": emotion_cycle.get("cycle_stage"),
            "temperature_score": emotion_cycle.get("temperature_score"),
        }

    @staticmethod
    def _resolve_theme_name(
        lifecycle_item: dict[str, Any] | None,
        opportunity_item: dict[str, Any] | None,
        watchlist_item: dict[str, Any] | None,
    ) -> str | None:
        return (
            (lifecycle_item or {}).get("theme_name")
            or (opportunity_item or {}).get("topic_name")
            or (watchlist_item or {}).get("theme_name")
        )

    def _build_events_for_ticker(
        self,
        *,
        ticker: str,
        user_id: str,
        record_date: str,
        market_digest: dict[str, Any],
        lifecycle_item: dict[str, Any] | None,
        exit_risk_item: dict[str, Any] | None,
        decision_record_item: dict[str, Any] | None,
        opportunity_item: dict[str, Any] | None,
        watchlist_item: dict[str, Any] | None,
        theme_item: dict[str, Any] | None,
        alerts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        display_name = self._resolve_display_name(
            ticker=ticker,
            lifecycle_item=lifecycle_item,
            exit_risk_item=exit_risk_item,
            opportunity_item=opportunity_item,
            watchlist_item=watchlist_item,
            alerts=alerts,
        )
        topic_name = self._resolve_theme_name(lifecycle_item, opportunity_item, watchlist_item)
        occurred_at = datetime.now(UTC)
        events: list[dict[str, Any]] = []
        events.append(
            self._make_event_payload(
                user_id=user_id,
                ticker=ticker,
                display_name=display_name,
                topic_name=topic_name,
                layer="market",
                event_type="market_state_snapshot",
                source="homepage_context",
                occurred_at=occurred_at,
                importance_score=55,
                direction=self._market_direction(str(market_digest.get("market_state") or "")),
                tradeability_hint=None,
                summary=str(market_digest.get("summary") or "市场状态仍需观察。"),
                record_date=record_date,
                payload_json=market_digest,
            )
        )
        if theme_item:
            theme_state = str(theme_item.get("theme_state") or "")
            events.append(
                self._make_event_payload(
                    user_id=user_id,
                    ticker=ticker,
                    display_name=display_name,
                    topic_name=topic_name,
                    layer="theme",
                    event_type=f"theme_{theme_state or 'neutral'}",
                    source="theme_radar",
                    occurred_at=occurred_at,
                    importance_score=min(95, int(theme_item.get("score") or 60)),
                    direction=self._theme_direction(theme_state),
                    tradeability_hint=theme_item.get("participation_hint"),
                    summary=str(
                        theme_item.get("observation_summary")
                        or theme_item.get("participation_hint")
                        or "题材状态值得继续观察。"
                    ),
                    record_date=record_date,
                    payload_json={
                        "theme_state": theme_state,
                        "watchlist_resonance_count": theme_item.get("watchlist_resonance_count"),
                        "opportunity_resonance_count": theme_item.get("opportunity_resonance_count"),
                    },
                )
            )
        if opportunity_item:
            candidate_state = str(opportunity_item.get("candidate_state") or "普通观察")
            events.append(
                self._make_event_payload(
                    user_id=user_id,
                    ticker=ticker,
                    display_name=display_name,
                    topic_name=topic_name,
                    layer="stock_position",
                    event_type="opportunity_candidate_state",
                    source="opportunity_pool",
                    occurred_at=occurred_at,
                    importance_score=int(opportunity_item.get("priority_score") or 55),
                    direction=self._candidate_direction(candidate_state),
                    tradeability_hint=opportunity_item.get("tradeability_state"),
                    summary=str(
                        opportunity_item.get("action_hint")
                        or opportunity_item.get("candidate_state")
                        or "机会池状态仍需继续确认。"
                    ),
                    record_date=record_date,
                    payload_json={
                        "candidate_state": candidate_state,
                        "tradeability_state": opportunity_item.get("tradeability_state"),
                        "expectation_gap_level": opportunity_item.get("expectation_gap_level"),
                    },
                )
            )
        if watchlist_item:
            events.append(
                self._make_event_payload(
                    user_id=user_id,
                    ticker=ticker,
                    display_name=display_name,
                    topic_name=topic_name,
                    layer="capital",
                    event_type="watchlist_resonance",
                    source="watchlist_center",
                    occurred_at=occurred_at,
                    importance_score=self._watchlist_importance(watchlist_item),
                    direction="confirm" if bool(watchlist_item.get("has_theme_resonance")) else "neutral",
                    tradeability_hint=watchlist_item.get("tradeability_state"),
                    summary=str(watchlist_item.get("quick_note") or watchlist_item.get("reason") or "观察池仍需跟踪。"),
                    record_date=record_date,
                    payload_json={
                        "observation_priority": watchlist_item.get("observation_priority"),
                        "linked_candidate_state": watchlist_item.get("linked_candidate_state"),
                        "linked_judge_action": watchlist_item.get("linked_judge_action"),
                        "has_opportunity_link": watchlist_item.get("has_opportunity_link"),
                    },
                )
            )
        if lifecycle_item:
            events.append(
                self._make_event_payload(
                    user_id=user_id,
                    ticker=ticker,
                    display_name=display_name,
                    topic_name=topic_name,
                    layer="stock_position",
                    event_type="holding_lifecycle_stage",
                    source="holding_lifecycle",
                    occurred_at=occurred_at,
                    importance_score=self._lifecycle_importance(lifecycle_item),
                    direction=self._lifecycle_direction(str(lifecycle_item.get("lifecycle_stage") or "")),
                    tradeability_hint=lifecycle_item.get("tradeability_state"),
                    summary=str(lifecycle_item.get("summary") or lifecycle_item.get("position_hint") or "持仓周期仍需观察。"),
                    record_date=record_date,
                    payload_json={
                        "lifecycle_stage": lifecycle_item.get("lifecycle_stage"),
                        "action": lifecycle_item.get("action"),
                        "role_label": lifecycle_item.get("role_label"),
                        "trend_quality": lifecycle_item.get("trend_quality"),
                        "invalid_conditions": lifecycle_item.get("invalid_conditions"),
                    },
                )
            )
        if exit_risk_item:
            events.append(
                self._make_event_payload(
                    user_id=user_id,
                    ticker=ticker,
                    display_name=display_name,
                    topic_name=topic_name,
                    layer="risk_filter",
                    event_type="exit_risk_signal",
                    source="exit_risk_center",
                    occurred_at=occurred_at,
                    importance_score=max(60, int(exit_risk_item.get("confidence") or 50)),
                    direction="risk" if str(exit_risk_item.get("action") or "") != "继续持有" else "neutral",
                    tradeability_hint=exit_risk_item.get("expected_exit_plan"),
                    summary=str(exit_risk_item.get("summary") or exit_risk_item.get("thesis") or "持仓风险仍需观察。"),
                    record_date=record_date,
                    payload_json={
                        "action": exit_risk_item.get("action"),
                        "risk_type": exit_risk_item.get("risk_type"),
                        "liquidity_warning": exit_risk_item.get("liquidity_warning"),
                        "risk_controls": exit_risk_item.get("risk_controls"),
                    },
                )
            )
        for alert in alerts[:2]:
            events.append(
                self._make_event_payload(
                    user_id=user_id,
                    ticker=ticker,
                    display_name=display_name,
                    topic_name=topic_name,
                    layer="risk_filter",
                    event_type=f"alert_{str(alert.get('alert_type') or 'general')}",
                    source="decision_alerts",
                    occurred_at=occurred_at,
                    importance_score=min(90, int(alert.get("confidence") or 55)),
                    direction=self._alert_direction(str(alert.get("action") or ""), str(alert.get("priority") or "")),
                    tradeability_hint=alert.get("next_action"),
                    summary=str(alert.get("title") or alert.get("body") or "提醒中心仍需继续观察。"),
                    record_date=record_date,
                    payload_json={
                        "alert_type": alert.get("alert_type"),
                        "priority": alert.get("priority"),
                        "action": alert.get("action"),
                    },
                )
            )
        if decision_record_item:
            events.append(
                self._make_event_payload(
                    user_id=user_id,
                    ticker=ticker,
                    display_name=display_name,
                    topic_name=topic_name,
                    layer="stock_position",
                    event_type="decision_record_snapshot",
                    source="decision_records",
                    occurred_at=occurred_at,
                    importance_score=max(50, int(decision_record_item.get("confidence") or 50)),
                    direction=self._decision_record_direction(str(decision_record_item.get("action") or "")),
                    tradeability_hint=decision_record_item.get("tradeability_state"),
                    summary=str(decision_record_item.get("summary") or "已有决策记录可回看。"),
                    record_date=record_date,
                    payload_json={
                        "record_id": decision_record_item.get("record_id"),
                        "action": decision_record_item.get("action"),
                        "lifecycle_stage": decision_record_item.get("lifecycle_stage"),
                    },
                )
            )
        return events

    @staticmethod
    def _resolve_display_name(
        *,
        ticker: str,
        lifecycle_item: dict[str, Any] | None,
        exit_risk_item: dict[str, Any] | None,
        opportunity_item: dict[str, Any] | None,
        watchlist_item: dict[str, Any] | None,
        alerts: list[dict[str, Any]],
    ) -> str:
        return str(
            (lifecycle_item or {}).get("display_name")
            or (exit_risk_item or {}).get("display_name")
            or (opportunity_item or {}).get("display_name")
            or (watchlist_item or {}).get("display_name")
            or (alerts[0].get("display_name") if alerts else None)
            or ticker
        )

    @staticmethod
    def _make_event_payload(
        *,
        user_id: str,
        ticker: str,
        display_name: str,
        topic_name: str | None,
        layer: str,
        event_type: str,
        source: str,
        occurred_at: datetime,
        importance_score: int,
        direction: str,
        tradeability_hint: str | None,
        summary: str,
        record_date: str,
        payload_json: dict[str, Any],
    ) -> dict[str, Any]:
        dedupe_key = "|".join([user_id, ticker, record_date, layer, event_type, source])
        return {
            "user_id": user_id,
            "ticker": ticker,
            "display_name": display_name,
            "topic_name": topic_name,
            "layer": layer,
            "event_type": event_type,
            "source": source,
            "occurred_at": occurred_at,
            "ingested_at": datetime.now(UTC),
            "importance_score": importance_score,
            "direction": direction,
            "time_horizon": "10-40个交易日",
            "tradeability_hint": tradeability_hint,
            "summary": summary,
            "payload_json": payload_json,
            "record_date": record_date,
            "is_active": True,
            "dedupe_key": dedupe_key,
        }

    @staticmethod
    def _fallback_event(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "event_id": 0,
            "user_id": payload["user_id"],
            "ticker": payload["ticker"],
            "display_name": payload["display_name"],
            "topic_name": payload["topic_name"],
            "layer": payload["layer"],
            "event_type": payload["event_type"],
            "source": payload["source"],
            "occurred_at": payload["occurred_at"].isoformat(),
            "ingested_at": payload["ingested_at"].isoformat(),
            "importance_score": payload["importance_score"],
            "direction": payload["direction"],
            "time_horizon": payload["time_horizon"],
            "tradeability_hint": payload["tradeability_hint"],
            "summary": payload["summary"],
            "payload_json": payload["payload_json"],
            "record_date": payload["record_date"],
            "is_active": payload["is_active"],
        }

    @staticmethod
    def _market_direction(market_state: str) -> str:
        if any(word in market_state for word in ("偏强", "修复", "回暖")):
            return "bullish"
        if any(word in market_state for word in ("偏弱", "退潮", "走弱")):
            return "bearish"
        return "neutral"

    @staticmethod
    def _theme_direction(theme_state: str) -> str:
        if theme_state == "加强":
            return "bullish"
        if theme_state == "退潮":
            return "risk"
        if theme_state == "分歧":
            return "neutral"
        return "confirm"

    @staticmethod
    def _candidate_direction(candidate_state: str) -> str:
        if "高优先级" in candidate_state:
            return "confirm"
        if "回避" in candidate_state or "不适合" in candidate_state:
            return "risk"
        return "neutral"

    @staticmethod
    def _watchlist_importance(item: dict[str, Any]) -> int:
        priority = str(item.get("observation_priority") or "低")
        if priority == "高":
            return 72
        if priority == "中":
            return 62
        return 50

    @staticmethod
    def _lifecycle_importance(item: dict[str, Any]) -> int:
        stage = str(item.get("lifecycle_stage") or "建仓观察期")
        if stage == "破逻辑退出期":
            return 90
        if stage == "退潮减仓期":
            return 80
        if stage == "分歧确认期":
            return 70
        if stage == "主升持有期":
            return 65
        return 55

    @staticmethod
    def _lifecycle_direction(stage: str) -> str:
        if stage in {"破逻辑退出期", "退潮减仓期"}:
            return "risk"
        if stage == "主升持有期":
            return "bullish"
        if stage == "分歧确认期":
            return "neutral"
        return "confirm"

    @staticmethod
    def _alert_direction(action: str, priority: str) -> str:
        if action in {"暂不参与", "风险回避", "纪律止损"} or priority == "high":
            return "risk"
        if action in {"接近可参与窗口", "继续观察"}:
            return "confirm"
        return "neutral"

    @staticmethod
    def _decision_record_direction(action: str) -> str:
        if action in {"纪律止损", "保护利润", "减仓观察"}:
            return "risk"
        if action == "继续持有":
            return "bullish"
        return "neutral"


_short_cycle_context_event_service: Optional[ShortCycleContextEventService] = None


def get_short_cycle_context_event_service() -> ShortCycleContextEventService:
    global _short_cycle_context_event_service
    if _short_cycle_context_event_service is None:
        _short_cycle_context_event_service = ShortCycleContextEventService()
    return _short_cycle_context_event_service


def reset_short_cycle_context_event_service() -> None:
    global _short_cycle_context_event_service
    _short_cycle_context_event_service = None
