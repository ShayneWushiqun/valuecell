from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from .short_cycle_data_service import ShortCycleDataService


class ThemeFocusService:
    def __init__(
        self,
        short_cycle_data_service: Optional[ShortCycleDataService] = None,
    ) -> None:
        self.short_cycle_data_service = short_cycle_data_service or ShortCycleDataService()

    def get_theme_focus_snapshot(
        self,
        trade_date: str | date | datetime | None = None,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
        top_n: int = 3,
    ) -> dict[str, Any]:
        payload = self.short_cycle_data_service.get_theme_focus_data(
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
        )
        if not payload.get("success"):
            return payload

        data = payload["data"]
        ths_index_rows = self._rows(data.get("ths_index"))
        ths_daily_rows = self._rows(data.get("ths_daily"))
        ths_member_rows = self._rows(data.get("ths_member"))
        moneyflow_ind_ths_rows = self._rows(data.get("moneyflow_ind_ths"))
        moneyflow_ind_dc_rows = self._rows(data.get("moneyflow_ind_dc"))
        kpl_rows = self._rows(data.get("kpl_list"))
        hot_rows = self._rows(data.get("ths_hot"))

        daily_map = self._build_latest_map(ths_daily_rows, "ts_code")
        moneyflow_ths_map = self._build_latest_map(moneyflow_ind_ths_rows, "ts_code")
        moneyflow_dc_map = self._build_latest_map(moneyflow_ind_dc_rows, "ts_code")
        member_map = self._build_member_map(ths_member_rows)
        kpl_theme_map = self._build_theme_signal_map(kpl_rows)
        hot_theme_map = self._build_theme_signal_map(hot_rows)

        snapshots: list[dict[str, Any]] = []
        for row in ths_index_rows:
            theme_code = self._pick_text(row, "ts_code", "concept_code", "code")
            theme_name = self._pick_text(row, "name", "concept_name", "industry_name")
            if not theme_code or not theme_name:
                continue

            daily_row = daily_map.get(theme_code, {})
            moneyflow_ths_row = moneyflow_ths_map.get(theme_code, {})
            moneyflow_dc_row = moneyflow_dc_map.get(theme_code, {})
            representative_tickers = member_map.get(theme_code, [])[:5]
            kpl_signal = kpl_theme_map.get(theme_name, {"count": 0, "leaders": []})
            hot_signal = hot_theme_map.get(theme_name, {"count": 0, "leaders": []})

            change_value = self._pick_float(
                daily_row,
                "pct_chg",
                "change_pct",
                "change",
                "pct_change",
            )
            ths_flow_value = self._pick_float(
                moneyflow_ths_row,
                "net_amount",
                "net_mf_amount",
                "net_inflow",
            )
            dc_flow_value = self._pick_float(
                moneyflow_dc_row,
                "net_amount",
                "net_mf_amount",
                "net_inflow",
            )
            score = self._calculate_theme_score(
                change_value=change_value,
                ths_flow_value=ths_flow_value,
                dc_flow_value=dc_flow_value,
                kpl_count=kpl_signal["count"],
                hot_count=hot_signal["count"],
                representative_count=len(representative_tickers),
            )
            theme_state = self._resolve_theme_state(score, change_value)
            expectation_gap_level = self._resolve_expectation_gap(
                score=score,
                hot_count=hot_signal["count"],
                kpl_count=kpl_signal["count"],
            )
            leaders = self._merge_tickers(
                kpl_signal["leaders"],
                hot_signal["leaders"],
                representative_tickers,
            )

            snapshots.append(
                {
                    "trading_date": payload.get("trade_date"),
                    "theme_name": theme_name,
                    "theme_code": theme_code,
                    "theme_state": theme_state,
                    "summary": self._build_summary(
                        theme_name=theme_name,
                        theme_state=theme_state,
                        change_value=change_value,
                        kpl_count=kpl_signal["count"],
                        hot_count=hot_signal["count"],
                    ),
                    "representative_tickers_json": representative_tickers,
                    "rank": 0,
                    "expectation_gap_level": expectation_gap_level,
                    "core_leaders_json": leaders[:3],
                    "core_institutions_json": self._build_core_institutions(
                        ths_flow_value=ths_flow_value,
                        dc_flow_value=dc_flow_value,
                    ),
                    "metrics": {
                        "score": score,
                        "change_value": change_value,
                        "ths_flow_value": ths_flow_value,
                        "dc_flow_value": dc_flow_value,
                        "kpl_count": kpl_signal["count"],
                        "hot_count": hot_signal["count"],
                    },
                }
            )

        snapshots.sort(
            key=lambda item: (
                item["metrics"]["score"],
                len(item["representative_tickers_json"]),
            ),
            reverse=True,
        )
        for index, item in enumerate(snapshots, start=1):
            item["rank"] = index

        return {
            "success": True,
            "data": {
                "trading_date": payload.get("trade_date"),
                "items": snapshots[:top_n],
                "count": len(snapshots[:top_n]),
            },
        }

    @staticmethod
    def _rows(frame_payload: dict[str, Any] | None) -> list[dict[str, Any]]:
        return list((frame_payload or {}).get("rows") or [])

    @staticmethod
    def _pick_text(row: dict[str, Any], *keys: str) -> str:
        for key in keys:
            value = str(row.get(key) or "").strip()
            if value:
                return value
        return ""

    @staticmethod
    def _pick_float(row: dict[str, Any], *keys: str) -> float:
        for key in keys:
            value = row.get(key)
            if value in (None, ""):
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
        return 0.0

    @staticmethod
    def _build_latest_map(
        rows: list[dict[str, Any]],
        key_name: str,
    ) -> dict[str, dict[str, Any]]:
        latest_map: dict[str, dict[str, Any]] = {}
        for row in rows:
            key = str(row.get(key_name) or "").strip()
            if not key or key in latest_map:
                continue
            latest_map[key] = row
        return latest_map

    @staticmethod
    def _build_member_map(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
        member_map: dict[str, list[str]] = {}
        for row in rows:
            theme_code = str(row.get("ts_code") or "").strip()
            ticker = str(row.get("con_ticker") or row.get("ticker") or "").strip()
            if not theme_code or not ticker:
                continue
            member_map.setdefault(theme_code, [])
            if ticker not in member_map[theme_code]:
                member_map[theme_code].append(ticker)
        return member_map

    def _build_theme_signal_map(
        self,
        rows: list[dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        theme_map: dict[str, dict[str, Any]] = {}
        for row in rows:
            labels = [
                self._pick_text(row, "concept_name"),
                self._pick_text(row, "industry_name"),
                self._pick_text(row, "reason_type"),
                self._pick_text(row, "theme"),
                self._pick_text(row, "name"),
            ]
            ticker = self._pick_text(row, "ticker", "con_ticker")
            for label in labels:
                if not label:
                    continue
                bucket = theme_map.setdefault(label, {"count": 0, "leaders": []})
                bucket["count"] += 1
                if ticker and ticker not in bucket["leaders"]:
                    bucket["leaders"].append(ticker)
        return theme_map

    @staticmethod
    def _calculate_theme_score(
        *,
        change_value: float,
        ths_flow_value: float,
        dc_flow_value: float,
        kpl_count: int,
        hot_count: int,
        representative_count: int,
    ) -> int:
        score = 45.0
        score += min(max(change_value, -10.0), 10.0) * 2.0
        score += min(max(ths_flow_value, -20.0), 20.0) * 0.8
        score += min(max(dc_flow_value, -20.0), 20.0) * 0.6
        score += min(kpl_count, 8) * 4.0
        score += min(hot_count, 10) * 2.0
        score += min(representative_count, 10) * 1.0
        return max(0, min(100, int(round(score))))

    @staticmethod
    def _resolve_theme_state(score: int, change_value: float) -> str:
        if score >= 75 and change_value >= 1.5:
            return "加强"
        if score >= 58:
            return "活跃"
        if score >= 40:
            return "观察"
        return "退潮"

    @staticmethod
    def _resolve_expectation_gap(score: int, hot_count: int, kpl_count: int) -> str:
        if score >= 78 and hot_count + kpl_count >= 6:
            return "高"
        if score >= 55:
            return "中"
        return "低"

    @staticmethod
    def _merge_tickers(*ticker_groups: list[str]) -> list[str]:
        merged: list[str] = []
        for group in ticker_groups:
            for ticker in group:
                if ticker not in merged:
                    merged.append(ticker)
        return merged

    @staticmethod
    def _build_core_institutions(
        *,
        ths_flow_value: float,
        dc_flow_value: float,
    ) -> list[dict[str, Any]]:
        institutions: list[dict[str, Any]] = []
        if ths_flow_value > 0:
            institutions.append({"source": "moneyflow_ind_ths", "net_inflow": ths_flow_value})
        if dc_flow_value > 0:
            institutions.append({"source": "moneyflow_ind_dc", "net_inflow": dc_flow_value})
        return institutions

    @staticmethod
    def _build_summary(
        *,
        theme_name: str,
        theme_state: str,
        change_value: float,
        kpl_count: int,
        hot_count: int,
    ) -> str:
        return (
            f"{theme_name} 当前处于{theme_state}状态，"
            f"板块涨跌幅约 {change_value:.2f}%，"
            f"短线联动 {kpl_count} 次，热榜关联 {hot_count} 次。"
        )


_theme_focus_service: Optional[ThemeFocusService] = None


def get_theme_focus_service() -> ThemeFocusService:
    global _theme_focus_service
    if _theme_focus_service is None:
        _theme_focus_service = ThemeFocusService()
    return _theme_focus_service


def reset_theme_focus_service() -> None:
    global _theme_focus_service
    _theme_focus_service = None
