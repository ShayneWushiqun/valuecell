from __future__ import annotations

from typing import Any, cast

from valuecell.server.services.assets.theme_radar_service import ThemeRadarService


class FakeThemeCandidateService:
    def get_theme_candidates(self, top_n: int = 12) -> dict[str, Any]:
        return {
            'success': True,
            'data': {
                'items': [
                    {
                        'theme_code': 'AI',
                        'theme_name': 'AI算力',
                        'theme_state': '加强',
                        'rank': 1,
                        'hot_level': 8,
                        'preferred_market': '主板为主',
                        'participation_hint': '可优先围绕主板核心票观察承接，再决定是否参与。',
                        'etf_hint': None,
                        'primary_representative': 'SZSE:300308',
                        'representative_tickers': ['SZSE:300308'],
                        'core_leaders_json': ['SZSE:300308'],
                        'metrics': {'score': 86, 'change_value': 3.2},
                    },
                    {
                        'theme_code': 'ROBOT',
                        'theme_name': '机器人',
                        'theme_state': '活跃',
                        'rank': 2,
                        'hot_level': 6,
                        'preferred_market': '创业板为主',
                        'participation_hint': '方向有热度，但不建议无差别追高，优先低吸或等待更好位置。',
                        'etf_hint': {'title': 'ETF', 'summary': 'hint', 'risk_hint': 'risk'},
                        'primary_representative': 'SZSE:300024',
                        'representative_tickers': ['SZSE:300024'],
                        'core_leaders_json': ['SZSE:300024'],
                        'metrics': {'score': 74, 'change_value': 1.6},
                    },
                    {
                        'theme_code': 'ST',
                        'theme_name': 'ST重整',
                        'theme_state': '退潮',
                        'rank': 3,
                        'hot_level': 2,
                        'preferred_market': '主板为主',
                        'participation_hint': '疑似 ST 或高风险方向，默认回避，不建议参与。',
                        'etf_hint': None,
                        'primary_representative': 'SZSE:000001',
                        'representative_tickers': ['SZSE:000001'],
                        'core_leaders_json': ['SZSE:000001'],
                        'metrics': {'score': 35, 'change_value': -2.4},
                    },
                ]
            },
        }


class FakeWatchlistObservationService:
    def get_watchlist_observation(
        self,
        user_id: str,
        theme_items: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return {
            'available': True,
            'items': [],
            'all_items': [
                {'ticker': 'SZSE:300308', 'theme_name': 'AI算力'},
                {'ticker': 'SZSE:300024', 'theme_name': '机器人'},
            ],
            'empty_message': None,
        }


class FakeOpportunityPoolService:
    def get_opportunity_candidates(self, user_id: str = 'default_user') -> dict[str, Any]:
        return {
            'available': True,
            'items': [
                {'ticker': 'SZSE:300308', 'topic_name': 'AI算力'},
                {'ticker': 'SZSE:300024', 'topic_name': '机器人'},
            ],
        }


class FakeStrategyPreferenceService:
    def get_effective_profile(self, user_id: str) -> dict[str, Any]:
        return {'preferred_themes': ['AI']}


def test_theme_radar_service_builds_resonance_and_preference_summary() -> None:
    service = ThemeRadarService(
        theme_candidate_service=cast(Any, FakeThemeCandidateService()),
        watchlist_observation_service=cast(Any, FakeWatchlistObservationService()),
        opportunity_pool_service=cast(Any, FakeOpportunityPoolService()),
        strategy_preference_service=cast(Any, FakeStrategyPreferenceService()),
    )

    result = service.get_overview('default_user')

    assert result['available'] is True
    assert result['summary']['strengthen_count'] == 1
    assert result['summary']['active_theme_count'] == 1
    assert result['summary']['preferred_theme_hit_count'] == 1
    assert result['summary']['watchlist_resonance_count'] == 2
    assert result['items'][0]['watchlist_resonance_count'] == 1
    assert result['items'][0]['opportunity_resonance_count'] == 1
    assert result['items'][0]['has_preference_match'] is True
    assert '不建议参与' in result['items'][2]['risk_tags']
