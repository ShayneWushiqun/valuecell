from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.theme_radar import create_theme_radar_router


class FakeThemeRadarService:
    def get_overview(self, user_id: str = 'default_user'):
        return {
            'generated_at': '2025-04-11T10:05:00Z',
            'available': True,
            'empty_message': None,
            'summary': {
                'active_theme_count': 1,
                'strengthen_count': 1,
                'split_count': 0,
                'fading_count': 0,
                'preferred_theme_hit_count': 1,
                'watchlist_resonance_count': 1,
                'opportunity_resonance_count': 1,
            },
            'items': [
                {
                    'theme_code': 'AI',
                    'theme_name': 'AI算力',
                    'theme_state': '加强',
                    'rank': 1,
                    'score': 88,
                    'hot_level': 8,
                    'preferred_market': '主板为主',
                    'participation_hint': '优先跟踪核心票。',
                    'etf_hint': None,
                    'primary_representative': 'SZSE:300308',
                    'representative_tickers': ['SZSE:300308'],
                    'core_leaders_json': ['SZSE:300308'],
                    'metrics': {'score': 88},
                    'watchlist_resonance_count': 1,
                    'opportunity_resonance_count': 1,
                    'has_preference_match': True,
                    'risk_tags': [],
                    'observation_summary': '值得继续跟踪。',
                }
            ],
            'grouped': {
                'strengthen_items': [],
                'active_items': [],
                'split_items': [],
                'fading_items': [],
            },
        }


def test_theme_radar_router_supports_overview(monkeypatch) -> None:
    monkeypatch.setattr(
        'valuecell.server.api.routers.theme_radar.get_theme_radar_service',
        lambda: FakeThemeRadarService(),
    )
    app = FastAPI()
    app.include_router(create_theme_radar_router(), prefix='/api/v1')
    client = TestClient(app)

    response = client.get('/api/v1/theme-radar/overview')

    assert response.status_code == 200
    assert response.json()['data']['summary']['strengthen_count'] == 1
    assert response.json()['data']['items'][0]['theme_name'] == 'AI算力'
