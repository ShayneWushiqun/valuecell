from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.watchlist_center import create_watchlist_center_router


class FakeWatchlistCenterService:
    def get_overview(self, user_id: str = 'default_user'):
        return {
            'generated_at': '2025-04-11T10:08:00Z',
            'available': True,
            'empty_message': None,
            'summary': {
                'total_count': 1,
                'focus_count': 1,
                'normal_count': 0,
                'theme_resonance_count': 1,
                'opportunity_linked_count': 1,
                'active_alert_count': 1,
                'holding_linked_count': 1,
            },
            'items': [
                {
                    'ticker': 'SZSE:300308',
                    'display_name': '中际旭创',
                    'watchlist_name': '默认观察池',
                    'theme_name': 'AI算力',
                    'status': '重点观察',
                    'reason': '与主线共振。',
                    'tradeability_state': '可观察',
                    'expectation_gap_level': '中',
                    'role_label': '龙头',
                    'trend_quality': '顺势',
                    'latest_price': '120.00',
                    'change_percent': 2.5,
                    'has_theme_resonance': True,
                    'has_opportunity_link': True,
                    'has_active_alert': True,
                    'has_holding': True,
                    'holding_action': '保护利润',
                    'linked_candidate_state': '高优先级买点',
                    'linked_judge_action': '接近可参与窗口',
                    'observation_priority': '高',
                    'quick_note': '值得继续跟踪。',
                }
            ],
            'grouped': {
                'focus_items': [],
                'resonance_items': [],
                'normal_items': [],
                'holding_linked_items': [],
            },
        }


def test_watchlist_center_router_supports_overview(monkeypatch) -> None:
    monkeypatch.setattr(
        'valuecell.server.api.routers.watchlist_center.get_watchlist_center_service',
        lambda: FakeWatchlistCenterService(),
    )
    app = FastAPI()
    app.include_router(create_watchlist_center_router(), prefix='/api/v1')
    client = TestClient(app)

    response = client.get('/api/v1/watchlist-center/overview')

    assert response.status_code == 200
    assert response.json()['data']['summary']['total_count'] == 1
    assert response.json()['data']['items'][0]['ticker'] == 'SZSE:300308'
