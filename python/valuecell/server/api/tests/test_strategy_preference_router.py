from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.strategy_preference import create_strategy_preference_router


class FakeStrategyPreferenceService:
    def get_templates(self):
        return {
            "items": [
                {
                    "template_id": "trend_continuation",
                    "title": "趋势延续",
                    "summary": "优先延续性和核心票强趋势。",
                    "preferred_themes": ["AI算力"],
                    "holding_period_days": 10,
                    "risk_style": "balanced",
                    "buy_style": "right_side",
                    "avoid_risks": ["ST"],
                    "accept_high_position": False,
                    "prefer_expectation_gap": True,
                    "prefer_leader_or_core": True,
                    "note": "",
                }
            ],
            "count": 1,
        }

    def get_effective_profile(self, user_id: str = "default_user"):
        return {
            "profile_id": 1,
            "kind": "ashare_strategy_preference",
            "schema_version": 1,
            "template_id": "trend_continuation",
            "template_title": "趋势延续",
            "preferred_themes": ["AI算力"],
            "holding_period_days": 10,
            "risk_style": "balanced",
            "buy_style": "right_side",
            "avoid_risks": ["ST"],
            "accept_high_position": False,
            "prefer_expectation_gap": True,
            "prefer_leader_or_core": True,
            "note": "",
        }

    def save_profile(self, user_id: str, payload: dict):
        return {
            **self.get_effective_profile(user_id),
            **payload,
        }


def test_strategy_preference_router_returns_profile_and_templates(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.strategy_preference.get_strategy_preference_service",
        lambda: FakeStrategyPreferenceService(),
    )
    app = FastAPI()
    app.include_router(create_strategy_preference_router(), prefix="/api/v1")
    client = TestClient(app)

    templates_response = client.get("/api/v1/strategy-preferences/templates")
    profile_response = client.get("/api/v1/strategy-preferences/profile")

    assert templates_response.status_code == 200
    assert profile_response.status_code == 200
    assert templates_response.json()["data"]["items"][0]["template_id"] == "trend_continuation"
    assert profile_response.json()["data"]["template_id"] == "trend_continuation"


def test_strategy_preference_router_updates_profile(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.strategy_preference.get_strategy_preference_service",
        lambda: FakeStrategyPreferenceService(),
    )
    app = FastAPI()
    app.include_router(create_strategy_preference_router(), prefix="/api/v1")
    client = TestClient(app)

    response = client.put(
        "/api/v1/strategy-preferences/profile",
        json={
            "template_id": "low_level_start",
            "preferred_themes": ["低位启动"],
            "holding_period_days": 12,
            "risk_style": "steady",
            "buy_style": "low_absorb",
            "avoid_risks": ["高位追强"],
            "accept_high_position": False,
            "prefer_expectation_gap": True,
            "prefer_leader_or_core": True,
            "note": "优先低吸。",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["template_id"] == "low_level_start"
