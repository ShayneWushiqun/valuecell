from __future__ import annotations

import datetime as dt
from collections import Counter, defaultdict
from typing import Any, Optional

from ...db.repositories.decision_outcome_review_repository import (
    DecisionOutcomeReviewRepository,
)
from .decision_record_service import DecisionRecordService

LOOKBACK_DAYS = 40
MAX_REVIEW_ITEMS = 160
MAX_RECORD_ITEMS = 220
RECENT_ITEM_LIMIT = 4
ACTION_ORDER = (
    "继续持有",
    "持有观察",
    "减仓观察",
    "保护利润",
    "纪律止损",
)
ROLE_ORDER = ("龙头", "中军", "跟风", "其他")
STATUS_SCORE_MAP = {
    "有效": 88,
    "部分有效": 66,
    "失效": 28,
    "仍在观察": 46,
    "数据不足": 42,
}


def _parse_iso_date(value: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return None


def _clean_theme_name(value: str | None) -> str | None:
    text = str(value or "").strip()
    if not text or text in {"-", "--", "无", "未知"}:
        return None
    return text


def _normalize_role(value: str | None) -> str:
    text = str(value or "").strip()
    if text in {"龙头", "中军", "跟风"}:
        return text
    return "其他"


def _sort_reviews(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: (
            str(item.get("review_date") or ""),
            int(item.get("outcome_score") or 0),
            str(item.get("ticker") or ""),
        ),
        reverse=True,
    )


class DecisionEffectivenessService:
    def __init__(
        self,
        decision_outcome_review_repository: Optional[DecisionOutcomeReviewRepository] = None,
        decision_record_service: Optional[DecisionRecordService] = None,
    ) -> None:
        self.decision_outcome_review_repository = (
            decision_outcome_review_repository or DecisionOutcomeReviewRepository()
        )
        self.decision_record_service = decision_record_service or DecisionRecordService()

    def get_summary(self, *, user_id: str) -> dict[str, Any]:
        raw_reviews = self.decision_outcome_review_repository.list_reviews(
            user_id=user_id,
            limit=MAX_REVIEW_ITEMS,
        )
        review_items = [item.to_dict() for item in raw_reviews]
        filtered_reviews = self._filter_recent_reviews(review_items)
        if not filtered_reviews:
            return {
                "generated_at": dt.datetime.now(dt.UTC).isoformat(),
                "available": False,
                "empty_message": "最近 40 天暂无可用结果回看，先保持轻量观察。",
                "overall_summary": "最近缺少足够回看样本，暂不外推判断有效性。",
                "overall_score": 0,
                "review_count": 0,
                "effective_count": 0,
                "partially_effective_count": 0,
                "failed_count": 0,
                "observing_count": 0,
                "insufficient_count": 0,
                "action_breakdown": [],
                "role_breakdown": [],
                "theme_breakdown": [],
                "recent_successes": [],
                "recent_failures": [],
            }

        record_map = self._load_record_map(user_id=user_id)
        enriched_reviews = [
            self._enrich_review(item, record_map=record_map) for item in filtered_reviews
        ]
        counts = Counter(str(item.get("outcome_status") or "") for item in enriched_reviews)
        overall_score = self._build_overall_score(enriched_reviews)
        action_breakdown = self._build_action_breakdown(enriched_reviews)
        role_breakdown = self._build_role_breakdown(enriched_reviews)
        theme_breakdown = self._build_theme_breakdown(enriched_reviews)
        recent_successes = self._build_recent_items(
            [
                item
                for item in enriched_reviews
                if str(item.get("outcome_status") or "") == "有效"
            ]
        )
        recent_failures = self._build_recent_items(
            [
                item
                for item in enriched_reviews
                if str(item.get("outcome_status") or "") == "失效"
            ]
        )
        return {
            "generated_at": dt.datetime.now(dt.UTC).isoformat(),
            "available": True,
            "empty_message": None,
            "overall_summary": self._build_overall_summary(
                reviews=enriched_reviews,
                overall_score=overall_score,
                counts=counts,
                action_breakdown=action_breakdown,
                theme_breakdown=theme_breakdown,
            ),
            "overall_score": overall_score,
            "review_count": len(enriched_reviews),
            "effective_count": counts.get("有效", 0),
            "partially_effective_count": counts.get("部分有效", 0),
            "failed_count": counts.get("失效", 0),
            "observing_count": counts.get("仍在观察", 0),
            "insufficient_count": counts.get("数据不足", 0),
            "action_breakdown": action_breakdown,
            "role_breakdown": role_breakdown,
            "theme_breakdown": theme_breakdown,
            "recent_successes": recent_successes,
            "recent_failures": recent_failures,
        }

    def _filter_recent_reviews(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        cutoff = dt.date.today() - dt.timedelta(days=LOOKBACK_DAYS)
        filtered: list[dict[str, Any]] = []
        for item in items:
            parsed_date = _parse_iso_date(str(item.get("review_date") or ""))
            if parsed_date is None or parsed_date < cutoff:
                continue
            filtered.append(item)
        return _sort_reviews(filtered)

    def _load_record_map(self, *, user_id: str) -> dict[int, dict[str, Any]]:
        records = self.decision_record_service.list_records(
            user_id=user_id,
            limit=MAX_RECORD_ITEMS,
        ).get("items") or []
        return {
            int(item.get("record_id") or 0): item
            for item in records
            if int(item.get("record_id") or 0) > 0
        }

    @staticmethod
    def _enrich_review(
        item: dict[str, Any],
        *,
        record_map: dict[int, dict[str, Any]],
    ) -> dict[str, Any]:
        record = record_map.get(int(item.get("record_id") or 0), {})
        return {
            **item,
            "role_label": _normalize_role(record.get("role_label")),
            "theme_name": _clean_theme_name(record.get("theme_name")),
        }

    def _build_overall_score(self, reviews: list[dict[str, Any]]) -> int:
        if not reviews:
            return 0
        total_score = 0
        for item in reviews:
            status = str(item.get("outcome_status") or "")
            fallback = STATUS_SCORE_MAP.get(status, 45)
            total_score += int(item.get("outcome_score") or fallback or 0) if status in {
                "有效",
                "部分有效",
                "失效",
            } else fallback
        return max(0, min(100, round(total_score / len(reviews))))

    def _build_action_breakdown(self, reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in reviews:
            grouped[str(item.get("action") or "")].append(item)
        result: list[dict[str, Any]] = []
        for action in ACTION_ORDER:
            items = grouped.get(action, [])
            result.append(self._build_breakdown_item(label=action, items=items))
        return result

    def _build_role_breakdown(self, reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in reviews:
            grouped[str(item.get("role_label") or "其他")].append(item)
        return [
            self._build_breakdown_item(label=role, items=grouped.get(role, []))
            for role in ROLE_ORDER
        ]

    def _build_theme_breakdown(self, reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in reviews:
            theme_name = _clean_theme_name(item.get("theme_name"))
            if theme_name:
                grouped[theme_name].append(item)
        sorted_items = sorted(
            grouped.items(),
            key=lambda entry: (
                -len(entry[1]),
                -self._average_score(entry[1]),
                entry[0],
            ),
        )
        return [
            self._build_breakdown_item(label=label, items=items)
            for label, items in sorted_items[:6]
        ]

    def _build_breakdown_item(
        self,
        *,
        label: str,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        counts = Counter(str(item.get("outcome_status") or "") for item in items)
        return {
            "label": label,
            "count": len(items),
            "effective_count": counts.get("有效", 0),
            "partially_effective_count": counts.get("部分有效", 0),
            "failed_count": counts.get("失效", 0),
            "observing_count": counts.get("仍在观察", 0),
            "insufficient_count": counts.get("数据不足", 0),
            "average_score": self._average_score(items),
        }

    def _average_score(self, items: list[dict[str, Any]]) -> int:
        if not items:
            return 0
        total = sum(int(item.get("outcome_score") or 0) for item in items)
        return round(total / len(items))

    def _build_recent_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for item in _sort_reviews(items)[:RECENT_ITEM_LIMIT]:
            result.append(
                {
                    "ticker": str(item.get("ticker") or ""),
                    "display_name": str(item.get("display_name") or item.get("ticker") or ""),
                    "action": str(item.get("action") or ""),
                    "outcome_status": str(item.get("outcome_status") or ""),
                    "summary": str(item.get("summary") or ""),
                    "review_date": str(item.get("review_date") or ""),
                }
            )
        return result

    def _build_overall_summary(
        self,
        *,
        reviews: list[dict[str, Any]],
        overall_score: int,
        counts: Counter[str],
        action_breakdown: list[dict[str, Any]],
        theme_breakdown: list[dict[str, Any]],
    ) -> str:
        review_count = len(reviews)
        validated_count = counts.get("有效", 0) + counts.get("部分有效", 0)
        best_action = self._pick_best_action(action_breakdown)
        weak_action = self._pick_weak_action(action_breakdown)
        theme_text = ""
        if theme_breakdown:
            theme_text = f"近期样本更多集中在 {theme_breakdown[0]['label']}。"
        if review_count < 4:
            return (
                f"最近 40 天仅有 {review_count} 条回看样本，当前更适合作为轻量观察，"
                f"整体得分 {overall_score}。{theme_text}".strip()
            )
        parts = [
            (
                f"最近 40 天共回看 {review_count} 条判断，其中 {validated_count} 条至少得到"
                "部分验证，整体得分 "
                f"{overall_score}。"
            )
        ]
        if best_action:
            parts.append(
                f"{best_action['label']} 这类动作的稳定度相对更好，平均分 {best_action['average_score']}。"
            )
        if weak_action:
            parts.append(
                f"{weak_action['label']} 这类动作近期更容易出现失配，需要结合新时间窗再收紧节奏。"
            )
        if theme_text:
            parts.append(theme_text)
        return " ".join(parts[:4])

    @staticmethod
    def _pick_best_action(items: list[dict[str, Any]]) -> dict[str, Any] | None:
        candidates = [item for item in items if int(item.get("count") or 0) > 0]
        if not candidates:
            return None
        return max(
            candidates,
            key=lambda item: (
                int(item.get("effective_count") or 0) + int(item.get("partially_effective_count") or 0),
                int(item.get("average_score") or 0),
                -int(item.get("failed_count") or 0),
            ),
        )

    @staticmethod
    def _pick_weak_action(items: list[dict[str, Any]]) -> dict[str, Any] | None:
        candidates = [item for item in items if int(item.get("failed_count") or 0) > 0]
        if not candidates:
            return None
        return max(
            candidates,
            key=lambda item: (
                int(item.get("failed_count") or 0),
                -int(item.get("average_score") or 0),
                int(item.get("count") or 0),
            ),
        )


_decision_effectiveness_service: Optional[DecisionEffectivenessService] = None


def get_decision_effectiveness_service() -> DecisionEffectivenessService:
    global _decision_effectiveness_service
    if _decision_effectiveness_service is None:
        _decision_effectiveness_service = DecisionEffectivenessService()
    return _decision_effectiveness_service


def reset_decision_effectiveness_service() -> None:
    global _decision_effectiveness_service
    _decision_effectiveness_service = None
