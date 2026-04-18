from __future__ import annotations

import datetime as dt
from typing import Any, Optional, Sequence

from .stock_analysis_workspace_service import StockAnalysisWorkspaceService


class StockAnalysisRefreshService:
    def __init__(
        self,
        stock_analysis_workspace_service: Optional[StockAnalysisWorkspaceService] = None,
    ) -> None:
        self.stock_analysis_workspace_service = (
            stock_analysis_workspace_service or StockAnalysisWorkspaceService()
        )

    async def refresh_stale_contexts(
        self,
        *,
        user_id: str,
        thread_id: int,
        context_ids: Sequence[int] | None = None,
        include_supported_only: bool = True,
        pin_refreshed_cards: bool = False,
    ) -> dict[str, Any] | None:
        context_result = await self.stock_analysis_workspace_service.list_context_cards(
            user_id=user_id,
            thread_id=thread_id,
        )
        if context_result is None:
            return None
        generated_at = dt.datetime.now(dt.UTC).isoformat()
        all_items = list(context_result.get("items") or [])
        requested_ids = {int(item) for item in list(context_ids or []) if int(item) > 0}
        refresh_targets = self._select_refresh_targets(
            items=all_items,
            requested_ids=requested_ids,
        )
        items: list[dict[str, Any]] = []
        refreshed_context_ids: list[int] = []
        skipped_context_ids: list[int] = []
        failed_context_ids: list[int] = []
        changed_contexts: list[dict[str, Any]] = []

        for before in refresh_targets:
            context_id = int(before.get("context_id") or 0)
            refresh_supported = bool(before.get("refresh_supported"))
            if include_supported_only and not refresh_supported:
                items.append(
                    self._build_result_item(
                        before=before,
                        after=None,
                        status="skipped",
                        reason="该卡片当前不支持直接刷新。",
                        changed_fields=[],
                    )
                )
                skipped_context_ids.append(context_id)
                continue
            try:
                after = await self.stock_analysis_workspace_service.refresh_context_card(
                    user_id=user_id,
                    thread_id=thread_id,
                    context_id=context_id,
                )
                if after is None:
                    items.append(
                        self._build_result_item(
                            before=before,
                            after=None,
                            status="failed",
                            reason="未找到可刷新的上下文卡片。",
                            changed_fields=[],
                        )
                    )
                    failed_context_ids.append(context_id)
                    continue
                if pin_refreshed_cards and not bool(after.get("is_pinned")):
                    pinned = await self.stock_analysis_workspace_service.update_context_card(
                        user_id=user_id,
                        thread_id=thread_id,
                        context_id=context_id,
                        is_pinned=True,
                    )
                    if pinned is not None:
                        after = pinned
                changed_fields = self._detect_changed_fields(before=before, after=after)
                item = self._build_result_item(
                    before=before,
                    after=after,
                    status="refreshed",
                    reason="刷新成功" if changed_fields else "刷新成功，但无明显变化。",
                    changed_fields=changed_fields,
                )
                items.append(item)
                refreshed_context_ids.append(context_id)
                if changed_fields:
                    changed_contexts.append(
                        {
                            "context_id": context_id,
                            "title": str(after.get("title") or before.get("title") or ""),
                            "changed_fields": changed_fields,
                            "after_freshness_label": after.get("freshness_label"),
                        }
                    )
            except ValueError as exc:
                items.append(
                    self._build_result_item(
                        before=before,
                        after=None,
                        status="skipped",
                        reason=str(exc),
                        changed_fields=[],
                    )
                )
                skipped_context_ids.append(context_id)
            except Exception as exc:  # pragma: no cover - defensive
                items.append(
                    self._build_result_item(
                        before=before,
                        after=None,
                        status="failed",
                        reason=f"刷新时发生异常: {exc}",
                        changed_fields=[],
                    )
                )
                failed_context_ids.append(context_id)

        refreshed_count = len(refreshed_context_ids)
        skipped_count = len(skipped_context_ids)
        failed_count = len(failed_context_ids)
        changed_count = len(changed_contexts)
        scope_label = "所选上下文" if requested_ids else "建议更新的上下文"
        if not refresh_targets:
            summary = f"当前线程没有可刷新的 {scope_label}。"
        else:
            summary = (
                f"{scope_label}共 {len(refresh_targets)} 张，已刷新 {refreshed_count} 张，"
                f"其中 {changed_count} 张有变化，跳过 {skipped_count} 张，失败 {failed_count} 张。"
            )
        return {
            "thread_id": thread_id,
            "refreshed_count": refreshed_count,
            "skipped_count": skipped_count,
            "failed_count": failed_count,
            "items": items,
            "summary": summary,
            "generated_at": generated_at,
            "refreshed_context_ids": refreshed_context_ids,
            "skipped_context_ids": skipped_context_ids,
            "failed_context_ids": failed_context_ids,
            "changed_contexts": changed_contexts,
        }

    @staticmethod
    def _select_refresh_targets(
        *,
        items: Sequence[dict[str, Any]],
        requested_ids: set[int],
    ) -> list[dict[str, Any]]:
        if requested_ids:
            return [
                item
                for item in items
                if int(item.get("context_id") or 0) in requested_ids
            ]
        return [
            item
            for item in items
            if bool(item.get("refresh_recommended")) or bool(item.get("is_stale"))
        ]

    @staticmethod
    def _detect_changed_fields(
        *,
        before: dict[str, Any],
        after: dict[str, Any],
    ) -> list[str]:
        changed_fields: list[str] = []
        if before.get("freshness_label") != after.get("freshness_label"):
            changed_fields.append("freshness_label")
        if str(before.get("generated_at") or "") != str(after.get("generated_at") or ""):
            changed_fields.append("generated_at")
        if str(before.get("data_time") or "") != str(after.get("data_time") or ""):
            changed_fields.append("data_time")
        if str(before.get("summary") or "") != str(after.get("summary") or ""):
            changed_fields.append("summary")
        before_refs = (
            list(before.get("ticker_refs_json") or []),
            list(before.get("theme_refs_json") or []),
        )
        after_refs = (
            list(after.get("ticker_refs_json") or []),
            list(after.get("theme_refs_json") or []),
        )
        if before_refs != after_refs:
            changed_fields.append("refs")
        return changed_fields

    @staticmethod
    def _build_result_item(
        *,
        before: dict[str, Any],
        after: dict[str, Any] | None,
        status: str,
        reason: str,
        changed_fields: Sequence[str],
    ) -> dict[str, Any]:
        target = after or before
        return {
            "context_id": int(before.get("context_id") or 0),
            "title": str(target.get("title") or before.get("title") or ""),
            "source_module": str(
                target.get("source_module") or before.get("source_module") or ""
            ),
            "refresh_supported": bool(before.get("refresh_supported")),
            "status": status,
            "reason": reason,
            "before_freshness_label": before.get("freshness_label"),
            "after_freshness_label": target.get("freshness_label") if after else None,
            "changed_fields": list(changed_fields),
            "new_generated_at": target.get("generated_at") if after else None,
            "new_data_time": target.get("data_time") if after else None,
        }


_stock_analysis_refresh_service: StockAnalysisRefreshService | None = None


def get_stock_analysis_refresh_service() -> StockAnalysisRefreshService:
    global _stock_analysis_refresh_service
    if _stock_analysis_refresh_service is None:
        _stock_analysis_refresh_service = StockAnalysisRefreshService()
    return _stock_analysis_refresh_service


def reset_stock_analysis_refresh_service() -> None:
    global _stock_analysis_refresh_service
    _stock_analysis_refresh_service = None
