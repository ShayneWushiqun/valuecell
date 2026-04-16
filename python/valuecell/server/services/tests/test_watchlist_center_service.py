from __future__ import annotations

from typing import Any, cast

from valuecell.server.services.assets.watchlist_center_service import WatchlistCenterService


class FakeThemeCandidateService:
    def get_theme_candidates(self, top_n: int = 12) -> dict[str, Any]:
        return {
            'success': True,
            'data': {
                'items': [
                    {'theme_name': 'AI算力', 'core_leaders_json': ['SZSE:300308']},
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
                    'price': '120.00',
                    'change_percent': 2.5,
                },
                {
                    'ticker': 'SZSE:000001',
                    'display_name': '平安银行',
                    'watchlist_name': '默认观察池',
                    'theme_name': None,
                    'status': '常规跟踪',
                    'reason': '暂无更强共振。',
                    'tradeability_state': '可低吸',
                    'expectation_gap_level': '高',
                    'role_label': '跟风',
                    'trend_quality': '震荡',
                    'price': '10.20',
                    'change_percent': 0.3,
                },
            ],
            'empty_message': None,
        }


class FakeOpportunityPoolService:
    def get_opportunity_candidates(self, user_id: str = 'default_user') -> dict[str, Any]:
        return {
            'available': True,
            'items': [
                {
                    'ticker': 'SZSE:300308',
                    'candidate_state': '高优先级买点',
                }
            ],
        }


class FakeDecisionAlertPersistenceService:
    def list_alerts(
        self,
        *,
        user_id: str,
        status: str = 'all',
        alert_type: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        return {
            'generated_at': '2025-04-11T10:00:00Z',
            'unread_count': 1,
            'count': 1,
            'items': [{'ticker': 'SZSE:300308'}],
        }


class FakeHoldingService:
    def list_holdings(self, user_id: str) -> list[dict[str, Any]]:
        return [{'id': 1, 'ticker': 'SZSE:300308', 'asset_name': '中际旭创'}]


class FakeHoldingExitSignalService:
    def list_exit_signals(self, user_id: str = 'default_user') -> dict[str, Any]:
        return {
            'generated_at': '2025-04-11T10:00:00Z',
            'items': [
                {'holding_id': 1, 'ticker': 'SZSE:300308', 'action': '保护利润'}
            ],
            'count': 1,
        }


class FakeDecisionJudgeService:
    def judge(
        self,
        *,
        ticker: str,
        user_id: str = 'default_user',
        enable_agent: bool = False,
        force_refresh_context: bool = False,
        user_note: str | None = None,
    ) -> dict[str, Any]:
        return {'action': '接近可参与窗口' if ticker == 'SZSE:300308' else '继续观察'}


def test_watchlist_center_service_builds_linked_overview() -> None:
    service = WatchlistCenterService(
        theme_candidate_service=cast(Any, FakeThemeCandidateService()),
        watchlist_observation_service=cast(Any, FakeWatchlistObservationService()),
        opportunity_pool_service=cast(Any, FakeOpportunityPoolService()),
        decision_alert_persistence_service=cast(Any, FakeDecisionAlertPersistenceService()),
        holding_service=cast(Any, FakeHoldingService()),
        holding_exit_signal_service=cast(Any, FakeHoldingExitSignalService()),
        decision_judge_service=cast(Any, FakeDecisionJudgeService()),
    )

    result = service.get_overview('default_user')

    assert result['available'] is True
    assert result['summary']['total_count'] == 2
    assert result['summary']['focus_count'] == 1
    assert result['summary']['holding_linked_count'] == 1
    assert result['items'][0]['ticker'] == 'SZSE:300308'
    assert result['items'][0]['has_active_alert'] is True
    assert result['items'][0]['holding_action'] == '保护利润'
    assert result['items'][0]['linked_judge_action'] == '接近可参与窗口'
