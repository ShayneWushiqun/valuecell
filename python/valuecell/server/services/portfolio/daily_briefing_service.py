"""Daily briefing service for portfolio phase one workflows."""

from __future__ import annotations

from datetime import date
from typing import Optional

from loguru import logger

from ....adapters.assets.ashare_provider import AShareDataProvider
from ...db.repositories.portfolio_repository import (
    DailyBriefingRepository,
    HoldingDiagnosisRepository,
    HoldingRepository,
)
from ...db.repositories.watchlist_repository import WatchlistRepository
from .diagnosis_service import ACTION_PRIORITY, HoldingDiagnosisService


class DailyBriefingService:
    """Generate portfolio daily briefings from holdings and watchlists."""

    def __init__(
        self,
        holding_repository: Optional[HoldingRepository] = None,
        diagnosis_repository: Optional[HoldingDiagnosisRepository] = None,
        briefing_repository: Optional[DailyBriefingRepository] = None,
        watchlist_repository: Optional[WatchlistRepository] = None,
        diagnosis_service: Optional[HoldingDiagnosisService] = None,
        ashare_provider: Optional[AShareDataProvider] = None,
    ) -> None:
        self.holding_repository = holding_repository or HoldingRepository()
        self.diagnosis_repository = diagnosis_repository or HoldingDiagnosisRepository()
        self.briefing_repository = briefing_repository or DailyBriefingRepository()
        self.watchlist_repository = watchlist_repository or WatchlistRepository()
        self.diagnosis_service = diagnosis_service or HoldingDiagnosisService(
            holding_repository=self.holding_repository,
            diagnosis_repository=self.diagnosis_repository,
            ashare_provider=ashare_provider,
        )
        self.ashare_provider = ashare_provider or AShareDataProvider()

    def get_latest_briefing(self, user_id: str) -> Optional[dict]:
        briefing = self.briefing_repository.get_latest_briefing(user_id)
        if briefing is None:
            return None
        return briefing.to_dict()

    def refresh_daily_briefing(
        self,
        user_id: str,
        briefing_date: date | None = None,
    ) -> Optional[dict]:
        target_date = briefing_date or date.today()
        holdings = self.holding_repository.list_holdings(user_id)
        latest_map = self.diagnosis_repository.list_latest_by_user(user_id)

        holding_cards: list[dict] = []
        for holding in holdings:
            holding_data = holding.to_dict()
            holding_id = holding_data["id"]
            diagnosis = latest_map.get(holding_id)
            if diagnosis is None or date.fromisoformat(
                diagnosis.to_dict()["diagnosis_date"]
            ) != target_date:
                refreshed = self.diagnosis_service.refresh_latest_diagnosis(
                    user_id=user_id,
                    holding_id=holding_id,
                )
                diagnosis = (
                    None
                    if refreshed is None
                    else self.diagnosis_repository.get_latest_by_holding(
                        user_id=user_id,
                        holding_id=holding_id,
                    )
                )
            if diagnosis is None:
                continue
            diagnosis_data = diagnosis.to_dict()
            holding_cards.append(
                {
                    "holding_id": holding_id,
                    "ticker": holding_data["ticker"],
                    "asset_name": holding_data["asset_name"],
                    "action": diagnosis_data["action"],
                    "risk_level": diagnosis_data["risk_level"],
                    "summary": diagnosis_data["summary"],
                    "is_focus": diagnosis_data["is_focus"],
                }
            )

        holding_cards.sort(
            key=lambda item: (
                ACTION_PRIORITY.get(item["action"], 99),
                0 if item["is_focus"] else 1,
                item["ticker"],
            )
        )

        watchlist_highlights = self._build_watchlist_highlights(user_id)
        focus_cards = self._build_focus_cards(holding_cards, watchlist_highlights)
        headline = self._build_headline(holding_cards, watchlist_highlights)
        action_summary = self._build_action_summary(holding_cards)

        summary = {
            "headline": headline,
            "focus_items": focus_cards,
            "holding_actions": action_summary,
            "watchlist_highlights": watchlist_highlights[:3],
        }
        content_markdown = self._render_markdown(summary)
        briefing = self.briefing_repository.upsert_briefing(
            user_id=user_id,
            briefing_date=target_date,
            content_markdown=content_markdown,
            summary=summary,
        )
        if briefing is None:
            return None
        return briefing.to_dict()

    def _build_watchlist_highlights(self, user_id: str) -> list[dict]:
        watchlists = self.watchlist_repository.get_user_watchlists(user_id)
        seen: set[str] = set()
        highlights: list[dict] = []
        for watchlist in watchlists:
            for item in watchlist.items:
                if item.ticker in seen:
                    continue
                seen.add(item.ticker)
                price = self.ashare_provider.get_real_time_price(item.ticker)
                if price is None or price.change_percent is None:
                    continue
                change_percent = float(price.change_percent)
                if abs(change_percent) < 2.5:
                    continue
                highlights.append(
                    {
                        "ticker": item.ticker,
                        "display_name": item.display_name,
                        "change_percent": change_percent,
                        "signal": "异动上行" if change_percent > 0 else "异动回落",
                    }
                )
        highlights.sort(key=lambda item: abs(item["change_percent"]), reverse=True)
        return highlights

    def _build_focus_cards(
        self,
        holding_cards: list[dict],
        watchlist_highlights: list[dict],
    ) -> list[dict]:
        focus_items: list[dict] = []
        for item in holding_cards[:3]:
            focus_items.append(
                {
                    "type": "holding",
                    "ticker": item["ticker"],
                    "title": f"{item['ticker']}：{item['action']}",
                    "summary": item["summary"],
                }
            )
        remaining = max(0, 5 - len(focus_items))
        for item in watchlist_highlights[:remaining]:
            focus_items.append(
                {
                    "type": "watchlist",
                    "ticker": item["ticker"],
                    "title": f"{item['ticker']}：{item['signal']}",
                    "summary": f"今日涨跌幅 {item['change_percent']:.2f}%，建议加入重点观察。",
                }
            )
        return focus_items[:5]

    def _build_headline(
        self,
        holding_cards: list[dict],
        watchlist_highlights: list[dict],
    ) -> str:
        if holding_cards:
            focus = holding_cards[0]
            return f"今日优先关注 {focus['ticker']}，当前建议为{focus['action']}。"
        if watchlist_highlights:
            focus = watchlist_highlights[0]
            return f"今日自选中 {focus['ticker']} 波动最明显，建议优先查看。"
        return "今日没有明显异常，优先复核现有持仓逻辑与自选节奏。"

    def _build_action_summary(self, holding_cards: list[dict]) -> list[dict]:
        if not holding_cards:
            return [
                {
                    "label": "持仓建议",
                    "value": "当前尚无持仓，建议先录入核心持仓后再生成更完整摘要。",
                }
            ]
        grouped = {"持有": 0, "减仓": 0, "卖出": 0, "观察": 0}
        for item in holding_cards:
            grouped[item["action"]] = grouped.get(item["action"], 0) + 1
        return [
            {"label": "持有", "value": str(grouped["持有"])},
            {"label": "减仓", "value": str(grouped["减仓"])},
            {"label": "卖出", "value": str(grouped["卖出"])},
            {"label": "观察", "value": str(grouped["观察"])},
        ]

    def _render_markdown(self, summary: dict) -> str:
        lines = [f"# 每日摘要", "", summary["headline"], "", "## 今日重点"]
        focus_items = summary.get("focus_items") or []
        if not focus_items:
            lines.append("- 今日暂无重点异动，优先看持仓纪律是否需要更新。")
        else:
            lines.extend(
                [f"- {item['title']}：{item['summary']}" for item in focus_items]
            )
        lines.append("")
        lines.append("## 动作汇总")
        for item in summary.get("holding_actions", []):
            lines.append(f"- {item['label']}：{item['value']}")
        return "\n".join(lines)


_daily_briefing_service: Optional[DailyBriefingService] = None


def get_daily_briefing_service() -> DailyBriefingService:
    """Get global daily briefing service instance."""
    global _daily_briefing_service
    if _daily_briefing_service is None:
        logger.info("Initializing daily briefing service")
        _daily_briefing_service = DailyBriefingService()
    return _daily_briefing_service
