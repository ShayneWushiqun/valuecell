from __future__ import annotations

from typing import Any, Optional

from .theme_focus_service import ThemeFocusService


class ThemeCandidateService:
    def __init__(
        self,
        theme_focus_service: Optional[ThemeFocusService] = None,
    ) -> None:
        self.theme_focus_service = theme_focus_service or ThemeFocusService()

    def get_theme_candidates(
        self,
        top_n: int = 12,
    ) -> dict[str, Any]:
        result = self.theme_focus_service.get_theme_focus_snapshot(top_n=max(top_n * 2, top_n))
        if not result.get("success"):
            return result

        data = result.get("data") or {}
        items = self._build_candidates(list(data.get("items") or []))
        return {
            "success": True,
            "data": {
                "trading_date": data.get("trading_date"),
                "items": items[:top_n],
                "count": len(items[:top_n]),
            },
        }

    def _build_candidates(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized_items: list[dict[str, Any]] = []
        for item in items:
            theme_name = str(item.get("theme_name") or "")
            leaders = list(item.get("core_leaders_json") or [])
            representatives = list(item.get("representative_tickers_json") or [])
            is_st_related = self._is_st_related_theme(
                theme_name=theme_name,
                leaders=leaders,
                representatives=representatives,
            )
            preferred_market = self._resolve_preferred_market(leaders + representatives)
            primary_representative = (
                leaders[0] if leaders else (representatives[0] if representatives else None)
            )
            normalized_items.append(
                {
                    **item,
                    "theme_state": self._normalize_theme_state(item.get("theme_state")),
                    "trend_state": self._resolve_trend_state(item),
                    "hot_level": item.get("metrics", {}).get("hot_count", 0),
                    "preferred_market": preferred_market,
                    "primary_representative": primary_representative,
                    "representative_tickers": representatives,
                    "is_suitable_for_direct_participation": self._is_suitable_for_direct_participation(
                        item=item,
                        preferred_market=preferred_market,
                        is_st_related=is_st_related,
                    ),
                    "participation_hint": self._build_theme_participation_hint(
                        item=item,
                        preferred_market=preferred_market,
                        is_st_related=is_st_related,
                    ),
                    "etf_hint": self._build_theme_etf_hint(
                        preferred_market=preferred_market,
                        is_st_related=is_st_related,
                    ),
                }
            )

        normalized_items.sort(
            key=lambda item: (
                1 if self._is_st_related_theme_item(item) else 0,
                0 if item.get("is_suitable_for_direct_participation") else 1,
                int(item.get("rank", 999) or 999),
            )
        )
        return normalized_items

    @staticmethod
    def _normalize_theme_state(theme_state: Any) -> str:
        if theme_state == "观察":
            return "分歧"
        return str(theme_state or "分歧")

    @staticmethod
    def _resolve_trend_state(item: dict[str, Any]) -> str:
        change_value = float(item.get("metrics", {}).get("change_value", 0) or 0)
        state = str(item.get("theme_state") or "")
        if "退潮" in state:
            return "走弱"
        if state in {"加强", "活跃"} and change_value > 1:
            return "加强"
        if state in {"分歧", "观察"}:
            return "分歧"
        return "横盘"

    @staticmethod
    def _resolve_preferred_market(tickers: list[str]) -> str:
        has_kcb = any(ticker.startswith("SSE:688") for ticker in tickers)
        has_gem = any(ticker.startswith("SZSE:30") for ticker in tickers)
        if has_kcb:
            return "科创板为主"
        if has_gem:
            return "创业板为主"
        return "主板为主"

    @staticmethod
    def _contains_st_marker(value: str | None) -> bool:
        text = str(value or "").upper().replace(" ", "")
        return "ST" in text

    def _is_st_related_theme(
        self,
        *,
        theme_name: str,
        leaders: list[str],
        representatives: list[str],
    ) -> bool:
        if self._contains_st_marker(theme_name):
            return True
        return any(
            self._contains_st_marker(text)
            for text in [*leaders, *representatives]
        )

    def _is_st_related_theme_item(self, item: dict[str, Any]) -> bool:
        theme_name = str(item.get("theme_name") or "")
        leaders = list(item.get("core_leaders_json") or [])
        representatives = list(item.get("representative_tickers_json") or [])
        primary_representative = item.get("primary_representative")
        return self._is_st_related_theme(
            theme_name=theme_name,
            leaders=[*leaders, str(primary_representative or "")],
            representatives=representatives,
        )

    def _is_suitable_for_direct_participation(
        self,
        *,
        item: dict[str, Any],
        preferred_market: str,
        is_st_related: bool,
    ) -> bool:
        if is_st_related:
            return False
        if preferred_market == "科创板为主":
            return False
        if preferred_market == "创业板为主":
            return str(item.get("expectation_gap_level")) != "高"
        return str(item.get("theme_state")) in {"加强", "活跃"}

    def _build_theme_participation_hint(
        self,
        *,
        item: dict[str, Any],
        preferred_market: str,
        is_st_related: bool,
    ) -> str:
        if is_st_related:
            return "疑似 ST 或高风险方向，默认回避，不建议参与。"
        if preferred_market == "科创板为主":
            return "方向可继续观察，但直接参与需更谨慎，优先考虑替代跟踪工具。"
        if preferred_market == "创业板为主":
            return "方向有热度，但不建议无差别追高，优先低吸或等待更好位置。"
        if str(item.get("theme_state")) == "退潮":
            return "方向走弱，更适合观察而不是直接参与。"
        return "可优先围绕主板核心票观察承接，再决定是否参与。"

    @staticmethod
    def _build_theme_etf_hint(
        *,
        preferred_market: str,
        is_st_related: bool,
    ) -> dict[str, str] | None:
        if is_st_related:
            return None
        if preferred_market == "主板为主":
            return None
        return {
            "title": "可考虑相关场内 ETF 作为替代观察",
            "summary": "当核心个股买不进去、追高性价比偏低，或主要集中在创业板/科创板时，可考虑相关场内 ETF 作为替代观察，暂无匹配具体 ETF。",
            "risk_hint": "ETF 仍需关注流动性、跟踪误差和板块快速退潮带来的回撤风险。",
        }


_theme_candidate_service: Optional[ThemeCandidateService] = None


def get_theme_candidate_service() -> ThemeCandidateService:
    global _theme_candidate_service
    if _theme_candidate_service is None:
        _theme_candidate_service = ThemeCandidateService()
    return _theme_candidate_service


def reset_theme_candidate_service() -> None:
    global _theme_candidate_service
    _theme_candidate_service = None
