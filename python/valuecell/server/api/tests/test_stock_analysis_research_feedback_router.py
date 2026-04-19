from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.stock_analysis_research_feedback import (
    create_stock_analysis_research_feedback_router,
)


class FakeResearchFeedbackService:
    async def list_feedbacks(self, *, user_id: str, thread_id: int):
        del user_id
        return {
            "thread_id": thread_id,
            "items": [
                {
                    "feedback_id": 1,
                    "thread_id": thread_id,
                    "user_id": "default_user",
                    "anchor_message_id": "msg_assistant_1",
                    "title": "中际旭创 研究反馈",
                    "anchor_question_intent": "compare_targets",
                    "anchor_response_strategy": "refresh_then_answer",
                    "anchor_mode": "need_tooling",
                    "anchor_plan_summary": "先 refresh 再 compare",
                    "anchor_validation_status": "thesis_recheck_needed",
                    "linked_task_ids_json": [1],
                    "linked_context_ids_json": [2],
                    "linked_memory_id": 3,
                    "linked_compression_id": 4,
                    "linked_compare_targets_json": [],
                    "linked_tickers_json": ["SZSE:300308"],
                    "linked_themes_json": ["AI算力"],
                    "linked_outcome_review_ids_json": [11],
                    "linked_effectiveness_snapshot_json": {
                        "available": True,
                        "overall_score": 70,
                    },
                    "linked_risk_sizing_snapshot_json": {
                        "available": True,
                        "market_risk_level": "中性",
                    },
                    "outcome_alignment_status": "partially_confirmed",
                    "process_quality_status": "mixed",
                    "compare_helpful": True,
                    "refresh_helpful": True,
                    "tooling_helpful": False,
                    "validation_helpful": True,
                    "what_helped_json": ["对比对象较明确。"],
                    "what_hurt_json": ["仍需继续跟踪。"],
                    "process_adjustments_json": ["下次先 refresh 再 compare。"],
                    "task_followup_suggestions_json": [
                        {
                            "task_id": 1,
                            "title": "继续跟踪主线确认",
                            "current_status": "open",
                            "suggestion": "keep_tracking",
                            "reason": "还需继续跟踪。",
                        }
                    ],
                    "summary": "结果回看偏 partially_confirmed。",
                    "detail_note": "刷新后重新回看。",
                    "version": 1,
                    "created_at": "2026-04-19T10:00:00Z",
                    "updated_at": "2026-04-19T10:00:00Z",
                }
            ],
            "latest_feedback": {
                "feedback_id": 1,
                "thread_id": thread_id,
                "user_id": "default_user",
                "anchor_message_id": "msg_assistant_1",
                "title": "中际旭创 研究反馈",
                "anchor_question_intent": "compare_targets",
                "anchor_response_strategy": "refresh_then_answer",
                "anchor_mode": "need_tooling",
                "anchor_plan_summary": "先 refresh 再 compare",
                "anchor_validation_status": "thesis_recheck_needed",
                "linked_task_ids_json": [1],
                "linked_context_ids_json": [2],
                "linked_memory_id": 3,
                "linked_compression_id": 4,
                "linked_compare_targets_json": [],
                "linked_tickers_json": ["SZSE:300308"],
                "linked_themes_json": ["AI算力"],
                "linked_outcome_review_ids_json": [11],
                "linked_effectiveness_snapshot_json": {
                    "available": True,
                    "overall_score": 70,
                },
                "linked_risk_sizing_snapshot_json": {
                    "available": True,
                    "market_risk_level": "中性",
                },
                "outcome_alignment_status": "partially_confirmed",
                "process_quality_status": "mixed",
                "compare_helpful": True,
                "refresh_helpful": True,
                "tooling_helpful": False,
                "validation_helpful": True,
                "what_helped_json": ["对比对象较明确。"],
                "what_hurt_json": ["仍需继续跟踪。"],
                "process_adjustments_json": ["下次先 refresh 再 compare。"],
                "task_followup_suggestions_json": [],
                "summary": "结果回看偏 partially_confirmed。",
                "detail_note": "刷新后重新回看。",
                "version": 1,
                "created_at": "2026-04-19T10:00:00Z",
                "updated_at": "2026-04-19T10:00:00Z",
            },
            "count": 1,
            "generated_at": "2026-04-19T10:00:00Z",
        }

    async def get_feedback(self, *, user_id: str, thread_id: int, feedback_id: int):
        del user_id
        data = await self.list_feedbacks(user_id="default_user", thread_id=thread_id)
        return {**data["items"][0], "feedback_id": feedback_id}

    async def capture_feedback(self, *, user_id: str, thread_id: int, **kwargs):
        del user_id, kwargs
        return await self.get_feedback(
            user_id="default_user",
            thread_id=thread_id,
            feedback_id=2,
        )

    async def refresh_feedback(
        self,
        *,
        user_id: str,
        thread_id: int,
        feedback_id: int,
        **kwargs,
    ):
        del user_id, kwargs
        data = await self.get_feedback(
            user_id="default_user",
            thread_id=thread_id,
            feedback_id=feedback_id + 1,
        )
        data["version"] = 2
        return data


def test_stock_analysis_research_feedback_router_handles_crud_actions(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.stock_analysis_research_feedback.get_stock_analysis_research_feedback_service",
        lambda: FakeResearchFeedbackService(),
    )
    app = FastAPI()
    app.include_router(create_stock_analysis_research_feedback_router(), prefix="/api/v1")
    client = TestClient(app)

    assert client.get("/api/v1/stock-analysis/threads/1/research-feedback").status_code == 200
    assert (
        client.get("/api/v1/stock-analysis/threads/1/research-feedback/1").status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/stock-analysis/threads/1/research-feedback/capture",
            json={"anchor_message_id": "msg_assistant_1"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/stock-analysis/threads/1/research-feedback/1/refresh",
            json={"note": "refresh"},
        ).status_code
        == 200
    )
