from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional

from .asset_service import AssetService
from .strategy_preference_service import StrategyPreferenceService
from .theme_candidate_service import ThemeCandidateService
from .watchlist_observation_service import WatchlistObservationService


class OpportunityPoolService:
    def __init__(
        self,
        theme_candidate_service: Optional[ThemeCandidateService] = None,
        watchlist_observation_service: Optional[WatchlistObservationService] = None,
        asset_service: Optional[AssetService] = None,
        strategy_preference_service: Optional[StrategyPreferenceService] = None,
    ) -> None:
        self.theme_candidate_service = theme_candidate_service or ThemeCandidateService()
        self.watchlist_observation_service = (
            watchlist_observation_service or WatchlistObservationService()
        )
        self.asset_service = asset_service or AssetService()
        self.strategy_preference_service = (
            strategy_preference_service or StrategyPreferenceService()
        )

    def get_opportunity_candidates(self, user_id: str = "default_user") -> dict[str, Any]:
        theme_result = self.theme_candidate_service.get_theme_candidates(top_n=12)
        theme_items = (
            list((theme_result.get("data") or {}).get("items") or [])
            if theme_result.get("success")
            else []
        )
        watchlist_result = self.watchlist_observation_service.get_watchlist_observation(
            user_id,
            theme_items,
        )
        watchlist_items = list(watchlist_result.get("all_items") or [])
        strategy_profile = self.strategy_preference_service.get_effective_profile(user_id)

        candidates_by_ticker: dict[str, dict[str, Any]] = {}
        theme_refs = self._build_theme_refs(theme_items)

        for item in watchlist_items:
            ticker = str(item.get("ticker") or "").strip()
            if not ticker:
                continue
            theme_ref = self._pick_theme_ref(
                ticker=ticker,
                watchlist_theme_name=item.get("theme_name"),
                theme_refs=theme_refs,
            )
            source_tags = ["watchlist"]
            if theme_ref:
                source_tags.extend(theme_ref["matched_source_tags"])
                source_tags.append("theme_resonance")
            candidate = self._build_watchlist_candidate(
                item=item,
                theme_ref=theme_ref,
                source_tags=source_tags,
            )
            candidates_by_ticker[ticker] = candidate

        for ticker, theme_ref in theme_refs.items():
            if ticker in candidates_by_ticker:
                continue
            candidates_by_ticker[ticker] = self._build_theme_candidate_only(
                ticker=ticker,
                theme_ref=theme_ref,
            )

        items = [
            self._apply_strategy_preferences(item, strategy_profile)
            for item in candidates_by_ticker.values()
        ]

        items = sorted(
            items,
            key=lambda item: (
                -int(item.get("priority_score") or 0),
                self._source_priority_rank(list(item.get("source_tags") or [])),
                self._candidate_state_rank(str(item.get("candidate_state") or "")),
                str(item.get("ticker") or ""),
            ),
        )
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "available": bool(items),
            "items": items,
            "count": len(items),
            "empty_message": None if items else "暂无可用机会池候选",
            "source_summary": {
                "watchlist_count": len(watchlist_items),
                "theme_candidate_count": len(theme_items),
                "candidate_count": len(items),
                "preference_profile_applied": strategy_profile.get("template_id"),
            },
        }

    def _build_theme_refs(self, theme_items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        refs: dict[str, dict[str, Any]] = {}
        for item in theme_items:
            representative_tickers = list(item.get("representative_tickers") or [])
            if not representative_tickers:
                representative_tickers = list(item.get("representative_tickers_json") or [])
            core_leaders = list(item.get("core_leaders_json") or [])
            primary_representative = str(item.get("primary_representative") or "").strip()

            for ticker in core_leaders:
                self._merge_theme_ref(
                    refs,
                    ticker=str(ticker),
                    theme_item=item,
                    source_tag="theme_core",
                )
            for ticker in representative_tickers:
                self._merge_theme_ref(
                    refs,
                    ticker=str(ticker),
                    theme_item=item,
                    source_tag="theme_representative",
                )
            if primary_representative:
                self._merge_theme_ref(
                    refs,
                    ticker=primary_representative,
                    theme_item=item,
                    source_tag="theme_representative",
                )
        return refs

    @staticmethod
    def _merge_theme_ref(
        refs: dict[str, dict[str, Any]],
        *,
        ticker: str,
        theme_item: dict[str, Any],
        source_tag: str,
    ) -> None:
        normalized_ticker = ticker.strip()
        if not normalized_ticker:
            return
        current = refs.get(normalized_ticker)
        if current is None or int(theme_item.get("rank", 999) or 999) < int(
            current["theme_item"].get("rank", 999) or 999
        ):
            refs[normalized_ticker] = {
                "theme_item": theme_item,
                "source_tags": [source_tag],
            }
            return
        if source_tag not in current["source_tags"]:
            current["source_tags"].append(source_tag)

    @staticmethod
    def _pick_theme_ref(
        *,
        ticker: str,
        watchlist_theme_name: str | None,
        theme_refs: dict[str, dict[str, Any]],
    ) -> dict[str, Any] | None:
        direct_ref = theme_refs.get(ticker)
        if direct_ref is not None:
            return {
                "theme_item": direct_ref["theme_item"],
                "matched_source_tags": list(direct_ref["source_tags"]),
            }
        if not watchlist_theme_name:
            return None
        for ref in theme_refs.values():
            if str(ref["theme_item"].get("theme_name") or "") == str(watchlist_theme_name or ""):
                return {
                    "theme_item": ref["theme_item"],
                    "matched_source_tags": [],
                }
        return None

    def _build_watchlist_candidate(
        self,
        *,
        item: dict[str, Any],
        theme_ref: dict[str, Any] | None,
        source_tags: list[str],
    ) -> dict[str, Any]:
        theme_item = theme_ref["theme_item"] if theme_ref else {}
        role_label = str(item.get("role_label") or "跟风")
        trend_quality = str(item.get("trend_quality") or "震荡")
        tradeability_state = str(item.get("tradeability_state") or "可观察")
        expectation_gap_level = str(item.get("expectation_gap_level") or "中")

        reasons = [str(item.get("reason") or "来自自选观察列表")]
        if theme_item:
            reasons.append(
                f"与 {theme_item.get('theme_name')} 方向共振，当前题材状态为 {theme_item.get('theme_state')}。"
            )

        missing_confirmations = self._build_missing_confirmations(
            theme_item=theme_item,
            tradeability_state=tradeability_state,
            expectation_gap_level=expectation_gap_level,
            has_theme_resonance=bool(theme_item),
        )
        invalid_conditions = self._build_invalid_conditions(
            theme_item=theme_item,
            tradeability_state=tradeability_state,
            trend_quality=trend_quality,
        )
        expectation_gap_score = self._resolve_expectation_gap_score(expectation_gap_level)
        continuity_score = self._resolve_continuity_score(
            theme_item=theme_item,
            trend_quality=trend_quality,
        )
        priority_score = self._resolve_priority_score(
            source_tags=source_tags,
            role_label=role_label,
            tradeability_state=tradeability_state,
            expectation_gap_score=expectation_gap_score,
            continuity_score=continuity_score,
            theme_item=theme_item,
            trend_quality=trend_quality,
            invalid_conditions=invalid_conditions,
        )
        candidate_state = self._resolve_candidate_state(
            priority_score=priority_score,
            status=str(item.get("status") or "普通观察"),
            tradeability_state=tradeability_state,
            invalid_conditions=invalid_conditions,
        )
        return {
            "ticker": item.get("ticker"),
            "display_name": item.get("display_name"),
            "latest_price": item.get("price"),
            "change_percent": item.get("change_percent"),
            "topic_name": theme_item.get("theme_name") or item.get("theme_name"),
            "candidate_state": candidate_state,
            "priority_score": priority_score,
            "expectation_gap_level": expectation_gap_level,
            "expectation_gap_score": expectation_gap_score,
            "continuity_score": continuity_score,
            "tradeability_state": tradeability_state,
            "role_label": role_label,
            "trend_quality": trend_quality,
            "ranking_bucket": self._resolve_ranking_bucket(priority_score),
            "reasons": reasons,
            "time_horizon": "1-2周" if theme_item else "1-4周",
            "source_tags": self._unique_list(source_tags),
            "action_hint": self._resolve_action_hint(candidate_state, tradeability_state),
            "missing_confirmations": missing_confirmations,
            "invalid_conditions": invalid_conditions,
        }

    def _build_theme_candidate_only(
        self,
        *,
        ticker: str,
        theme_ref: dict[str, Any],
    ) -> dict[str, Any]:
        theme_item = theme_ref["theme_item"]
        price_result = self.asset_service.get_asset_price(ticker, language="zh-CN")
        info_result = self.asset_service.get_asset_info(ticker, language="zh-CN")
        display_name = (
            info_result.get("display_name")
            if info_result.get("success")
            else ticker
        )
        raw_change_percent = price_result.get("change_percent") if price_result.get("success") else None
        price_change_percent = (
            float(raw_change_percent)
            if raw_change_percent is not None
            else None
        )
        tradeability_state = self._resolve_theme_tradeability_state(
            theme_item,
            change_percent=price_change_percent,
        )
        role_label = self._resolve_theme_role_label(
            ticker=ticker,
            theme_item=theme_item,
        )
        trend_quality = self._resolve_theme_trend_quality(theme_item)
        expectation_gap_level = str(theme_item.get("expectation_gap_level") or "中")
        reasons = [
            f"{theme_item.get('theme_name')} 方向的核心候选，当前题材状态为 {theme_item.get('theme_state')}。"
        ]
        if price_result.get("success") and price_result.get("change_percent") is not None:
            reasons.append(
                f"日内涨跌幅 {float(price_result.get('change_percent') or 0):+.2f}%，需结合可交易性判断是否参与。"
            )
        missing_confirmations = self._build_missing_confirmations(
            theme_item=theme_item,
            tradeability_state=tradeability_state,
            expectation_gap_level=expectation_gap_level,
            has_theme_resonance=True,
        )
        invalid_conditions = self._build_invalid_conditions(
            theme_item=theme_item,
            tradeability_state=tradeability_state,
            trend_quality=trend_quality,
        )
        expectation_gap_score = self._resolve_expectation_gap_score(expectation_gap_level)
        continuity_score = self._resolve_continuity_score(
            theme_item=theme_item,
            trend_quality=trend_quality,
        )
        priority_score = self._resolve_priority_score(
            source_tags=theme_ref["source_tags"],
            role_label=role_label,
            tradeability_state=tradeability_state,
            expectation_gap_score=expectation_gap_score,
            continuity_score=continuity_score,
            theme_item=theme_item,
            trend_quality=trend_quality,
            invalid_conditions=invalid_conditions,
        )
        candidate_state = self._resolve_candidate_state(
            priority_score=priority_score,
            status="普通观察",
            tradeability_state=tradeability_state,
            invalid_conditions=invalid_conditions,
        )
        return {
            "ticker": ticker,
            "display_name": display_name,
            "latest_price": price_result.get("price_formatted")
            if price_result.get("success")
            else None,
            "change_percent": price_change_percent,
            "topic_name": theme_item.get("theme_name"),
            "candidate_state": candidate_state,
            "priority_score": priority_score,
            "expectation_gap_level": expectation_gap_level,
            "expectation_gap_score": expectation_gap_score,
            "continuity_score": continuity_score,
            "tradeability_state": tradeability_state,
            "role_label": role_label,
            "trend_quality": trend_quality,
            "ranking_bucket": self._resolve_ranking_bucket(priority_score),
            "reasons": reasons,
            "time_horizon": "1-2周",
            "source_tags": self._unique_list(theme_ref["source_tags"]),
            "action_hint": self._resolve_action_hint(candidate_state, tradeability_state),
            "missing_confirmations": missing_confirmations,
            "invalid_conditions": invalid_conditions,
        }

    @staticmethod
    def _resolve_expectation_gap_score(expectation_gap_level: str) -> int:
        mapping = {
            "高": 78,
            "中": 58,
            "低": 35,
        }
        return mapping.get(expectation_gap_level, 50)

    def _resolve_continuity_score(
        self,
        *,
        theme_item: dict[str, Any],
        trend_quality: str,
    ) -> int:
        score = 40
        theme_state = str(theme_item.get("theme_state") or "")
        if theme_state == "加强":
            score += 24
        elif theme_state == "活跃":
            score += 16
        elif theme_state in {"分歧", "观察"}:
            score += 6
        else:
            score -= 12

        hot_level = int(theme_item.get("hot_level") or 0)
        score += min(hot_level, 6) * 3

        if trend_quality == "顺势":
            score += 10
        elif trend_quality == "走弱":
            score -= 12

        return max(0, min(100, score))

    def _resolve_priority_score(
        self,
        *,
        source_tags: list[str],
        role_label: str,
        tradeability_state: str,
        expectation_gap_score: int,
        continuity_score: int,
        theme_item: dict[str, Any],
        trend_quality: str,
        invalid_conditions: list[str],
    ) -> int:
        score = 22.0
        if "theme_resonance" in source_tags:
            score += 28
        elif "watchlist" in source_tags:
            score += 12

        if "theme_core" in source_tags:
            score += 16
        if "theme_representative" in source_tags:
            score += 10

        score += expectation_gap_score * 0.18
        score += continuity_score * 0.22

        if role_label == "龙头":
            score += 10
        elif role_label == "中军":
            score += 8
        elif role_label == "跟风":
            score -= 6

        if tradeability_state == "可低吸":
            score += 10
        elif tradeability_state == "可观察":
            score += 5
        elif tradeability_state == "谨慎追高":
            score -= 18
        elif tradeability_state == "流动性风险":
            score -= 24

        if trend_quality == "顺势":
            score += 8
        elif trend_quality == "走弱":
            score -= 10

        if str(theme_item.get("theme_state") or "") == "退潮":
            score -= 18

        if invalid_conditions:
            score -= 25

        return max(0, min(100, int(round(score))))

    def _apply_strategy_preferences(
        self,
        item: dict[str, Any],
        profile: dict[str, Any],
    ) -> dict[str, Any]:
        adjustments: list[dict[str, Any]] = []
        matched_preferences: list[str] = []
        topic_name = str(item.get("topic_name") or "")
        tradeability_state = str(item.get("tradeability_state") or "")
        role_label = str(item.get("role_label") or "")
        trend_quality = str(item.get("trend_quality") or "")
        expectation_gap_level = str(item.get("expectation_gap_level") or "")
        source_tags = list(item.get("source_tags") or [])
        invalid_conditions = " ".join(item.get("invalid_conditions") or [])
        change_percent = item.get("change_percent")
        delta = 0

        preferred_themes = [str(theme or "").strip() for theme in profile.get("preferred_themes") or []]
        if topic_name and any(theme and theme in topic_name for theme in preferred_themes):
            adjustments.append({"label": "偏好题材命中", "delta": 8})
            matched_preferences.append(f"偏好题材命中：{topic_name}")
            delta += 8

        if "watchlist" in source_tags and "theme_resonance" in source_tags:
            adjustments.append({"label": "自选与主线共振", "delta": 6})
            matched_preferences.append("自选与主线共振")
            delta += 6

        if profile.get("prefer_leader_or_core"):
            if role_label == "龙头":
                adjustments.append({"label": "偏好龙头", "delta": 8})
                matched_preferences.append("偏好龙头/核心")
                delta += 8
            elif role_label == "中军":
                adjustments.append({"label": "偏好中军", "delta": 6})
                matched_preferences.append("偏好龙头/核心")
                delta += 6
            elif role_label == "跟风":
                adjustments.append({"label": "跟风降权", "delta": -8})
                delta -= 8
            if "theme_core" in source_tags:
                adjustments.append({"label": "核心票加权", "delta": 4})
                delta += 4
            elif "theme_representative" in source_tags:
                adjustments.append({"label": "代表票加权", "delta": 2})
                delta += 2

        if profile.get("prefer_expectation_gap"):
            if expectation_gap_level == "高":
                adjustments.append({"label": "偏好高预期差", "delta": 6})
                matched_preferences.append("偏好预期差")
                delta += 6
            elif expectation_gap_level == "中":
                adjustments.append({"label": "偏好中预期差", "delta": 3})
                matched_preferences.append("偏好预期差")
                delta += 3
            elif expectation_gap_level == "低":
                adjustments.append({"label": "低预期差降权", "delta": -8})
                delta -= 8

        risk_style = str(profile.get("risk_style") or "balanced")
        if risk_style == "steady":
            if tradeability_state == "谨慎追高":
                adjustments.append({"label": "稳健风格回避追高", "delta": -12})
                matched_preferences.append("稳健风格")
                delta -= 12
            if tradeability_state == "流动性风险":
                adjustments.append({"label": "稳健风格回避流动性风险", "delta": -18})
                matched_preferences.append("稳健风格")
                delta -= 18
            if trend_quality == "走弱" or "回避" in invalid_conditions:
                adjustments.append({"label": "稳健风格回避走弱/高风险", "delta": -10})
                delta -= 10

        if not profile.get("accept_high_position", False):
            if tradeability_state == "谨慎追高":
                adjustments.append({"label": "不接受高位追强", "delta": -10})
                matched_preferences.append("不接受高位追强")
                delta -= 10
            if change_percent is not None and float(change_percent) >= 6:
                adjustments.append({"label": "高位涨幅降权", "delta": -6})
                delta -= 6

        buy_style = str(profile.get("buy_style") or "right_side")
        if buy_style in {"low_absorb", "pullback"}:
            if tradeability_state == "可低吸":
                adjustments.append({"label": "偏好低吸/回踩", "delta": 8})
                matched_preferences.append("偏好低吸/回踩")
                delta += 8
            if tradeability_state == "谨慎追高":
                adjustments.append({"label": "低吸风格回避追高", "delta": -8})
                delta -= 8
        elif buy_style in {"breakout", "right_side"} and trend_quality == "顺势":
            adjustments.append({"label": "偏好右侧/突破", "delta": 4})
            matched_preferences.append("偏好右侧/突破")
            delta += 4

        avoid_risks = [str(risk or "").strip() for risk in profile.get("avoid_risks") or []]
        combined_risk_text = " ".join(
            [
                topic_name,
                tradeability_state,
                invalid_conditions,
                " ".join(item.get("reasons") or []),
            ]
        )
        for risk in avoid_risks:
            if risk and risk in combined_risk_text:
                adjustments.append({"label": f"规避风险：{risk}", "delta": -6})
                matched_preferences.append(f"规避风险：{risk}")
                delta -= 6

        updated_score = max(0, min(100, int(item.get("priority_score") or 0) + delta))
        updated_item = {
            **item,
            "priority_score": updated_score,
            "ranking_bucket": self._resolve_ranking_bucket(updated_score),
            "candidate_state": self._resolve_candidate_state(
                priority_score=updated_score,
                status=str(item.get("candidate_state") or "普通观察"),
                tradeability_state=tradeability_state,
                invalid_conditions=list(item.get("invalid_conditions") or []),
            ),
            "preference_adjustments": adjustments,
            "matched_preferences": self._unique_list(matched_preferences),
        }
        if matched_preferences:
            updated_item["reasons"] = self._unique_list(
                [*list(item.get("reasons") or []), "更符合当前偏好，但仍需确认。"]
            )
        return updated_item

    @staticmethod
    def _resolve_candidate_state(
        *,
        priority_score: int,
        status: str,
        tradeability_state: str,
        invalid_conditions: list[str],
    ) -> str:
        if invalid_conditions:
            return "暂不参与"
        if tradeability_state == "谨慎追高":
            return "仅适合持有"
        if tradeability_state == "流动性风险":
            return "暂不参与"
        if priority_score >= 82:
            return "高优先级买点"
        if priority_score >= 68:
            return "候选买点"
        if status == "重点观察":
            return "重点观察"
        return "普通观察"

    def _build_missing_confirmations(
        self,
        *,
        theme_item: dict[str, Any],
        tradeability_state: str,
        expectation_gap_level: str,
        has_theme_resonance: bool,
    ) -> list[str]:
        missing: list[str] = []
        if not has_theme_resonance:
            missing.append("缺少与主线题材的明确共振确认。")
        if expectation_gap_level == "低":
            missing.append("预期差偏低，需等待更好的风险收益比。")
        if tradeability_state in {"可观察", "谨慎追高"}:
            missing.append("仍需等待更明确的承接或回踩确认。")
        preferred_market = str(theme_item.get("preferred_market") or "")
        if preferred_market in {"创业板为主", "科创板为主"}:
            missing.append("需确认风险承受能力与板块波动容忍度。")
        return self._unique_list(missing)

    def _build_invalid_conditions(
        self,
        *,
        theme_item: dict[str, Any],
        tradeability_state: str,
        trend_quality: str,
    ) -> list[str]:
        invalid: list[str] = []
        participation_hint = str(theme_item.get("participation_hint") or "")
        theme_state = str(theme_item.get("theme_state") or "")
        if "不建议参与" in participation_hint:
            invalid.append("疑似 ST 或高风险方向，默认回避。")
        if tradeability_state == "流动性风险":
            invalid.append("流动性风险偏高，不满足候选要求。")
        if tradeability_state == "谨慎追高":
            invalid.append("短线涨幅过大，当前不宜追高。")
        if theme_state == "退潮" or trend_quality == "走弱":
            invalid.append("题材或个股处于走弱阶段，需等待修复。")
        return self._unique_list(invalid)

    @staticmethod
    def _resolve_ranking_bucket(priority_score: int) -> str:
        if priority_score >= 80:
            return "A"
        if priority_score >= 65:
            return "B"
        return "C"

    @staticmethod
    def _resolve_action_hint(candidate_state: str, tradeability_state: str) -> str:
        if candidate_state == "高优先级买点":
            return "可以继续跟踪低吸或分批参与，不使用绝对化买点表达。"
        if candidate_state == "候选买点":
            return "保持重点跟踪，等待承接、回踩或量价确认后再行动。"
        if candidate_state == "仅适合持有":
            return "方向本身可跟踪，但当前位置更适合持有观察，不宜追高。"
        if tradeability_state == "流动性风险":
            return "优先回避流动性风险，等待更好的退出条件。"
        return "先观察，不急于参与，等待更明确的确认信号。"

    @staticmethod
    def _resolve_theme_tradeability_state(
        theme_item: dict[str, Any],
        *,
        change_percent: float | None,
    ) -> str:
        if change_percent is not None:
            if change_percent >= 8:
                return "谨慎追高"
            if change_percent <= -8:
                return "流动性风险"
            if -2 <= change_percent <= 2:
                return "可低吸"
            return "可观察"
        change_value = float(theme_item.get("metrics", {}).get("change_value", 0) or 0)
        if change_value >= 6:
            return "谨慎追高"
        if change_value <= -6:
            return "流动性风险"
        if -2 <= change_value <= 2:
            return "可低吸"
        return "可观察"

    @staticmethod
    def _resolve_theme_role_label(*, ticker: str, theme_item: dict[str, Any]) -> str:
        leaders = list(theme_item.get("core_leaders_json") or [])
        if ticker in leaders:
            return "龙头"
        if ticker.startswith("SSE:60") or ticker.startswith("SZSE:00"):
            return "中军"
        return "跟风"

    @staticmethod
    def _resolve_theme_trend_quality(theme_item: dict[str, Any]) -> str:
        change_value = float(theme_item.get("metrics", {}).get("change_value", 0) or 0)
        if change_value >= 2:
            return "顺势"
        if change_value <= -3:
            return "走弱"
        return "震荡"

    @staticmethod
    def _candidate_state_rank(candidate_state: str) -> int:
        ranking = {
            "高优先级买点": 0,
            "候选买点": 1,
            "重点观察": 2,
            "普通观察": 3,
            "仅适合持有": 4,
            "暂不参与": 5,
        }
        return ranking.get(candidate_state, 9)

    @staticmethod
    def _source_priority_rank(source_tags: list[str]) -> int:
        if "theme_resonance" in source_tags:
            return 0
        if "theme_core" in source_tags or "theme_representative" in source_tags:
            return 1
        if "watchlist" in source_tags:
            return 2
        return 3

    @staticmethod
    def _unique_list(values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            text = str(value or "").strip()
            if text and text not in seen:
                seen.add(text)
                result.append(text)
        return result


_opportunity_pool_service: Optional[OpportunityPoolService] = None


def get_opportunity_pool_service() -> OpportunityPoolService:
    global _opportunity_pool_service
    if _opportunity_pool_service is None:
        _opportunity_pool_service = OpportunityPoolService()
    return _opportunity_pool_service


def reset_opportunity_pool_service() -> None:
    global _opportunity_pool_service
    _opportunity_pool_service = None
