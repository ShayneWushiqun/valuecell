"""Holding diagnosis service for A-share phase one portfolio workflows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from statistics import mean
from typing import Optional

from loguru import logger

from ....adapters.assets.ashare_provider import AShareDataProvider
from ...db.repositories.portfolio_repository import (
    HoldingDiagnosisRepository,
    HoldingRepository,
)

NEWS_RISK_KEYWORDS = (
    "减持",
    "问询",
    "诉讼",
    "处罚",
    "退市",
    "停牌",
    "亏损",
    "爆雷",
    "风险",
)

ACTION_PRIORITY = {
    "卖出": 0,
    "减仓": 1,
    "观察": 2,
    "持有": 3,
}


@dataclass
class DiagnosisMetrics:
    current_price: float | None
    latest_change_percent: float | None
    profit_percent: float | None
    ma5: float | None
    ma10: float | None
    history_points: int
    news_count: int
    news_risk_title: str | None
    data_status: str


class HoldingDiagnosisService:
    """Generate and retrieve structured holding diagnoses."""

    def __init__(
        self,
        holding_repository: Optional[HoldingRepository] = None,
        diagnosis_repository: Optional[HoldingDiagnosisRepository] = None,
        ashare_provider: Optional[AShareDataProvider] = None,
    ) -> None:
        self.holding_repository = holding_repository or HoldingRepository()
        self.diagnosis_repository = diagnosis_repository or HoldingDiagnosisRepository()
        self.ashare_provider = ashare_provider or AShareDataProvider()

    def get_latest_diagnosis(self, user_id: str, holding_id: int) -> Optional[dict]:
        diagnosis = self.diagnosis_repository.get_latest_by_holding(
            user_id=user_id,
            holding_id=holding_id,
        )
        if diagnosis is None:
            return None
        return diagnosis.to_dict()

    def refresh_latest_diagnosis(self, user_id: str, holding_id: int) -> Optional[dict]:
        holding = self.holding_repository.get_holding(holding_id, user_id)
        if holding is None:
            return None

        holding_data = holding.to_dict()
        ticker = holding_data["ticker"]
        current_price = self.ashare_provider.get_real_time_price(ticker)
        history = self.ashare_provider.get_historical_prices(
            ticker,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            interval="1d",
        )
        news = self.ashare_provider.get_recent_news(ticker, limit=5)

        metrics = self._build_metrics(
            cost_price=float(holding_data["cost_price"]),
            current_price=float(current_price.price) if current_price else None,
            current_change_percent=(
                float(current_price.change_percent)
                if current_price and current_price.change_percent is not None
                else None
            ),
            history=history,
            news=news,
        )
        result = self._build_diagnosis_result(holding_data, metrics)
        diagnosis = self.diagnosis_repository.create_diagnosis(
            user_id=user_id,
            holding_id=holding_id,
            diagnosis_date=date.today(),
            action=result["action"],
            risk_level=result["risk_level"],
            confidence=result["confidence"],
            summary=result["summary"],
            key_risk=result["key_risk"],
            reasons=result["reasons"],
            trigger_conditions=result["trigger_conditions"],
            invalid_conditions=result["invalid_conditions"],
            is_focus=result["is_focus"],
            raw_context=result["raw_context"],
        )
        if diagnosis is None:
            return None
        return diagnosis.to_dict()

    def _build_metrics(
        self,
        *,
        cost_price: float,
        current_price: float | None,
        current_change_percent: float | None,
        history: list,
        news: list[dict],
    ) -> DiagnosisMetrics:
        closes = [
            float(item.close_price or item.price)
            for item in history
            if item.close_price is not None or item.price is not None
        ]
        ma5 = mean(closes[-5:]) if len(closes) >= 5 else None
        ma10 = mean(closes[-10:]) if len(closes) >= 10 else None
        latest_change_percent = current_change_percent
        if latest_change_percent is None and len(closes) >= 2 and closes[-2] != 0:
            latest_change_percent = ((closes[-1] - closes[-2]) / closes[-2]) * 100
        profit_percent = None
        if current_price is not None and cost_price > 0:
            profit_percent = ((current_price - cost_price) / cost_price) * 100
        news_risk_title = self._pick_news_risk(news)

        if current_price is None or len(closes) < 5:
            data_status = "limited"
        elif len(closes) < 10:
            data_status = "partial"
        else:
            data_status = "complete"

        return DiagnosisMetrics(
            current_price=current_price,
            latest_change_percent=latest_change_percent,
            profit_percent=profit_percent,
            ma5=ma5,
            ma10=ma10,
            history_points=len(closes),
            news_count=len(news),
            news_risk_title=news_risk_title,
            data_status=data_status,
        )

    def _build_diagnosis_result(
        self,
        holding: dict,
        metrics: DiagnosisMetrics,
    ) -> dict:
        reasons: list[str] = []
        trigger_conditions: list[str] = []
        invalid_conditions: list[str] = []
        key_risk: str | None = None

        if metrics.current_price is None:
            reasons.append("当前缺少可用实时价格，先按观察处理。")
        if metrics.history_points < 5:
            reasons.append("近 5 个交易日行情不足，趋势判断不完整。")

        price_below_cost = (
            metrics.profit_percent is not None and metrics.profit_percent <= -8
        )
        trend_broken = bool(
            metrics.current_price is not None
            and metrics.ma5 is not None
            and metrics.ma10 is not None
            and metrics.current_price < metrics.ma5 < metrics.ma10
        )
        abnormal_drop = bool(
            metrics.latest_change_percent is not None
            and metrics.latest_change_percent <= -4
        )
        strong_uptrend = bool(
            metrics.current_price is not None
            and metrics.ma5 is not None
            and metrics.ma10 is not None
            and metrics.current_price >= metrics.ma5 >= metrics.ma10
        )
        profitable = bool(
            metrics.profit_percent is not None and metrics.profit_percent >= 5
        )
        news_risk = metrics.news_risk_title is not None

        if price_below_cost:
            reasons.append("当前价格已明显跌破成本位，持仓容错空间变窄。")
            key_risk = "成本位失守"
        if trend_broken:
            reasons.append("短中期趋势走弱，价格与均线关系尚未修复。")
            key_risk = key_risk or "趋势破坏"
        if abnormal_drop:
            reasons.append("最近一个交易日跌幅偏大，短期波动风险抬升。")
            key_risk = key_risk or "短期波动放大"
        if news_risk:
            reasons.append(f"近期资讯中出现需要重点复核的风险线索：{metrics.news_risk_title}。")
            key_risk = key_risk or "公告/新闻风险"
        if strong_uptrend and profitable:
            reasons.append("价格仍运行在偏强趋势区间，持仓逻辑暂未破坏。")
        elif metrics.profit_percent is not None and metrics.profit_percent > 0:
            reasons.append("持仓仍处于盈利区间，但需要继续观察趋势延续性。")

        if metrics.data_status == "limited":
            action = "观察"
            risk_level = "中"
            confidence = "低"
            summary = (
                f"{holding['ticker']} 当前数据不完整，建议先观察并等待价格或趋势信息补齐。"
            )
            trigger_conditions = ["补齐近 5-10 日行情后再刷新诊断。"]
            invalid_conditions = ["若出现新的重大风险公告，需要立即重评。"]
        elif news_risk and (trend_broken or price_below_cost):
            action = "卖出"
            risk_level = "高"
            confidence = "中"
            summary = (
                f"{holding['ticker']} 同时出现趋势破坏与风险线索，优先考虑卖出或显著收缩仓位。"
            )
            trigger_conditions = [
                "若后续再度放量下跌，可按卖出预案执行。",
                "如风险公告继续发酵，应优先保护本金。",
            ]
            invalid_conditions = [
                "若价格重新站回短中期均线并确认企稳，可重新评估。",
            ]
        elif price_below_cost or trend_broken or abnormal_drop:
            action = "减仓"
            risk_level = "中" if not news_risk else "高"
            confidence = "中"
            summary = (
                f"{holding['ticker']} 风险信号已抬升，建议先减仓控制波动，再观察后续修复。"
            )
            trigger_conditions = [
                "若继续跌破近期支撑位，优先继续收缩仓位。",
                "若量价修复且重新站回均线，可停止减仓。",
            ]
            invalid_conditions = [
                "若价格重新回到 MA5 与 MA10 上方，本次减仓逻辑失效。",
            ]
        elif strong_uptrend or profitable:
            action = "持有"
            risk_level = "低"
            confidence = "中" if metrics.news_count == 0 else "高"
            summary = (
                f"{holding['ticker']} 当前仍以持有为主，趋势与盈亏结构暂时支持继续跟踪。"
            )
            trigger_conditions = [
                "若价格继续站稳短中期均线，可维持持有判断。",
                "若无新增风险公告，继续以持有为主。",
            ]
            invalid_conditions = [
                "若放量跌破 MA10 或出现重大负面公告，需要重评。",
            ]
        else:
            action = "观察"
            risk_level = "中"
            confidence = "中"
            summary = (
                f"{holding['ticker']} 当前多空信号并不充分，建议继续观察并等待更清晰确认。"
            )
            trigger_conditions = [
                "若价格放量突破近期平台，可重新评估为持有。",
                "若价格转弱并跌破关键均线，可转入减仓预案。",
            ]
            invalid_conditions = [
                "若资讯层出现明确风险事件，需要立即重评。",
            ]

        if not reasons:
            reasons.append("当前未发现足够强的单边信号，先按中性判断处理。")

        raw_context = {
            "current_price": metrics.current_price,
            "latest_change_percent": metrics.latest_change_percent,
            "profit_percent": metrics.profit_percent,
            "ma5": metrics.ma5,
            "ma10": metrics.ma10,
            "history_points": metrics.history_points,
            "news_count": metrics.news_count,
            "news_risk_title": metrics.news_risk_title,
            "data_status": metrics.data_status,
        }
        return {
            "action": action,
            "risk_level": risk_level,
            "confidence": confidence,
            "summary": summary,
            "key_risk": key_risk,
            "reasons": reasons[:4],
            "trigger_conditions": trigger_conditions,
            "invalid_conditions": invalid_conditions,
            "is_focus": action != "持有" or risk_level in {"中", "高"},
            "raw_context": raw_context,
        }

    def _pick_news_risk(self, news: list[dict]) -> str | None:
        for item in news:
            title = str(item.get("title") or "")
            content = str(item.get("content") or "")
            for keyword in NEWS_RISK_KEYWORDS:
                if keyword in title or keyword in content:
                    return title or keyword
        return None


_holding_diagnosis_service: Optional[HoldingDiagnosisService] = None


def get_holding_diagnosis_service() -> HoldingDiagnosisService:
    """Get global holding diagnosis service instance."""
    global _holding_diagnosis_service
    if _holding_diagnosis_service is None:
        logger.info("Initializing holding diagnosis service")
        _holding_diagnosis_service = HoldingDiagnosisService()
    return _holding_diagnosis_service
