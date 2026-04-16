from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional

from ..portfolio.holding_exit_signal_service import HoldingExitSignalService
from ..portfolio.holding_service import HoldingService
from .ashare_decision_judge_service import AShareDecisionJudgeService
from .decision_alert_persistence_service import DecisionAlertPersistenceService
from .opportunity_pool_service import OpportunityPoolService
from .theme_candidate_service import ThemeCandidateService
from .watchlist_observation_service import WatchlistObservationService


class WatchlistCenterService:
    def __init__(
        self,
        theme_candidate_service: Optional[ThemeCandidateService] = None,
        watchlist_observation_service: Optional[WatchlistObservationService] = None,
        opportunity_pool_service: Optional[OpportunityPoolService] = None,
        decision_alert_persistence_service: Optional[DecisionAlertPersistenceService] = None,
        holding_service: Optional[HoldingService] = None,
        holding_exit_signal_service: Optional[HoldingExitSignalService] = None,
        decision_judge_service: Optional[AShareDecisionJudgeService] = None,
    ) -> None:
        self.theme_candidate_service = theme_candidate_service or ThemeCandidateService()
        self.watchlist_observation_service = (
            watchlist_observation_service or WatchlistObservationService()
        )
        self.opportunity_pool_service = opportunity_pool_service or OpportunityPoolService()
        self.decision_alert_persistence_service = (
            decision_alert_persistence_service or DecisionAlertPersistenceService()
        )
        self.holding_service = holding_service or HoldingService()
        self.holding_exit_signal_service = (
            holding_exit_signal_service or HoldingExitSignalService()
        )
        self.decision_judge_service = decision_judge_service or AShareDecisionJudgeService()

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
        watchlist_items = list(watchlist_result.get('all_items') or [])
        opportunity_result = self.opportunity_pool_service.get_opportunity_candidates(user_id)
        alert_result = self.decision_alert_persistence_service.list_alerts(
            user_id=user_id,
            status='active',
            limit=200,
        )
        holdings = self.holding_service.list_holdings(user_id)
        exit_signals = self.holding_exit_signal_service.list_exit_signals(user_id)

        opportunity_by_ticker = {
            str(item.get('ticker') or ''): item
            for item in list(opportunity_result.get('items') or [])
            if str(item.get('ticker') or '')
        }
        active_alert_tickers = {
            str(item.get('ticker') or '')
            for item in list(alert_result.get('items') or [])
            if str(item.get('ticker') or '')
        }
        holding_by_ticker = {
            str(item.get('ticker') or ''): item for item in holdings if str(item.get('ticker') or '')
        }
        exit_signal_by_ticker = {
            str(item.get('ticker') or ''): item
            for item in list(exit_signals.get('items') or [])
            if str(item.get('ticker') or '')
        }
        judge_action_by_ticker = self._build_judge_action_by_ticker(
            user_id=user_id,
            tickers=[str(item.get('ticker') or '') for item in watchlist_items],
        )

        items = [
            self._build_watchlist_center_item(
                item=item,
                opportunity_by_ticker=opportunity_by_ticker,
                active_alert_tickers=active_alert_tickers,
                holding_by_ticker=holding_by_ticker,
                exit_signal_by_ticker=exit_signal_by_ticker,
                judge_action_by_ticker=judge_action_by_ticker,
            )
            for item in watchlist_items
        ]
        items.sort(key=self._sort_key)
        available = bool(items)
        return {
            'generated_at': datetime.now(UTC).isoformat(),
            'available': available,
            'empty_message': None if available else '暂无可用观察池中心数据。',
            'summary': self._build_summary(items),
            'items': items,
            'grouped': self._build_grouped(items),
        }

    def _build_judge_action_by_ticker(
        self,
        *,
        user_id: str,
        tickers: list[str],
    ) -> dict[str, str | None]:
        actions: dict[str, str | None] = {}
        for ticker in tickers:
            normalized_ticker = str(ticker or '').strip()
            if not normalized_ticker or normalized_ticker in actions:
                continue
            result = self.decision_judge_service.judge(
                ticker=normalized_ticker,
                user_id=user_id,
                enable_agent=False,
                force_refresh_context=False,
                user_note=None,
            )
            actions[normalized_ticker] = str(result.get('action') or '').strip() or None
        return actions

    def _build_watchlist_center_item(
        self,
        *,
        item: dict[str, Any],
        opportunity_by_ticker: dict[str, dict[str, Any]],
        active_alert_tickers: set[str],
        holding_by_ticker: dict[str, dict[str, Any]],
        exit_signal_by_ticker: dict[str, dict[str, Any]],
        judge_action_by_ticker: dict[str, str | None],
    ) -> dict[str, Any]:
        ticker = str(item.get('ticker') or '')
        linked_opportunity = opportunity_by_ticker.get(ticker) or {}
        linked_holding = holding_by_ticker.get(ticker) or {}
        linked_exit_signal = exit_signal_by_ticker.get(ticker) or {}
        has_theme_resonance = bool(item.get('theme_name'))
        has_opportunity_link = bool(linked_opportunity)
        has_active_alert = ticker in active_alert_tickers
        has_holding = bool(linked_holding)
        holding_action = str(linked_exit_signal.get('action') or '').strip() or None
        observation_priority = self._resolve_observation_priority(
            status=str(item.get('status') or ''),
            has_theme_resonance=has_theme_resonance,
            has_opportunity_link=has_opportunity_link,
            has_active_alert=has_active_alert,
            holding_action=holding_action,
        )
        linked_candidate_state = (
            str(linked_opportunity.get('candidate_state') or '').strip() or None
        )
        linked_judge_action = judge_action_by_ticker.get(ticker)
        return {
            'ticker': ticker,
            'display_name': item.get('display_name'),
            'watchlist_name': item.get('watchlist_name'),
            'theme_name': item.get('theme_name'),
            'status': item.get('status'),
            'reason': item.get('reason'),
            'tradeability_state': item.get('tradeability_state'),
            'expectation_gap_level': item.get('expectation_gap_level'),
            'role_label': item.get('role_label'),
            'trend_quality': item.get('trend_quality'),
            'latest_price': item.get('price'),
            'change_percent': item.get('change_percent'),
            'has_theme_resonance': has_theme_resonance,
            'has_opportunity_link': has_opportunity_link,
            'has_active_alert': has_active_alert,
            'has_holding': has_holding,
            'holding_action': holding_action,
            'linked_candidate_state': linked_candidate_state,
            'linked_judge_action': linked_judge_action,
            'observation_priority': observation_priority,
            'quick_note': self._build_quick_note(
                display_name=str(item.get('display_name') or ticker),
                has_theme_resonance=has_theme_resonance,
                has_opportunity_link=has_opportunity_link,
                has_active_alert=has_active_alert,
                has_holding=has_holding,
                holding_action=holding_action,
            ),
        }

    @staticmethod
    def _resolve_observation_priority(
        *,
        status: str,
        has_theme_resonance: bool,
        has_opportunity_link: bool,
        has_active_alert: bool,
        holding_action: str | None,
    ) -> str:
        score = 0
        if status == '重点观察':
            score += 4
        elif status in {'主题联动', '风险观察'}:
            score += 2
        if has_theme_resonance:
            score += 2
        if has_opportunity_link:
            score += 3
        if has_active_alert:
            score += 2
        if holding_action in {'纪律止损', '保护利润', '减仓观察'}:
            score += 3
        elif holding_action:
            score += 1
        if score >= 8:
            return '高'
        if score >= 4:
            return '中'
        return '低'

    @staticmethod
    def _build_quick_note(
        *,
        display_name: str,
        has_theme_resonance: bool,
        has_opportunity_link: bool,
        has_active_alert: bool,
        has_holding: bool,
        holding_action: str | None,
    ) -> str:
        if has_holding and holding_action:
            return f'{display_name} 已有关联持仓，先按{holding_action}节奏处理，不外推成新开仓语义。'
        if has_active_alert and has_opportunity_link:
            return f'{display_name} 已进入提醒与机会联动，观察优先级更高。'
        if has_theme_resonance and has_opportunity_link:
            return f'{display_name} 与主线题材共振，且已进入机会池，值得继续跟踪。'
        if has_theme_resonance:
            return f'{display_name} 与主线题材存在共振，适合放到重点观察列表。'
        return f'{display_name} 当前以常规观察为主，等待更明确联动信号。'

    @staticmethod
    def _sort_key(item: dict[str, Any]) -> tuple[int, int, int, float, str]:
        priority_rank = {'高': 0, '中': 1, '低': 2}
        return (
            priority_rank.get(str(item.get('observation_priority') or ''), 9),
            0 if bool(item.get('has_opportunity_link')) else 1,
            0 if bool(item.get('has_active_alert')) else 1,
            -abs(float(item.get('change_percent') or 0)),
            str(item.get('ticker') or ''),
        )

    @staticmethod
    def _build_summary(items: list[dict[str, Any]]) -> dict[str, int]:
        return {
            'total_count': len(items),
            'focus_count': len(
                [item for item in items if str(item.get('observation_priority') or '') == '高']
            ),
            'normal_count': len(
                [item for item in items if str(item.get('observation_priority') or '') == '低']
            ),
            'theme_resonance_count': len(
                [item for item in items if bool(item.get('has_theme_resonance'))]
            ),
            'opportunity_linked_count': len(
                [item for item in items if bool(item.get('has_opportunity_link'))]
            ),
            'active_alert_count': len(
                [item for item in items if bool(item.get('has_active_alert'))]
            ),
            'holding_linked_count': len(
                [item for item in items if bool(item.get('has_holding'))]
            ),
        }

    @staticmethod
    def _build_grouped(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        return {
            'focus_items': [
                item for item in items if str(item.get('observation_priority') or '') == '高'
            ],
            'resonance_items': [
                item
                for item in items
                if bool(item.get('has_theme_resonance')) or bool(item.get('has_opportunity_link'))
            ],
            'normal_items': [
                item for item in items if str(item.get('observation_priority') or '') == '低'
            ],
            'holding_linked_items': [
                item for item in items if bool(item.get('has_holding'))
            ],
        }


_watchlist_center_service: Optional[WatchlistCenterService] = None


def get_watchlist_center_service() -> WatchlistCenterService:
    global _watchlist_center_service
    if _watchlist_center_service is None:
        _watchlist_center_service = WatchlistCenterService()
    return _watchlist_center_service


def reset_watchlist_center_service() -> None:
    global _watchlist_center_service
    _watchlist_center_service = None
