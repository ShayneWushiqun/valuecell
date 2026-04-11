from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from .short_cycle_data_service import ShortCycleDataService


class MarketPulseService:
    def __init__(
        self,
        short_cycle_data_service: Optional[ShortCycleDataService] = None,
    ) -> None:
        self.short_cycle_data_service = short_cycle_data_service or ShortCycleDataService()

    def get_market_pulse_snapshot(
        self,
        trade_date: str | date | datetime | None = None,
    ) -> dict[str, Any]:
        payload = self.short_cycle_data_service.get_market_pulse_data(trade_date)
        if not payload.get("success"):
            return payload

        data = payload["data"]
        daily_info_row = self._first_row(data.get("daily_info"))
        limit_rows = self._rows(data.get("limit_list_d"))
        kpl_rows = self._rows(data.get("kpl_list"))
        hot_rows = self._rows(data.get("ths_hot"))

        metrics = {
            "up_limit_count": self._pick_number(
                daily_info_row,
                "up_limit",
                "up_limit_num",
                "zt_num",
                default=self._count_limit_rows(limit_rows, ("涨停", "U")),
            ),
            "down_limit_count": self._pick_number(
                daily_info_row,
                "down_limit",
                "down_limit_num",
                "dt_num",
                default=self._count_limit_rows(limit_rows, ("跌停", "D")),
            ),
            "broken_limit_count": self._pick_number(
                daily_info_row,
                "broken_limit",
                "zbg_num",
                default=self._count_broken_rows(limit_rows, kpl_rows),
            ),
            "hot_count": len(hot_rows),
            "active_board_count": self._unique_count(
                kpl_rows,
                "theme",
                "reason_type",
                "industry_name",
                "concept",
            ),
            "strongest_board_height": self._pick_max_number(
                kpl_rows,
                "high_days",
                "continue_num",
                "limit_up_num",
                "lianban",
            ),
        }
        score = self._calculate_market_score(metrics)
        market_state = self._resolve_market_state(score, metrics)
        action_hint = self._resolve_action_hint(market_state)
        confidence = self._resolve_confidence(metrics)
        signals = self._build_signals(metrics)

        snapshot = {
            "trading_date": payload.get("trade_date"),
            "market_state": market_state,
            "summary": self._build_summary(market_state, metrics),
            "confidence": confidence,
            "action_hint": action_hint,
            "signals_json": signals,
            "score": score,
            "metrics": metrics,
        }
        return {"success": True, "data": snapshot}

    @staticmethod
    def _first_row(frame_payload: dict[str, Any] | None) -> dict[str, Any]:
        rows = (frame_payload or {}).get("rows") or []
        if not rows:
            return {}
        return rows[0]

    @staticmethod
    def _rows(frame_payload: dict[str, Any] | None) -> list[dict[str, Any]]:
        return list((frame_payload or {}).get("rows") or [])

    @staticmethod
    def _pick_number(row: dict[str, Any], *keys: str, default: int = 0) -> int:
        for key in keys:
            value = row.get(key)
            if value in (None, ""):
                continue
            try:
                return int(float(value))
            except (TypeError, ValueError):
                continue
        return default

    @staticmethod
    def _pick_max_number(rows: list[dict[str, Any]], *keys: str) -> int:
        max_value = 0
        for row in rows:
            for key in keys:
                value = row.get(key)
                if value in (None, ""):
                    continue
                try:
                    max_value = max(max_value, int(float(value)))
                except (TypeError, ValueError):
                    continue
        return max_value

    @staticmethod
    def _unique_count(rows: list[dict[str, Any]], *keys: str) -> int:
        values: set[str] = set()
        for row in rows:
            for key in keys:
                value = str(row.get(key) or "").strip()
                if value:
                    values.add(value)
                    break
        return len(values)

    @staticmethod
    def _count_limit_rows(rows: list[dict[str, Any]], markers: tuple[str, ...]) -> int:
        count = 0
        for row in rows:
            text = " ".join(
                str(row.get(key) or "")
                for key in ("limit", "status", "tag", "type", "limit_type")
            )
            if any(marker in text for marker in markers):
                count += 1
        return count

    @staticmethod
    def _count_broken_rows(
        limit_rows: list[dict[str, Any]],
        kpl_rows: list[dict[str, Any]],
    ) -> int:
        broken = 0
        for row in [*limit_rows, *kpl_rows]:
            text = " ".join(
                str(row.get(key) or "")
                for key in ("limit", "status", "tag", "type", "limit_type")
            )
            if "炸" in text:
                broken += 1
        return broken

    @staticmethod
    def _calculate_market_score(metrics: dict[str, int]) -> int:
        score = 50
        score += min(metrics["up_limit_count"], 120) * 0.25
        score -= min(metrics["down_limit_count"], 80) * 0.5
        score -= min(metrics["broken_limit_count"], 50) * 0.35
        score += min(metrics["active_board_count"], 15) * 1.2
        score += min(metrics["strongest_board_height"], 7) * 2.5
        score += min(metrics["hot_count"], 30) * 0.4
        return max(0, min(100, int(round(score))))

    @staticmethod
    def _resolve_market_state(score: int, metrics: dict[str, int]) -> str:
        if metrics["down_limit_count"] >= metrics["up_limit_count"] and score < 35:
            return "退潮"
        if score >= 75:
            return "进攻"
        if score >= 60:
            return "修复"
        if score >= 48:
            return "轮动"
        if score >= 35:
            return "震荡"
        return "退潮"

    @staticmethod
    def _resolve_action_hint(market_state: str) -> str:
        mapping = {
            "进攻": "优先顺着强势方向做核心票，允许小幅提高进攻仓位。",
            "修复": "以修复试错为主，优先低吸确认过强度的方向。",
            "轮动": "更适合轻仓快切，不宜在弱势题材重仓停留。",
            "震荡": "耐心等待更明确主线，控制追涨频率。",
            "退潮": "优先防守，降低仓位并回避高位接力。",
        }
        return mapping[market_state]

    @staticmethod
    def _resolve_confidence(metrics: dict[str, int]) -> str:
        if metrics["up_limit_count"] + metrics["down_limit_count"] >= 20:
            return "高"
        if metrics["active_board_count"] >= 2:
            return "中"
        return "低"

    @staticmethod
    def _build_signals(metrics: dict[str, int]) -> list[dict[str, Any]]:
        return [
            {"label": "涨停家数", "value": metrics["up_limit_count"]},
            {"label": "跌停家数", "value": metrics["down_limit_count"]},
            {"label": "炸板家数", "value": metrics["broken_limit_count"]},
            {"label": "活跃方向数", "value": metrics["active_board_count"]},
            {"label": "最高连板", "value": metrics["strongest_board_height"]},
            {"label": "热榜样本数", "value": metrics["hot_count"]},
        ]

    @staticmethod
    def _build_summary(market_state: str, metrics: dict[str, int]) -> str:
        return (
            f"当前市场偏{market_state}，涨停 {metrics['up_limit_count']} 家、"
            f"跌停 {metrics['down_limit_count']} 家、炸板 {metrics['broken_limit_count']} 家，"
            f"最高连板 {metrics['strongest_board_height']} 板。"
        )


_market_pulse_service: Optional[MarketPulseService] = None


def get_market_pulse_service() -> MarketPulseService:
    global _market_pulse_service
    if _market_pulse_service is None:
        _market_pulse_service = MarketPulseService()
    return _market_pulse_service


def reset_market_pulse_service() -> None:
    global _market_pulse_service
    _market_pulse_service = None
