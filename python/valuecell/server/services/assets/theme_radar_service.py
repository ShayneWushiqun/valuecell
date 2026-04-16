from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional

from .opportunity_pool_service import OpportunityPoolService
from .strategy_preference_service import StrategyPreferenceService
from .theme_candidate_service import ThemeCandidateService
from .watchlist_observation_service import WatchlistObservationService


class ThemeRadarService:
    def __init__(
        self,
        theme_candidate_service: Optional[ThemeCandidateService] = None,
        watchlist_observation_service: Optional[WatchlistObservationService] = None,
        opportunity_pool_service: Optional[OpportunityPoolService] = None,
        strategy_preference_service: Optional[StrategyPreferenceService] = None,
    ) -> None:
        self.theme_candidate_service = theme_candidate_service or ThemeCandidateService()
        self.watchlist_observation_service = (
            watchlist_observation_service or WatchlistObservationService()
        )
        self.opportunity_pool_service = opportunity_pool_service or OpportunityPoolService()
        self.strategy_preference_service = (
            strategy_preference_service or StrategyPreferenceService()
        )

    def get_overview(self, user_id: str = 'default_user') -> dict[str, Any]:
        theme_result = self.theme_candidate_service.get_theme_candidates(top_n=16)
        theme_items = (
            list((theme_result.get('data') or {}).get('items') or [])
            if theme_result.get('success')
            else []
        )
        watchlist_result = self.watchlist_observation_service.get_watchlist_observation(
            user_id,
            theme_items,
        )
        opportunity_result = self.opportunity_pool_service.get_opportunity_candidates(user_id)
        strategy_profile = self.strategy_preference_service.get_effective_profile(user_id)
        preferred_themes = [
            str(theme or '').strip()
            for theme in strategy_profile.get('preferred_themes') or []
            if str(theme or '').strip()
        ]

        watchlist_counts = self._count_by_theme_name(
            list(watchlist_result.get('all_items') or []),
            field_name='theme_name',
        )
        opportunity_counts = self._count_by_theme_name(
            list(opportunity_result.get('items') or []),
            field_name='topic_name',
        )
        items = [
            self._build_theme_item(
                item=item,
                preferred_themes=preferred_themes,
                watchlist_resonance_count=watchlist_counts.get(
                    str(item.get('theme_name') or ''),
                    0,
                ),
                opportunity_resonance_count=opportunity_counts.get(
                    str(item.get('theme_name') or ''),
                    0,
                ),
            )
            for item in theme_items
        ]

        available = bool(items)
        return {
            'generated_at': datetime.now(UTC).isoformat(),
            'available': available,
            'empty_message': None if available else '暂无可用题材雷达摘要。',
            'summary': self._build_summary(items),
            'items': items,
            'grouped': self._build_grouped(items),
        }

    @staticmethod
    def _count_by_theme_name(
        items: list[dict[str, Any]],
        *,
        field_name: str,
    ) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in items:
            theme_name = str(item.get(field_name) or '').strip()
            if not theme_name:
                continue
            counts[theme_name] = counts.get(theme_name, 0) + 1
        return counts

    def _build_theme_item(
        self,
        *,
        item: dict[str, Any],
        preferred_themes: list[str],
        watchlist_resonance_count: int,
        opportunity_resonance_count: int,
    ) -> dict[str, Any]:
        theme_name = str(item.get('theme_name') or '')
        has_preference_match = any(
            preferred and preferred in theme_name for preferred in preferred_themes
        )
        risk_tags = self._build_risk_tags(
            theme_state=str(item.get('theme_state') or ''),
            preferred_market=str(item.get('preferred_market') or ''),
            participation_hint=str(item.get('participation_hint') or ''),
            watchlist_resonance_count=watchlist_resonance_count,
            opportunity_resonance_count=opportunity_resonance_count,
        )
        return {
            'theme_code': item.get('theme_code'),
            'theme_name': theme_name,
            'theme_state': item.get('theme_state'),
            'rank': int(item.get('rank') or 0),
            'score': int((item.get('metrics') or {}).get('score') or 0),
            'hot_level': int(item.get('hot_level') or 0),
            'preferred_market': item.get('preferred_market'),
            'participation_hint': item.get('participation_hint'),
            'etf_hint': item.get('etf_hint'),
            'primary_representative': item.get('primary_representative'),
            'representative_tickers': list(item.get('representative_tickers') or []),
            'core_leaders_json': list(item.get('core_leaders_json') or []),
            'metrics': dict(item.get('metrics') or {}),
            'watchlist_resonance_count': watchlist_resonance_count,
            'opportunity_resonance_count': opportunity_resonance_count,
            'has_preference_match': has_preference_match,
            'risk_tags': risk_tags,
            'observation_summary': self._build_observation_summary(
                item=item,
                has_preference_match=has_preference_match,
                watchlist_resonance_count=watchlist_resonance_count,
                opportunity_resonance_count=opportunity_resonance_count,
                risk_tags=risk_tags,
            ),
        }

    @staticmethod
    def _build_risk_tags(
        *,
        theme_state: str,
        preferred_market: str,
        participation_hint: str,
        watchlist_resonance_count: int,
        opportunity_resonance_count: int,
    ) -> list[str]:
        tags: list[str] = []
        if '不建议参与' in participation_hint:
            tags.append('不建议参与')
        if theme_state == '退潮':
            tags.append('当前偏防守')
        elif theme_state == '分歧':
            tags.append('分歧加大')
        if preferred_market in {'创业板为主', '科创板为主'}:
            tags.append('波动较高')
        if watchlist_resonance_count == 0 and opportunity_resonance_count == 0:
            tags.append('共振不足')
        return ThemeRadarService._unique_list(tags)

    @staticmethod
    def _build_observation_summary(
        *,
        item: dict[str, Any],
        has_preference_match: bool,
        watchlist_resonance_count: int,
        opportunity_resonance_count: int,
        risk_tags: list[str],
    ) -> str:
        theme_name = str(item.get('theme_name') or '当前题材')
        theme_state = str(item.get('theme_state') or '分歧')
        if '不建议参与' in risk_tags:
            return f'{theme_name} 涉及高风险方向，当前不建议参与，更适合仅做风险观察。'
        if theme_state == '加强':
            return (
                f'{theme_name} 当前继续加强，观察池共振 {watchlist_resonance_count} 只，'
                f'机会池联动 {opportunity_resonance_count} 只，优先跟踪核心票。'
            )
        if theme_state == '活跃':
            preference_text = '，且命中当前偏好' if has_preference_match else ''
            return f'{theme_name} 当前维持活跃{preference_text}，值得继续跟踪参与边界。'
        if theme_state == '退潮':
            return f'{theme_name} 当前偏退潮，更适合观察修复，而不是提升动作强度。'
        return f'{theme_name} 当前分歧较大，先看核心票是否继续稳定，再决定跟踪优先级。'

    @staticmethod
    def _build_summary(items: list[dict[str, Any]]) -> dict[str, int]:
        strengthen_count = len(
            [item for item in items if str(item.get('theme_state') or '') == '加强']
        )
        active_count = len(
            [item for item in items if str(item.get('theme_state') or '') == '活跃']
        )
        split_count = len(
            [item for item in items if str(item.get('theme_state') or '') == '分歧']
        )
        fading_count = len(
            [item for item in items if str(item.get('theme_state') or '') == '退潮']
        )
        preferred_theme_hit_count = len(
            [item for item in items if bool(item.get('has_preference_match'))]
        )
        watchlist_resonance_count = len(
            [item for item in items if int(item.get('watchlist_resonance_count') or 0) > 0]
        )
        opportunity_resonance_count = len(
            [item for item in items if int(item.get('opportunity_resonance_count') or 0) > 0]
        )
        return {
            'active_theme_count': active_count,
            'strengthen_count': strengthen_count,
            'split_count': split_count,
            'fading_count': fading_count,
            'preferred_theme_hit_count': preferred_theme_hit_count,
            'watchlist_resonance_count': watchlist_resonance_count,
            'opportunity_resonance_count': opportunity_resonance_count,
        }

    @staticmethod
    def _build_grouped(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        return {
            'strengthen_items': [
                item for item in items if str(item.get('theme_state') or '') == '加强'
            ],
            'active_items': [
                item for item in items if str(item.get('theme_state') or '') == '活跃'
            ],
            'split_items': [
                item for item in items if str(item.get('theme_state') or '') == '分歧'
            ],
            'fading_items': [
                item for item in items if str(item.get('theme_state') or '') == '退潮'
            ],
        }

    @staticmethod
    def _unique_list(values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            text = str(value or '').strip()
            if text and text not in seen:
                seen.add(text)
                result.append(text)
        return result


_theme_radar_service: Optional[ThemeRadarService] = None


def get_theme_radar_service() -> ThemeRadarService:
    global _theme_radar_service
    if _theme_radar_service is None:
        _theme_radar_service = ThemeRadarService()
    return _theme_radar_service


def reset_theme_radar_service() -> None:
    global _theme_radar_service
    _theme_radar_service = None
