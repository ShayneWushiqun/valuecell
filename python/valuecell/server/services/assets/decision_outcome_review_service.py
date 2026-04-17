from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Any, Optional

from loguru import logger

from ...db.repositories.decision_outcome_review_repository import (
    DecisionOutcomeReviewRepository,
)
from ...db.repositories.decision_record_repository import DecisionRecordRepository
from ..assets.asset_service import AssetService
from .ashare_daily_snapshot_service import AShareDailySnapshotService
from .decision_context_window_service import DecisionContextWindowService
from .decision_record_service import DecisionRecordService

REVIEW_HORIZONS = (5, 10, 20)
OBSERVATION_BUFFER_DAYS = 5
REFRESH_LOOKBACK_DAYS = 60
REFRESH_LIMIT_RECORDS = 30
MAX_REFRESH_RECORD_SCAN = 120
MAX_SCORE = 100
MIN_SCORE = 0
ACTION_HOLD = "继续持有"
ACTION_HOLD_OBSERVE = "持有观察"
ACTION_REDUCE = "减仓观察"
ACTION_PROTECT = "保护利润"
ACTION_STOP = "纪律止损"
LONG_BIAS_ACTIONS = {ACTION_HOLD, ACTION_HOLD_OBSERVE}
RISK_REDUCTION_ACTIONS = {ACTION_REDUCE, ACTION_PROTECT, ACTION_STOP}
SUPPORTED_ACTIONS = LONG_BIAS_ACTIONS | RISK_REDUCTION_ACTIONS

HOLD_VALID_GAIN_PCT = 3.0
HOLD_FAIL_LOSS_PCT = -5.0
HOLD_VALID_MAE_PCT = -5.0
HOLD_FAIL_MAE_PCT = -7.0
HOLD_OBSERVE_FAIL_LOSS_PCT = -5.0
HOLD_OBSERVE_FAIL_MAE_PCT = -6.0
REDUCE_VALID_PULLBACK_PCT = 4.0
PROTECT_VALID_PULLBACK_PCT = 4.0
STOP_VALID_PULLBACK_PCT = 5.0
STRONG_CONTINUATION_PCT = 6.0
SMALL_REVERSAL_PCT = 2.0
LOW_DRAWBACK_PCT = -3.0


@dataclass
class PriceBar:
    timestamp: datetime
    price: float | None
    open_price: float | None
    high_price: float | None
    low_price: float | None
    close_price: float | None

    @property
    def trading_date(self) -> date:
        return self.timestamp.astimezone().date()

    def reference_price(self) -> float | None:
        if self.close_price is not None:
            return self.close_price
        return self.price

    def high_reference(self) -> float | None:
        if self.high_price is not None:
            return self.high_price
        return self.reference_price()

    def low_reference(self) -> float | None:
        if self.low_price is not None:
            return self.low_price
        return self.reference_price()


