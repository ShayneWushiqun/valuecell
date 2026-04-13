from __future__ import annotations

import json
from typing import Any

from valuecell.server.services.assets.strategy_preference_service import (
    STRATEGY_PREFERENCE_KIND,
    StrategyPreferenceService,
)


class FakeUserProfileService:
    def __init__(self, profiles: list[dict[str, Any]] | None = None) -> None:
        self.profiles = profiles or []
        self.created_payloads: list[dict[str, Any]] = []
        self.updated_payloads: list[dict[str, Any]] = []

    def get_user_profiles(self, user_id: str, category: str | None = None) -> list[dict[str, Any]]:
        return list(self.profiles)

    def create_profile(self, user_id: str, category: str, content: str) -> dict[str, Any]:
        payload = {
            "id": 101,
            "user_id": user_id,
            "category": category,
            "content": content,
        }
        self.created_payloads.append(payload)
        self.profiles.insert(0, payload)
        return payload

    def update_profile(self, profile_id: int, user_id: str, content: str) -> dict[str, Any]:
        payload = {
            "id": profile_id,
            "user_id": user_id,
            "category": "normal",
            "content": content,
        }
        self.updated_payloads.append(payload)
        self.profiles = [payload if int(p.get("id", 0)) == profile_id else p for p in self.profiles]
        return payload


def test_strategy_preference_service_returns_default_profile_when_missing() -> None:
    service = StrategyPreferenceService(user_profile_service=FakeUserProfileService())

    result = service.get_effective_profile("default_user")

    assert result["template_id"] == "trend_continuation"
    assert result["risk_style"] == "balanced"
    assert result["profile_id"] is None


def test_strategy_preference_service_skips_invalid_json_and_falls_back_to_default() -> None:
    service = StrategyPreferenceService(
        user_profile_service=FakeUserProfileService(
            profiles=[
                {
                    "id": 1,
                    "content": "{bad-json",
                    "category": "normal",
                }
            ]
        )
    )

    result = service.get_effective_profile("default_user")

    assert result["template_id"] == "trend_continuation"
    assert result["profile_id"] is None


def test_strategy_preference_service_updates_existing_profile() -> None:
    content = json.dumps(
        {
            "kind": STRATEGY_PREFERENCE_KIND,
            "schema_version": 1,
            "profile": {
                "template_id": "event_driven",
                "preferred_themes": ["业绩预告"],
                "holding_period_days": 5,
                "risk_style": "balanced",
                "buy_style": "breakout",
                "avoid_risks": ["ST"],
                "accept_high_position": False,
                "prefer_expectation_gap": True,
                "prefer_leader_or_core": True,
                "note": "",
            },
        },
        ensure_ascii=False,
    )
    fake_user_profile_service = FakeUserProfileService(
        profiles=[{"id": 7, "content": content, "category": "normal"}]
    )
    service = StrategyPreferenceService(user_profile_service=fake_user_profile_service)

    result = service.save_profile(
        "default_user",
        {
            "template_id": "low_level_start",
            "preferred_themes": ["低位启动"],
            "holding_period_days": 12,
            "risk_style": "steady",
            "buy_style": "low_absorb",
            "avoid_risks": ["高位追强"],
            "accept_high_position": False,
            "prefer_expectation_gap": True,
            "prefer_leader_or_core": True,
            "note": "优先做低位启动。",
        },
    )

    assert result["profile_id"] == 7
    assert result["template_id"] == "low_level_start"
    assert fake_user_profile_service.updated_payloads


def test_strategy_preference_service_normalizes_bad_holding_period_and_text_inputs() -> None:
    service = StrategyPreferenceService(user_profile_service=FakeUserProfileService())

    result = service.save_profile(
        "default_user",
        {
            "template_id": "trend_continuation",
            "preferred_themes": "AI算力, 机器人，证券",
            "holding_period_days": "bad-value",
            "risk_style": "balanced",
            "buy_style": "right_side",
            "avoid_risks": "ST, 流动性风险",
            "accept_high_position": "false",
            "prefer_expectation_gap": "true",
            "prefer_leader_or_core": "false",
            "note": "",
        },
    )

    assert result["holding_period_days"] == 10
    assert result["preferred_themes"] == ["AI算力", "机器人", "证券"]
    assert result["avoid_risks"] == ["ST", "流动性风险"]
    assert result["accept_high_position"] is False
    assert result["prefer_expectation_gap"] is True
    assert result["prefer_leader_or_core"] is False


def test_strategy_preference_service_handles_empty_or_invalid_values_defensively() -> None:
    service = StrategyPreferenceService(user_profile_service=FakeUserProfileService())

    result = service.save_profile(
        "default_user",
        {
            "template_id": "event_driven",
            "preferred_themes": 123,
            "holding_period_days": None,
            "risk_style": "balanced",
            "buy_style": "breakout",
            "avoid_risks": {"ST", "流动性风险"},
            "accept_high_position": "",
            "prefer_expectation_gap": "false",
            "prefer_leader_or_core": None,
            "note": "",
        },
    )

    assert result["holding_period_days"] == 5
    assert result["preferred_themes"] == ["业绩预告", "并购重组", "产品发布"]
    assert sorted(result["avoid_risks"]) == ["ST", "流动性风险"]
    assert result["accept_high_position"] is False
    assert result["prefer_expectation_gap"] is False
    assert result["prefer_leader_or_core"] is True
