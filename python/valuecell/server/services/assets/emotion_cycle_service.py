from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Optional

from .market_pulse_service import MarketPulseService
from .short_cycle_data_service import ShortCycleDataService


class EmotionCycleService:
    def __init__(
        self,
        market_pulse_service: Optional[MarketPulseService] = None,
        short_cycle_data_service: Optional[ShortCycleDataService] = None,
    ) -> None:
        self.short_cycle_data_service = short_cycle_data_service or ShortCycleDataService()
        self.market_pulse_service = market_pulse_service or MarketPulseService(
            short_cycle_data_service=self.short_cycle_data_service,
        )

    def get_emotion_cycle_snapshot(
        self,
        trade_date: str | date | datetime | None = None,
    ) -> dict[str, Any]:
        pulse = self.market_pulse_service.get_market_pulse_snapshot(trade_date)
        if not pulse.get("success"):
            return pulse
        snapshot = pulse["data"]
        stage_score = self._calculate_stage_score(snapshot)
        cycle_stage = self._resolve_cycle_stage(snapshot, stage_score)
        result = {
            "trading_date": snapshot["trading_date"],
            "cycle_stage": cycle_stage,
            "stage_score": stage_score,
            "summary": self._build_summary(cycle_stage, snapshot),
            "action_hint": self._resolve_action_hint(cycle_stage),
            "signals_json": snapshot["signals_json"],
        }
        return {"success": True, "data": result}

    def get_emotion_cycle_timeline(
        self,
        end_date: str | date | datetime | None = None,
        window_days: int = 5,
    ) -> dict[str, Any]:
        normalized_end = self._normalize_to_datetime(end_date) or datetime.now()
        start_date = normalized_end - timedelta(days=max(window_days * 3, 10))
        pulse_window = self.short_cycle_data_service.get_market_pulse_window_data(
            start_date=start_date,
            end_date=normalized_end,
            max_points=window_days,
        )
        if not pulse_window.get("success"):
            return pulse_window

        stage_points: list[dict[str, Any]] = []
        for item in pulse_window.get("items", []):
            if not item.get("success"):
                continue
            pulse_snapshot = self.market_pulse_service.get_market_pulse_snapshot(
                trade_date=item.get("trade_date")
            )
            if not pulse_snapshot.get("success"):
                continue
            snapshot = pulse_snapshot["data"]
            stage_score = self._calculate_stage_score(snapshot)
            cycle_stage = self._resolve_cycle_stage(snapshot, stage_score)
            stage_points.append(
                {
                    "trading_date": snapshot["trading_date"],
                    "cycle_stage": cycle_stage,
                    "stage_score": stage_score,
                }
            )

        trend_direction = self._resolve_timeline_direction(stage_points)
        turning_points = self._build_turning_points(stage_points)
        timeline = {
            "window_days": window_days,
            "stage_points_json": stage_points,
            "trend_direction": trend_direction,
            "turning_points_json": turning_points,
        }
        return {"success": True, "data": timeline}

    @staticmethod
    def _calculate_stage_score(snapshot: dict[str, Any]) -> int:
        metrics = snapshot.get("metrics", {})
        score = snapshot.get("score", 50)
        score += min(metrics.get("strongest_board_height", 0), 7) * 2
        score -= min(metrics.get("broken_limit_count", 0), 30)
        return max(0, min(100, int(score)))

    @staticmethod
    def _resolve_cycle_stage(snapshot: dict[str, Any], stage_score: int) -> str:
        metrics = snapshot.get("metrics", {})
        highest_board = metrics.get("strongest_board_height", 0)
        broken_limit = metrics.get("broken_limit_count", 0)
        market_state = snapshot.get("market_state")

        if stage_score <= 20:
            return "冰点"
        if market_state == "退潮":
            return "退潮"
        if market_state == "修复" and highest_board <= 2:
            return "修复试错"
        if stage_score >= 85 and highest_board >= 4 and broken_limit <= 5:
            return "高潮一致"
        if stage_score >= 68 and highest_board >= 2:
            return "主升发酵"
        if broken_limit >= 6 or market_state == "震荡":
            return "分歧"
        return "修复试错"

    @staticmethod
    def _resolve_action_hint(cycle_stage: str) -> str:
        mapping = {
            "冰点": "以观察和等待为主，只保留极少量试错仓位。",
            "修复试错": "优先做低位试错，确认强度后再考虑加仓。",
            "主升发酵": "优先聚焦主线核心，允许顺势参与强势票。",
            "高潮一致": "情绪过热时避免无差别追高，重点看分歧后的承接。",
            "分歧": "控制节奏，等待分歧后强者回流的确认信号。",
            "退潮": "降低仓位和频率，优先处理弱势持仓。",
        }
        return mapping[cycle_stage]

    @staticmethod
    def _build_summary(cycle_stage: str, snapshot: dict[str, Any]) -> str:
        metrics = snapshot.get("metrics", {})
        return (
            f"当前情绪处于{cycle_stage}阶段，最高连板 {metrics.get('strongest_board_height', 0)} 板，"
            f"炸板 {metrics.get('broken_limit_count', 0)} 家。"
        )

    @staticmethod
    def _resolve_timeline_direction(stage_points: list[dict[str, Any]]) -> str:
        if len(stage_points) < 2:
            return "横向"
        first = stage_points[0]["stage_score"]
        last = stage_points[-1]["stage_score"]
        if last - first >= 10:
            return "上行"
        if first - last >= 10:
            return "下行"
        return "横向"

    @staticmethod
    def _build_turning_points(stage_points: list[dict[str, Any]]) -> list[dict[str, Any]]:
        turning_points: list[dict[str, Any]] = []
        previous_stage: str | None = None
        for point in stage_points:
            if previous_stage is None:
                previous_stage = point["cycle_stage"]
                continue
            if point["cycle_stage"] != previous_stage:
                turning_points.append(
                    {
                        "trading_date": point["trading_date"],
                        "from_stage": previous_stage,
                        "to_stage": point["cycle_stage"],
                    }
                )
                previous_stage = point["cycle_stage"]
        return turning_points

    @staticmethod
    def _normalize_to_datetime(
        value: str | date | datetime | None,
    ) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        text = str(value).strip()
        for fmt in ("%Y-%m-%d", "%Y%m%d"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return None


_emotion_cycle_service: Optional[EmotionCycleService] = None


def get_emotion_cycle_service() -> EmotionCycleService:
    global _emotion_cycle_service
    if _emotion_cycle_service is None:
        _emotion_cycle_service = EmotionCycleService()
    return _emotion_cycle_service


def reset_emotion_cycle_service() -> None:
    global _emotion_cycle_service
    _emotion_cycle_service = None