class DecisionOutcomeReviewService:
    def __init__(
        self,
        decision_outcome_review_repository: Optional[DecisionOutcomeReviewRepository] = None,
        decision_record_repository: Optional[DecisionRecordRepository] = None,
        decision_record_service: Optional[DecisionRecordService] = None,
        decision_context_window_service: Optional[DecisionContextWindowService] = None,
        ashare_daily_snapshot_service: Optional[AShareDailySnapshotService] = None,
        asset_service: Optional[AssetService] = None,
    ) -> None:
        self.decision_outcome_review_repository = (
            decision_outcome_review_repository or DecisionOutcomeReviewRepository()
        )
        self.decision_record_repository = (
            decision_record_repository or DecisionRecordRepository()
        )
        self.decision_record_service = decision_record_service or DecisionRecordService()
        self.decision_context_window_service = (
            decision_context_window_service or DecisionContextWindowService()
        )
        self.ashare_daily_snapshot_service = (
            ashare_daily_snapshot_service or AShareDailySnapshotService()
        )
        self.asset_service = asset_service or AssetService()

    def list_reviews(
        self,
        *,
        user_id: str,
        record_id: int | None = None,
        outcome_status: str | None = None,
        action: str | None = None,
        review_horizon_days: int | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        reviews = self.decision_outcome_review_repository.list_reviews(
            user_id=user_id,
            record_id=record_id,
            outcome_status=outcome_status,
            action=action,
            review_horizon_days=review_horizon_days,
            limit=limit,
        )
        items = [item.to_dict() for item in reviews]
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "items": items,
            "count": len(items),
        }

    def get_review_detail(self, *, user_id: str, review_id: int) -> dict[str, Any] | None:
        item = self.decision_outcome_review_repository.get_review_by_id(
            user_id=user_id,
            review_id=review_id,
        )
        return item.to_dict() if item else None

    def capture_review(
        self,
        *,
        user_id: str,
        record_id: int,
        review_horizon_days: int,
        review_date: str | None = None,
    ) -> dict[str, Any] | None:
        record = self.decision_record_service.get_record_detail(
            user_id=user_id,
            record_id=record_id,
        )
        if record is None:
            return None
        return self._upsert_review(
            user_id=user_id,
            record=record,
            review_horizon_days=review_horizon_days,
            review_date=review_date,
        )

    def refresh_reviews(
        self,
        *,
        user_id: str,
        review_horizon_days_list: list[int] | None = None,
        lookback_days: int = REFRESH_LOOKBACK_DAYS,
        limit_records: int = REFRESH_LIMIT_RECORDS,
        review_date: str | None = None,
    ) -> dict[str, Any]:
        horizons = self._normalize_horizons(review_horizon_days_list)
        records = list(
            self.decision_record_service.list_records(
                user_id=user_id,
                limit=max(limit_records, MAX_REFRESH_RECORD_SCAN),
            ).get("items")
            or []
        )
        cutoff_date = datetime.now().astimezone().date() - timedelta(days=lookback_days)
        eligible_records = [
            record
            for record in records
            if self._is_recent_record(record, cutoff_date=cutoff_date)
            and str(record.get("action") or "") in SUPPORTED_ACTIONS
        ][:limit_records]
        items: list[dict[str, Any]] = []
        for record in eligible_records:
            for horizon in horizons:
                item = self._upsert_review(
                    user_id=user_id,
                    record=record,
                    review_horizon_days=horizon,
                    review_date=review_date,
                )
                if item is not None:
                    items.append(item)
        logger.info(
            "Refreshed decision outcome reviews count={count} record_count={record_count}",
            count=len(items),
            record_count=len(eligible_records),
        )
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "items": items,
            "count": len(items),
        }

    def _upsert_review(
        self,
        *,
        user_id: str,
        record: dict[str, Any],
        review_horizon_days: int,
        review_date: str | None,
    ) -> dict[str, Any]:
        payload = self._build_review_payload(
            user_id=user_id,
            record=record,
            review_horizon_days=review_horizon_days,
            review_date=review_date,
        )
        existing = self.decision_outcome_review_repository.get_review_by_dedupe_key(
            user_id=user_id,
            dedupe_key=str(payload["dedupe_key"]),
        )
        if existing is None:
            saved = self.decision_outcome_review_repository.create_review(payload)
        else:
            saved = self.decision_outcome_review_repository.update_review(
                int(existing.id),
                {key: value for key, value in payload.items() if key not in {"user_id", "dedupe_key"}},
            )
        self._sync_record_outcome(record_id=int(record["record_id"]), payload=payload)
        if saved:
            return saved.to_dict()
        return self._fallback_review(payload)

    def _build_review_payload(
        self,
        *,
        user_id: str,
        record: dict[str, Any],
        review_horizon_days: int,
        review_date: str | None,
    ) -> dict[str, Any]:
        normalized_horizon = self._validate_horizon(review_horizon_days)
        normalized_review_date = review_date or datetime.now().astimezone().date().isoformat()
        record_date = self._parse_iso_date(str(record.get("record_date") or ""))
        as_of_date = self._parse_iso_date(normalized_review_date)
        context_window = self._load_context_window(
            user_id=user_id,
            record=record,
        )
        market_background = self._load_market_background(
            user_id=user_id,
            record_date=record_date.isoformat(),
        )
        linked_context_window_id = int(
            context_window.get("window_id")
            or record.get("context_window_id")
            or 0
        ) or None
        linked_event_ids_json = [
            int(item)
            for item in list(record.get("linked_event_ids_json") or [])
            if int(item or 0) > 0
        ]
        action = str(record.get("action") or "")
        base_payload = {
            "user_id": user_id,
            "record_id": int(record["record_id"]),
            "ticker": str(record.get("ticker") or ""),
            "display_name": str(record.get("display_name") or record.get("ticker") or ""),
            "action": action,
            "lifecycle_stage": record.get("lifecycle_stage"),
            "record_date": record_date.isoformat(),
            "review_date": normalized_review_date,
            "review_horizon_days": normalized_horizon,
            "linked_context_window_id": linked_context_window_id,
            "linked_event_ids_json": linked_event_ids_json,
        }
        if action not in SUPPORTED_ACTIONS:
            return {
                **base_payload,
                "available": False,
                "outcome_status": "数据不足",
                "outcome_score": 0,
                "price_change_pct": None,
                "max_favorable_excursion_pct": None,
                "max_adverse_excursion_pct": None,
                "entry_reference_price": None,
                "exit_reference_price": None,
                "summary": "当前动作暂未纳入结果回看规则。",
                "what_happened": "缺少可识别动作口径，未生成结果判断。",
                "what_was_right": "暂无可复用结论。",
                "what_was_wrong": "当前规则未覆盖该动作。",
                "followup_view": "后续可补规则覆盖后再复盘，不外推成交易指令。",
                "risk_after_signal": "当前仅保留原始记录，不追加结果判断。",
                "context_consistency": self._build_context_consistency(
                    action=action,
                    outcome_status="数据不足",
                    context_window=context_window,
                ),
                "empty_message": "Unsupported decision action for outcome review.",
                "dedupe_key": self._build_dedupe_key(
                    record_id=int(record["record_id"]),
                    review_horizon_days=normalized_horizon,
                    review_date=normalized_review_date,
                ),
            }
        price_window = self._load_price_window(
            ticker=str(record.get("ticker") or ""),
            record_date=record_date,
            as_of_date=as_of_date,
        )
        if not price_window["success"]:
            message = str(price_window.get("message") or "Historical price data not available.")
            return {
                **base_payload,
                "available": False,
                "outcome_status": "数据不足",
                "outcome_score": 0,
                "price_change_pct": None,
                "max_favorable_excursion_pct": None,
                "max_adverse_excursion_pct": None,
                "entry_reference_price": None,
                "exit_reference_price": None,
                "summary": "历史价格不足，暂时无法完成结果回看。",
                "what_happened": "价格窗口无法组成有效观察区间。",
                "what_was_right": "暂无足够价格证据。",
                "what_was_wrong": "缺少完整价格路径，不能给出可靠结论。",
                "followup_view": "等待后续日线补齐后再做轻量回看。",
                "risk_after_signal": self._build_risk_after_signal(
                    action=action,
                    adverse_excursion_pct=None,
                    context_window=context_window,
                ),
                "context_consistency": self._build_context_consistency(
                    action=action,
                    outcome_status="数据不足",
                    context_window=context_window,
                ),
                "empty_message": message,
                "dedupe_key": self._build_dedupe_key(
                    record_id=int(record["record_id"]),
                    review_horizon_days=normalized_horizon,
                    review_date=normalized_review_date,
                ),
            }
        price_bars = list(price_window["bars"])
        evaluation_window, review_status, empty_message = self._resolve_evaluation_window(
            price_bars=price_bars,
            review_horizon_days=normalized_horizon,
            as_of_date=as_of_date,
        )
        if not evaluation_window:
            return {
                **base_payload,
                "available": False,
                "outcome_status": "数据不足",
                "outcome_score": 0,
                "price_change_pct": None,
                "max_favorable_excursion_pct": None,
                "max_adverse_excursion_pct": None,
                "entry_reference_price": None,
                "exit_reference_price": None,
                "summary": "历史价格不足，暂时无法完成结果回看。",
                "what_happened": "未能形成有效的起始与结束参考价格。",
                "what_was_right": "暂无足够价格证据。",
                "what_was_wrong": "价格窗口仍不完整。",
                "followup_view": "等待后续价格补齐后再复盘。",
                "risk_after_signal": self._build_risk_after_signal(
                    action=action,
                    adverse_excursion_pct=None,
                    context_window=context_window,
                ),
                "context_consistency": self._build_context_consistency(
                    action=action,
                    outcome_status="数据不足",
                    context_window=context_window,
                ),
                "empty_message": empty_message or "Historical review window is not available.",
                "dedupe_key": self._build_dedupe_key(
                    record_id=int(record["record_id"]),
                    review_horizon_days=normalized_horizon,
                    review_date=normalized_review_date,
                ),
            }
        metrics = self._calculate_metrics(
            action=action,
            evaluation_window=evaluation_window,
        )
        outcome_status, outcome_score = self._evaluate_outcome(
            action=action,
            review_status=review_status,
            price_change_pct=metrics["price_change_pct"],
            favorable_excursion_pct=metrics["max_favorable_excursion_pct"],
            adverse_excursion_pct=metrics["max_adverse_excursion_pct"],
        )
        summary = self._build_summary(
            action=action,
            outcome_status=outcome_status,
            price_change_pct=metrics["price_change_pct"],
            review_horizon_days=normalized_horizon,
            review_status=review_status,
        )
        what_happened = self._build_what_happened(
            action=action,
            metrics=metrics,
            normalized_review_date=normalized_review_date,
            market_background=market_background,
            review_status=review_status,
        )
        what_was_right = self._build_what_was_right(
            action=action,
            outcome_status=outcome_status,
            metrics=metrics,
        )
        what_was_wrong = self._build_what_was_wrong(
            action=action,
            outcome_status=outcome_status,
            metrics=metrics,
        )
        followup_view = self._build_followup_view(
            action=action,
            outcome_status=outcome_status,
            review_status=review_status,
            review_horizon_days=normalized_horizon,
        )
        risk_after_signal = self._build_risk_after_signal(
            action=action,
            adverse_excursion_pct=metrics["max_adverse_excursion_pct"],
            context_window=context_window,
        )
        context_consistency = self._build_context_consistency(
            action=action,
            outcome_status=outcome_status,
            context_window=context_window,
        )
        return {
            **base_payload,
            "available": outcome_status != "数据不足",
            "outcome_status": outcome_status,
            "outcome_score": outcome_score,
            "price_change_pct": metrics["price_change_pct"],
            "max_favorable_excursion_pct": metrics["max_favorable_excursion_pct"],
            "max_adverse_excursion_pct": metrics["max_adverse_excursion_pct"],
            "entry_reference_price": metrics["entry_reference_price"],
            "exit_reference_price": metrics["exit_reference_price"],
            "summary": summary,
            "what_happened": what_happened,
            "what_was_right": what_was_right,
            "what_was_wrong": what_was_wrong,
            "followup_view": followup_view,
            "risk_after_signal": risk_after_signal,
            "context_consistency": context_consistency,
            "empty_message": empty_message,
            "dedupe_key": self._build_dedupe_key(
                record_id=int(record["record_id"]),
                review_horizon_days=normalized_horizon,
                review_date=normalized_review_date,
            ),
        }

    def _load_price_window(
        self,
        *,
        ticker: str,
        record_date: date,
        as_of_date: date,
    ) -> dict[str, Any]:
        start_dt = datetime.combine(record_date, time.min)
        end_dt = datetime.combine(as_of_date, time.max)
        try:
            result = self.asset_service.get_historical_prices(
                ticker=ticker,
                start_date=start_dt,
                end_date=end_dt,
                interval="1d",
            )
        except Exception as exc:
            logger.warning(
                "Failed to load historical prices ticker={ticker} err={err}",
                ticker=ticker,
                err=str(exc),
            )
            return {"success": False, "message": str(exc), "bars": []}
        if not bool(result.get("success")):
            return {
                "success": False,
                "message": str(result.get("error") or "Historical price data not available."),
                "bars": [],
            }
        bars: list[PriceBar] = []
        for item in list(result.get("prices") or []):
            timestamp = self._parse_timestamp(str(item.get("timestamp") or ""))
            if timestamp is None:
                continue
            bars.append(
                PriceBar(
                    timestamp=timestamp,
                    price=self._to_float(item.get("price")),
                    open_price=self._to_float(item.get("open_price")),
                    high_price=self._to_float(item.get("high_price")),
                    low_price=self._to_float(item.get("low_price")),
                    close_price=self._to_float(item.get("close_price")),
                )
            )
        bars.sort(key=lambda item: item.timestamp)
        if not bars:
            return {
                "success": False,
                "message": "Historical price data is empty.",
                "bars": [],
            }
        return {"success": True, "bars": bars}

    def _resolve_evaluation_window(
        self,
        *,
        price_bars: list[PriceBar],
        review_horizon_days: int,
        as_of_date: date,
    ) -> tuple[list[PriceBar], str, str | None]:
        if not price_bars:
            return [], "insufficient", "Historical price data is empty."
        if len(price_bars) < 2:
            return [], "insufficient", "Historical price data has fewer than two bars."
        if len(price_bars) >= review_horizon_days + 1:
            return price_bars[: review_horizon_days + 1], "complete", None
        start_date = price_bars[0].trading_date
        calendar_age = (as_of_date - start_date).days
        if calendar_age < review_horizon_days + OBSERVATION_BUFFER_DAYS:
            return price_bars, "ongoing", "Observation window is still in progress."
        return [], "insufficient", "Historical price points are not enough for the requested horizon."

    def _calculate_metrics(
        self,
        *,
        action: str,
        evaluation_window: list[PriceBar],
    ) -> dict[str, float | None]:
        start_price = evaluation_window[0].reference_price()
        end_price = evaluation_window[-1].reference_price()
        if start_price is None or end_price is None or start_price <= 0:
            return {
                "entry_reference_price": None,
                "exit_reference_price": None,
                "price_change_pct": None,
                "max_favorable_excursion_pct": None,
                "max_adverse_excursion_pct": None,
            }
        high_values = [
            value
            for value in (item.high_reference() for item in evaluation_window)
            if value is not None
        ]
        low_values = [
            value
            for value in (item.low_reference() for item in evaluation_window)
            if value is not None
        ]
        if not high_values or not low_values:
            return {
                "entry_reference_price": start_price,
                "exit_reference_price": end_price,
                "price_change_pct": self._pct_change(end_price, start_price),
                "max_favorable_excursion_pct": None,
                "max_adverse_excursion_pct": None,
            }
        highest_price = max(high_values)
        lowest_price = min(low_values)
        if action in LONG_BIAS_ACTIONS:
            favorable = self._pct_change(highest_price, start_price)
            adverse = self._pct_change(lowest_price, start_price)
        else:
            favorable = self._pct_change(start_price, lowest_price)
            adverse = -1 * self._pct_change(highest_price, start_price)
        return {
            "entry_reference_price": start_price,
            "exit_reference_price": end_price,
            "price_change_pct": self._pct_change(end_price, start_price),
            "max_favorable_excursion_pct": favorable,
            "max_adverse_excursion_pct": adverse,
        }

    def _evaluate_outcome(
        self,
        *,
        action: str,
        review_status: str,
        price_change_pct: float | None,
        favorable_excursion_pct: float | None,
        adverse_excursion_pct: float | None,
    ) -> tuple[str, int]:
        if price_change_pct is None or favorable_excursion_pct is None or adverse_excursion_pct is None:
            return "数据不足", 0
        if review_status == "ongoing":
            return "仍在观察", 45
        if action == ACTION_HOLD:
            if price_change_pct >= HOLD_VALID_GAIN_PCT and adverse_excursion_pct > HOLD_VALID_MAE_PCT:
                return "有效", self._clamp_score(80 + min(int(price_change_pct), 12))
            if price_change_pct <= HOLD_FAIL_LOSS_PCT or adverse_excursion_pct <= HOLD_FAIL_MAE_PCT:
                return "失效", self._clamp_score(28 + int(max(price_change_pct, -12)))
            return "部分有效", 60
        if action == ACTION_HOLD_OBSERVE:
            if price_change_pct <= HOLD_OBSERVE_FAIL_LOSS_PCT or adverse_excursion_pct <= HOLD_OBSERVE_FAIL_MAE_PCT:
                return "失效", 32
            if abs(price_change_pct) <= HOLD_VALID_GAIN_PCT and adverse_excursion_pct > HOLD_FAIL_MAE_PCT:
                return "有效", 72
            if price_change_pct >= STRONG_CONTINUATION_PCT and adverse_excursion_pct > HOLD_VALID_MAE_PCT:
                return "部分有效", 58
            return "部分有效", 62
        if action == ACTION_REDUCE:
            if favorable_excursion_pct >= REDUCE_VALID_PULLBACK_PCT or price_change_pct <= -4.0:
                return "有效", 78
            if price_change_pct >= STRONG_CONTINUATION_PCT and adverse_excursion_pct >= LOW_DRAWBACK_PCT:
                return "失效", 26
            return "部分有效", 56
        if action == ACTION_PROTECT:
            if favorable_excursion_pct >= PROTECT_VALID_PULLBACK_PCT or price_change_pct <= -3.0:
                return "有效", 76
            if price_change_pct >= STRONG_CONTINUATION_PCT and favorable_excursion_pct < SMALL_REVERSAL_PCT:
                return "失效", 34
            return "部分有效", 57
        if action == ACTION_STOP:
            if favorable_excursion_pct >= STOP_VALID_PULLBACK_PCT or price_change_pct <= HOLD_FAIL_LOSS_PCT:
                return "有效", 84
            if price_change_pct >= 5.0 and favorable_excursion_pct < SMALL_REVERSAL_PCT:
                return "失效", 20
            return "部分有效", 52
        return "数据不足", 0

    def _build_summary(
        self,
        *,
        action: str,
        outcome_status: str,
        price_change_pct: float | None,
        review_horizon_days: int,
        review_status: str,
    ) -> str:
        if outcome_status == "数据不足":
            return "历史价格不足，暂时无法完成结果回看。"
        if review_status == "ongoing":
            return (
                f"{action} 的 {review_horizon_days} 日回看窗口尚未走完，"
                "当前只保留轻量观察结论。"
            )
        return (
            f"{action} 在 {review_horizon_days} 日回看中判定为{outcome_status}，"
            f"窗口价格变化 {self._format_pct(price_change_pct)}。"
        )

    def _build_what_happened(
        self,
        *,
        action: str,
        metrics: dict[str, float | None],
        normalized_review_date: str,
        market_background: dict[str, Any],
        review_status: str,
    ) -> str:
        market_state = str(market_background.get("market_state") or "市场背景待补充")
        market_note = str(market_background.get("market_note") or "")
        base = (
            f"截至 {normalized_review_date}，{action} 对应窗口价格变化 "
            f"{self._format_pct(metrics['price_change_pct'])}，"
            f"最大有利波动 {self._format_pct(metrics['max_favorable_excursion_pct'])}，"
            f"最大不利波动 {self._format_pct(metrics['max_adverse_excursion_pct'])}。"
        )
        if review_status == "ongoing":
            return f"{base} 当前观察窗未走完，仅做阶段性记录。市场背景：{market_state}。"
        if market_note:
            return f"{base} 当日市场背景为 {market_state}，{market_note}"
        return f"{base} 当日市场背景为 {market_state}。"

    def _build_what_was_right(
        self,
        *,
        action: str,
        outcome_status: str,
        metrics: dict[str, float | None],
    ) -> str:
        favorable = self._format_pct(metrics["max_favorable_excursion_pct"])
        adverse = self._format_pct(metrics["max_adverse_excursion_pct"])
        if outcome_status == "有效":
            if action in LONG_BIAS_ACTIONS:
                return f"信号后仍有延续或承接，最大不利波动控制在 {adverse} 附近。"
            return f"信号后出现了对保守处理有利的回撤，最大有利波动为 {favorable}。"
        if outcome_status == "部分有效":
            return "原判断并未被完全否定，但验证力度一般，更多体现为节奏管理而非方向碾压。"
        if outcome_status == "仍在观察":
            return "当前窗口仍在推进，先保留原判断中的风险控制价值。"
        return "当前回看里暂未看到足够被验证的部分。"

    def _build_what_was_wrong(
        self,
        *,
        action: str,
        outcome_status: str,
        metrics: dict[str, float | None],
    ) -> str:
        price_change = self._format_pct(metrics["price_change_pct"])
        if outcome_status == "失效":
            if action in LONG_BIAS_ACTIONS:
                return f"信号后走势未能延续，窗口价格变化 {price_change}，原先持有假设被削弱。"
            return f"信号后并未出现足够的回撤验证，反而走出 {price_change} 的反向变化。"
        if outcome_status == "部分有效":
            return "当前结果并不够干净，说明原判断更多是保守应对，而不是高确定性结论。"
        if outcome_status == "仍在观察":
            return "窗口尚未收敛，现在下结论仍偏早。"
        if outcome_status == "数据不足":
            return "缺少完整价格路径，无法判断哪里错。"
        return "当前回看中未见明显失配点。"

    def _build_followup_view(
        self,
        *,
        action: str,
        outcome_status: str,
        review_status: str,
        review_horizon_days: int,
    ) -> str:
        if review_status == "ongoing":
            return (
                f"先继续观察，待满 {review_horizon_days} 个交易日后再做完整复盘，"
                "不把阶段性结果外推成交易指令。"
            )
        if outcome_status == "失效":
            return (
                f"{action} 这次回看偏弱，后续更适合结合新的时间窗和最新风险证据重新判断。"
            )
        if outcome_status == "有效":
            return "这次回看支持原判断方向，但仍需继续结合新的日级信号复核。"
        return "这次回看只提供轻量验证，后续应继续结合新的市场与题材语境复盘。"

    def _build_risk_after_signal(
        self,
        *,
        action: str,
        adverse_excursion_pct: float | None,
        context_window: dict[str, Any] | None,
    ) -> str:
        risk_count = len((context_window or {}).get("risk_events_json") or [])
        if adverse_excursion_pct is None:
            return "历史价格不足，当前只保留记录级风险提示。"
        if action in LONG_BIAS_ACTIONS:
            return (
                f"信号后最大回撤为 {self._format_pct(adverse_excursion_pct)}，"
                f"时间窗内风险证据 {risk_count} 条。"
            )
        return (
            f"若未及时收缩风险，窗口内最不利反向波动约为 "
            f"{self._format_pct(adverse_excursion_pct)}，风险证据 {risk_count} 条。"
        )

    def _build_context_consistency(
        self,
        *,
        action: str,
        outcome_status: str,
        context_window: dict[str, Any] | None,
    ) -> str:
        if not context_window:
            return "缺少决策时间窗上下文，本次仅基于决策记录与日线价格做轻量回看。"
        support_count = len(context_window.get("support_events_json") or [])
        opposing_count = len(context_window.get("opposing_events_json") or [])
        risk_count = len(context_window.get("risk_events_json") or [])
        if outcome_status in {"有效", "部分有效"} and action in LONG_BIAS_ACTIONS:
            if support_count >= max(opposing_count, risk_count):
                return "当时支持证据相对更多，后续走势与继续持有方向基本一致。"
            return "当时时间窗并非单边支持，结果只做有限验证。"
        if outcome_status in {"有效", "部分有效"} and action in RISK_REDUCTION_ACTIONS:
            if risk_count >= support_count:
                return "当时风险证据不弱，后续结果与保守处理方向基本一致。"
            return "当时上下文分歧仍在，保守动作只得到部分验证。"
        if outcome_status == "失效" and action in LONG_BIAS_ACTIONS:
            return "当时风险或反对证据并未完全消失，后续转弱说明原判断承受了过高波动。"
        if outcome_status == "失效" and action in RISK_REDUCTION_ACTIONS:
            return "当时支持证据并不算弱，后续修复说明保守动作偏早。"
        return "当前上下文与结果之间仍需更多样本做轻量校准。"

    def _load_context_window(
        self,
        *,
        user_id: str,
        record: dict[str, Any],
    ) -> dict[str, Any] | None:
        context_window_id = int(record.get("context_window_id") or 0)
        if context_window_id > 0:
            try:
                return self.decision_context_window_service.get_window_detail(
                    user_id=user_id,
                    window_id=context_window_id,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to load context window detail window_id={window_id} err={err}",
                    window_id=context_window_id,
                    err=str(exc),
                )
        ticker = str(record.get("ticker") or "")
        if not ticker:
            return None
        try:
            items = self.decision_context_window_service.list_windows(
                user_id=user_id,
                ticker=ticker,
                limit=1,
            ).get("items") or []
        except Exception as exc:
            logger.warning(
                "Failed to list context windows ticker={ticker} err={err}",
                ticker=ticker,
                err=str(exc),
            )
            return None
        return next(iter(items), None)

    def _load_market_background(
        self,
        *,
        user_id: str,
        record_date: str,
    ) -> dict[str, Any]:
        try:
            snapshot = self.ashare_daily_snapshot_service.get_snapshot_detail(
                user_id=user_id,
                snapshot_date=record_date,
            )
        except Exception as exc:
            logger.warning(
                "Failed to load daily snapshot record_date={record_date} err={err}",
                record_date=record_date,
                err=str(exc),
            )
            snapshot = None
        market_digest = dict((snapshot or {}).get("market_digest") or {})
        attention_digest = dict((snapshot or {}).get("attention_digest") or {})
        if not market_digest:
            return {
                "market_state": None,
                "market_note": "",
            }
        note = (
            f"风险回避 {int(attention_digest.get('risk_alert_count') or 0)} 条，"
            f"需要处理的持仓 {int(attention_digest.get('holding_risk_count') or 0)} 个。"
        )
        return {
            "market_state": market_digest.get("market_state"),
            "market_note": note,
        }

    def _sync_record_outcome(self, *, record_id: int, payload: dict[str, Any]) -> None:
        try:
            self.decision_record_repository.update_record(
                record_id,
                {
                    "outcome_status": payload.get("outcome_status"),
                    "review_note": payload.get("summary"),
                },
            )
        except Exception as exc:
            logger.warning(
                "Failed to sync decision record outcome record_id={record_id} err={err}",
                record_id=record_id,
                err=str(exc),
            )

    @staticmethod
    def _fallback_review(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "review_id": 0,
            **{key: value for key, value in payload.items() if key != "dedupe_key"},
        }

    @staticmethod
    def _build_dedupe_key(
        *,
        record_id: int,
        review_horizon_days: int,
        review_date: str,
    ) -> str:
        return f"{record_id}|{review_horizon_days}|{review_date}"

    @staticmethod
    def _validate_horizon(review_horizon_days: int) -> int:
        if review_horizon_days not in REVIEW_HORIZONS:
            raise ValueError("Unsupported review horizon")
        return review_horizon_days

    @staticmethod
    def _normalize_horizons(review_horizon_days_list: list[int] | None) -> list[int]:
        if not review_horizon_days_list:
            return list(REVIEW_HORIZONS)
        normalized: list[int] = []
        for item in review_horizon_days_list:
            if item in REVIEW_HORIZONS and item not in normalized:
                normalized.append(item)
        return normalized or list(REVIEW_HORIZONS)

    @staticmethod
    def _is_recent_record(record: dict[str, Any], *, cutoff_date: date) -> bool:
        record_date = str(record.get("record_date") or "")
        if not record_date:
            return False
        try:
            parsed = date.fromisoformat(record_date)
        except ValueError:
            return False
        return parsed >= cutoff_date

    @staticmethod
    def _parse_iso_date(value: str) -> date:
        return date.fromisoformat(value)

    @staticmethod
    def _parse_timestamp(value: str) -> datetime | None:
        if not value:
            return None
        try:
            normalized = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed

    @staticmethod
    def _to_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _pct_change(end_value: float, start_value: float) -> float:
        return round(((end_value - start_value) / start_value) * 100, 2)

    @staticmethod
    def _format_pct(value: float | None) -> str:
        if value is None:
            return "N/A"
        return f"{value:+.2f}%"

    @staticmethod
    def _clamp_score(value: int) -> int:
        return max(MIN_SCORE, min(MAX_SCORE, value))


_decision_outcome_review_service: Optional[DecisionOutcomeReviewService] = None


def get_decision_outcome_review_service() -> DecisionOutcomeReviewService:
    global _decision_outcome_review_service
    if _decision_outcome_review_service is None:
        _decision_outcome_review_service = DecisionOutcomeReviewService()
    return _decision_outcome_review_service


def reset_decision_outcome_review_service() -> None:
    global _decision_outcome_review_service
    _decision_outcome_review_service = None
