from __future__ import annotations

import json
from typing import Any, Optional

from loguru import logger

from ...db.models.user_profile import ProfileCategory
from ..user_profile_service import UserProfileService

STRATEGY_PREFERENCE_KIND = "ashare_strategy_preference"
STRATEGY_PREFERENCE_SCHEMA_VERSION = 1


class StrategyPreferenceService:
    def __init__(
        self,
        user_profile_service: Optional[UserProfileService] = None,
    ) -> None:
        self.user_profile_service = user_profile_service or UserProfileService()

    def get_templates(self) -> dict[str, Any]:
        templates = [self._build_template_data(template) for template in self._templates()]
        return {
            "items": templates,
            "count": len(templates),
        }

    def get_effective_profile(self, user_id: str = "default_user") -> dict[str, Any]:
        stored_profile = self._find_existing_profile(user_id)
        if stored_profile is None:
            return self._build_effective_profile(
                profile_id=None,
                profile=self._default_profile(),
            )
        return self._build_effective_profile(
            profile_id=stored_profile["id"],
            profile=stored_profile["profile"],
        )

    def save_profile(
        self,
        user_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        normalized_profile = self._normalize_profile(payload)
        content = json.dumps(
            {
                "kind": STRATEGY_PREFERENCE_KIND,
                "schema_version": STRATEGY_PREFERENCE_SCHEMA_VERSION,
                "profile": normalized_profile,
            },
            ensure_ascii=False,
        )
        existing_profile = self._find_existing_profile(user_id)
        if existing_profile is None:
            created = self.user_profile_service.create_profile(
                user_id=user_id,
                category=ProfileCategory.NORMAL.value,
                content=content,
            )
            profile_id = created.get("id") if created else None
            return self._build_effective_profile(
                profile_id=profile_id,
                profile=normalized_profile,
            )

        updated = self.user_profile_service.update_profile(
            profile_id=int(existing_profile["id"]),
            user_id=user_id,
            content=content,
        )
        profile_id = updated.get("id") if updated else existing_profile["id"]
        return self._build_effective_profile(
            profile_id=profile_id,
            profile=normalized_profile,
        )

    def _find_existing_profile(self, user_id: str) -> dict[str, Any] | None:
        profiles = self.user_profile_service.get_user_profiles(
            user_id,
            category=ProfileCategory.NORMAL.value,
        )
        for profile in profiles:
            parsed = self._parse_profile_content(profile)
            if parsed is None:
                continue
            return {
                "id": profile.get("id"),
                "profile": parsed,
            }
        return None

    def _parse_profile_content(self, profile: dict[str, Any]) -> dict[str, Any] | None:
        content = profile.get("content")
        if not content:
            return None
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            logger.warning(
                "Invalid strategy preference JSON profile_id={profile_id}, fallback to default",
                profile_id=profile.get("id"),
            )
            return None
        if payload.get("kind") != STRATEGY_PREFERENCE_KIND:
            return None
        profile_payload = payload.get("profile")
        if not isinstance(profile_payload, dict):
            logger.warning(
                "Malformed strategy preference payload profile_id={profile_id}, fallback to default",
                profile_id=profile.get("id"),
            )
            return None
        return self._normalize_profile(profile_payload)

    def _build_effective_profile(
        self,
        *,
        profile_id: int | None,
        profile: dict[str, Any],
    ) -> dict[str, Any]:
        normalized_profile = self._normalize_profile(profile)
        template = self._template_map().get(normalized_profile["template_id"])
        return {
            "profile_id": profile_id,
            "kind": STRATEGY_PREFERENCE_KIND,
            "schema_version": STRATEGY_PREFERENCE_SCHEMA_VERSION,
            **normalized_profile,
            "template_title": template["title"] if template else None,
        }

    def _normalize_profile(self, payload: dict[str, Any]) -> dict[str, Any]:
        template_id = str(payload.get("template_id") or self._default_template_id())
        template_map = self._template_map()
        if template_id not in template_map:
            template_id = self._default_template_id()
        base_profile = template_map[template_id]["profile"]
        preferred_themes = self._normalize_text_list(
            payload.get("preferred_themes"),
            default=list(base_profile["preferred_themes"]),
        )
        avoid_risks = self._normalize_text_list(
            payload.get("avoid_risks"),
            default=list(base_profile["avoid_risks"]),
        )
        holding_period_days = self._normalize_holding_period_days(
            payload.get("holding_period_days"),
            default=int(base_profile["holding_period_days"]),
        )
        risk_style = str(payload.get("risk_style") or base_profile["risk_style"])
        buy_style = str(payload.get("buy_style") or base_profile["buy_style"])
        note = str(payload.get("note") or "").strip()
        return {
            "template_id": template_id,
            "preferred_themes": preferred_themes,
            "holding_period_days": max(1, min(60, holding_period_days)),
            "risk_style": risk_style
            if risk_style in {"steady", "balanced", "aggressive"}
            else base_profile["risk_style"],
            "buy_style": buy_style
            if buy_style in {"pullback", "breakout", "low_absorb", "right_side"}
            else base_profile["buy_style"],
            "avoid_risks": avoid_risks,
            "accept_high_position": self._normalize_bool(
                payload.get("accept_high_position"),
                default=bool(base_profile["accept_high_position"]),
            ),
            "prefer_expectation_gap": self._normalize_bool(
                payload.get("prefer_expectation_gap"),
                default=bool(base_profile["prefer_expectation_gap"]),
            ),
            "prefer_leader_or_core": self._normalize_bool(
                payload.get("prefer_leader_or_core"),
                default=bool(base_profile["prefer_leader_or_core"]),
            ),
            "note": note,
        }

    @staticmethod
    def _normalize_holding_period_days(value: Any, *, default: int) -> int:
        if value in (None, ""):
            return default
        try:
            parsed_value = int(value)
        except (TypeError, ValueError):
            return default
        return max(1, min(60, parsed_value))

    @staticmethod
    def _normalize_text_list(value: Any, *, default: list[str]) -> list[str]:
        if value is None:
            source_values: list[Any] = list(default)
        elif isinstance(value, str):
            normalized = value.replace("，", ",")
            source_values = [part.strip() for part in normalized.split(",")]
        elif isinstance(value, (list, tuple, set)):
            source_values = list(value)
        else:
            source_values = list(default)

        return [
            str(item).strip()
            for item in source_values
            if str(item).strip()
        ]

    @staticmethod
    def _normalize_bool(value: Any, *, default: bool) -> bool:
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "y", "on"}:
                return True
            if normalized in {"false", "0", "no", "n", "off", ""}:
                return False
            return default
        if isinstance(value, (int, float)):
            return bool(value)
        return default

    def _default_profile(self) -> dict[str, Any]:
        return self._template_map()[self._default_template_id()]["profile"].copy()

    @staticmethod
    def _default_template_id() -> str:
        return "trend_continuation"

    def _build_template_data(self, template: dict[str, Any]) -> dict[str, Any]:
        return {
            "template_id": template["template_id"],
            "title": template["title"],
            "summary": template["summary"],
            **template["profile"],
        }

    def _template_map(self) -> dict[str, dict[str, Any]]:
        return {
            template["template_id"]: template
            for template in self._templates()
        }

    @staticmethod
    def _templates() -> list[dict[str, Any]]:
        return [
            {
                "template_id": "policy_catalyst",
                "title": "政策催化",
                "summary": "更关注政策方向共振与核心受益题材，强调确认后的右侧参与。",
                "profile": {
                    "template_id": "policy_catalyst",
                    "preferred_themes": ["国企改革", "自主可控", "新质生产力"],
                    "holding_period_days": 8,
                    "risk_style": "balanced",
                    "buy_style": "right_side",
                    "avoid_risks": ["ST", "流动性风险", "退潮题材"],
                    "accept_high_position": False,
                    "prefer_expectation_gap": True,
                    "prefer_leader_or_core": True,
                    "note": "",
                },
            },
            {
                "template_id": "event_driven",
                "title": "事件驱动",
                "summary": "围绕事件催化后的强弱切换做观察，强调快速确认与纪律回避。",
                "profile": {
                    "template_id": "event_driven",
                    "preferred_themes": ["业绩预告", "并购重组", "产品发布"],
                    "holding_period_days": 5,
                    "risk_style": "balanced",
                    "buy_style": "breakout",
                    "avoid_risks": ["ST", "流动性风险"],
                    "accept_high_position": False,
                    "prefer_expectation_gap": True,
                    "prefer_leader_or_core": True,
                    "note": "",
                },
            },
            {
                "template_id": "trend_continuation",
                "title": "趋势延续",
                "summary": "优先延续性和核心票强趋势，适合当前阶段默认模板。",
                "profile": {
                    "template_id": "trend_continuation",
                    "preferred_themes": ["AI算力", "机器人", "证券"],
                    "holding_period_days": 10,
                    "risk_style": "balanced",
                    "buy_style": "right_side",
                    "avoid_risks": ["ST", "流动性风险", "退潮题材"],
                    "accept_high_position": False,
                    "prefer_expectation_gap": True,
                    "prefer_leader_or_core": True,
                    "note": "",
                },
            },
            {
                "template_id": "secondary_strength_after_pullback",
                "title": "回调后二次走强",
                "summary": "更重视回踩承接与二次走强确认，偏好低风险收益比窗口。",
                "profile": {
                    "template_id": "secondary_strength_after_pullback",
                    "preferred_themes": ["主线修复", "分歧转一致"],
                    "holding_period_days": 7,
                    "risk_style": "steady",
                    "buy_style": "pullback",
                    "avoid_risks": ["ST", "流动性风险", "追高"],
                    "accept_high_position": False,
                    "prefer_expectation_gap": True,
                    "prefer_leader_or_core": True,
                    "note": "",
                },
            },
            {
                "template_id": "low_level_start",
                "title": "低位启动",
                "summary": "更偏好预期差和低位启动，强调低吸与核心辨识度。",
                "profile": {
                    "template_id": "low_level_start",
                    "preferred_themes": ["低位启动", "补涨切换"],
                    "holding_period_days": 12,
                    "risk_style": "steady",
                    "buy_style": "low_absorb",
                    "avoid_risks": ["ST", "流动性风险", "高位追强"],
                    "accept_high_position": False,
                    "prefer_expectation_gap": True,
                    "prefer_leader_or_core": True,
                    "note": "",
                },
            },
        ]


_strategy_preference_service: Optional[StrategyPreferenceService] = None


def get_strategy_preference_service() -> StrategyPreferenceService:
    global _strategy_preference_service
    if _strategy_preference_service is None:
        _strategy_preference_service = StrategyPreferenceService()
    return _strategy_preference_service


def reset_strategy_preference_service() -> None:
    global _strategy_preference_service
    _strategy_preference_service = None
