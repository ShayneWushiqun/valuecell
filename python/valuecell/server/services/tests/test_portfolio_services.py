from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from valuecell.server.services.portfolio.daily_briefing_service import (
    DailyBriefingService,
)
from valuecell.server.services.portfolio.diagnosis_service import (
    HoldingDiagnosisService,
)


@dataclass
class FakeHolding:
    payload: dict

    @property
    def id(self) -> int:
        return self.payload["id"]

    def to_dict(self) -> dict:
        return dict(self.payload)


@dataclass
class FakeDiagnosis:
    payload: dict

    def to_dict(self) -> dict:
        return dict(self.payload)


@dataclass
class FakeBriefing:
    payload: dict

    def to_dict(self) -> dict:
        return dict(self.payload)


@dataclass
class FakePrice:
    price: float
    change_percent: float | None = None
    close_price: float | None = None


class FakeHoldingRepository:
    def __init__(self, holding: dict):
        self.holding = FakeHolding(holding)

    def get_holding(self, holding_id: int, user_id: str):
        if holding_id != self.holding.id:
            return None
        return self.holding

    def list_holdings(self, user_id: str):
        return [self.holding]


class FakeDiagnosisRepository:
    def __init__(self):
        self.rows: list[dict] = []

    def create_diagnosis(self, **kwargs):
        payload = {
            "id": len(self.rows) + 1,
            "holding_id": kwargs["holding_id"],
            "user_id": kwargs["user_id"],
            "diagnosis_date": kwargs["diagnosis_date"].isoformat(),
            "action": kwargs["action"],
            "risk_level": kwargs["risk_level"],
            "confidence": kwargs["confidence"],
            "summary": kwargs["summary"],
            "key_risk": kwargs["key_risk"],
            "reasons": list(kwargs["reasons"]),
            "trigger_conditions": list(kwargs["trigger_conditions"]),
            "invalid_conditions": list(kwargs["invalid_conditions"]),
            "is_focus": kwargs["is_focus"],
            "raw_context": dict(kwargs["raw_context"]),
            "created_at": datetime.now().isoformat(),
        }
        self.rows.append(payload)
        return FakeDiagnosis(payload)

    def get_latest_by_holding(self, *, user_id: str, holding_id: int):
        for row in reversed(self.rows):
            if row["user_id"] == user_id and row["holding_id"] == holding_id:
                return FakeDiagnosis(row)
        return None

    def list_latest_by_user(self, user_id: str):
        latest: dict[int, FakeDiagnosis] = {}
        for row in reversed(self.rows):
            if row["user_id"] != user_id:
                continue
            if row["holding_id"] not in latest:
                latest[row["holding_id"]] = FakeDiagnosis(row)
        return latest


class FakeBriefingRepository:
    def __init__(self):
        self.payload: dict | None = None

    def get_latest_briefing(self, user_id: str):
        if self.payload is None:
            return None
        return FakeBriefing(self.payload)

    def upsert_briefing(self, **kwargs):
        self.payload = {
            "id": 1,
            "user_id": kwargs["user_id"],
            "briefing_date": kwargs["briefing_date"].isoformat(),
            "content_markdown": kwargs["content_markdown"],
            "summary": dict(kwargs["summary"]),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        return FakeBriefing(self.payload)


class FakeWatchlistItem:
    def __init__(self, ticker: str, display_name: str | None):
        self.ticker = ticker
        self.display_name = display_name


class FakeWatchlist:
    def __init__(self, items: list[FakeWatchlistItem]):
        self.items = items


class FakeWatchlistRepository:
    def get_user_watchlists(self, user_id: str):
        return [FakeWatchlist([FakeWatchlistItem("SSE:600519", "贵州茅台")])]


class FakeAshareProvider:
    def get_real_time_price(self, ticker: str):
        if ticker == "SSE:600519":
            return FakePrice(price=1460.0, change_percent=-5.2)
        return FakePrice(price=22.5, change_percent=3.8)

    def get_historical_prices(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
    ):
        return [
            FakePrice(price=1500, close_price=1500),
            FakePrice(price=1492, close_price=1492),
            FakePrice(price=1485, close_price=1485),
            FakePrice(price=1478, close_price=1478),
            FakePrice(price=1470, close_price=1470),
            FakePrice(price=1468, close_price=1468),
            FakePrice(price=1465, close_price=1465),
            FakePrice(price=1462, close_price=1462),
            FakePrice(price=1461, close_price=1461),
            FakePrice(price=1460, close_price=1460),
        ]

    def get_recent_news(self, ticker: str, limit: int = 5):
        return [
            {
                "title": "公司收到监管问询函",
                "content": "监管问询触发市场风险关注。",
            }
        ]


def test_holding_diagnosis_service_generates_structured_sell_signal() -> None:
    holding_repository = FakeHoldingRepository(
        {
            "id": 1,
            "user_id": "default_user",
            "ticker": "SSE:600519",
            "exchange": "SSE",
            "asset_name": "贵州茅台",
            "quantity": 100,
            "cost_price": 1600.0,
            "position_weight": 25.0,
            "buy_date": "2026-04-01",
            "thesis_note": "龙头白马",
            "notes": "",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
    )
    diagnosis_repository = FakeDiagnosisRepository()
    service = HoldingDiagnosisService(
        holding_repository=holding_repository,
        diagnosis_repository=diagnosis_repository,
        ashare_provider=FakeAshareProvider(),
    )

    diagnosis = service.refresh_latest_diagnosis("default_user", 1)

    assert diagnosis is not None
    assert diagnosis["action"] == "卖出"
    assert diagnosis["risk_level"] == "高"
    assert diagnosis["summary"]
    assert diagnosis["reasons"]
    assert diagnosis["raw_context"]["current_price"] == 1460.0


def test_daily_briefing_service_prioritizes_holding_focus() -> None:
    holding_repository = FakeHoldingRepository(
        {
            "id": 1,
            "user_id": "default_user",
            "ticker": "SSE:600519",
            "exchange": "SSE",
            "asset_name": "贵州茅台",
            "quantity": 100,
            "cost_price": 1600.0,
            "position_weight": 25.0,
            "buy_date": "2026-04-01",
            "thesis_note": "龙头白马",
            "notes": "",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
    )
    diagnosis_repository = FakeDiagnosisRepository()
    diagnosis_service = HoldingDiagnosisService(
        holding_repository=holding_repository,
        diagnosis_repository=diagnosis_repository,
        ashare_provider=FakeAshareProvider(),
    )
    diagnosis_service.refresh_latest_diagnosis("default_user", 1)

    briefing_service = DailyBriefingService(
        holding_repository=holding_repository,
        diagnosis_repository=diagnosis_repository,
        briefing_repository=FakeBriefingRepository(),
        watchlist_repository=FakeWatchlistRepository(),
        diagnosis_service=diagnosis_service,
        ashare_provider=FakeAshareProvider(),
    )

    briefing = briefing_service.refresh_daily_briefing(
        "default_user",
        briefing_date=date.today(),
    )

    assert briefing is not None
    assert briefing["summary"]["headline"].startswith("今日优先关注 SSE:600519")
    assert briefing["summary"]["focus_items"]
    assert briefing["summary"]["holding_actions"]
