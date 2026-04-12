from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from valuecell.server.api.routers.opportunity_pool import create_opportunity_pool_router


class FakeOpportunityPoolService:
    def get_opportunity_candidates(self, user_id: str = "default_user"):
        return {
            "generated_at": "2025-04-10T09:30:00Z",
            "available": True,
            "items": [
                {
                    "ticker": "SZSE:300308",
                    "display_name": "中际旭创",
                    "topic_name": "AI算力",
                    "candidate_state": "候选买点",
                    "priority_score": 86,
                    "expectation_gap_level": "中",
                    "expectation_gap_score": 58,
                    "continuity_score": 78,
                    "tradeability_state": "可观察",
                    "role_label": "龙头",
                    "trend_quality": "顺势",
                    "ranking_bucket": "A",
                    "reasons": ["与主线题材共振。"],
                    "time_horizon": "1-2周",
                    "source_tags": ["watchlist", "theme_core", "theme_resonance"],
                    "action_hint": "保持重点跟踪，等待承接、回踩或量价确认后再行动。",
                    "missing_confirmations": ["仍需等待更明确的承接或回踩确认。"],
                    "invalid_conditions": [],
                }
            ],
            "count": 1,
            "empty_message": None,
            "source_summary": {
                "watchlist_count": 2,
                "theme_candidate_count": 3,
                "candidate_count": 1,
            },
        }


def test_opportunity_pool_router_returns_structured_response(monkeypatch) -> None:
    monkeypatch.setattr(
        "valuecell.server.api.routers.opportunity_pool.get_opportunity_pool_service",
        lambda: FakeOpportunityPoolService(),
    )
    app = FastAPI()
    app.include_router(create_opportunity_pool_router(), prefix="/api/v1")
    client = TestClient(app)

    response = client.get("/api/v1/opportunities/candidates")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"]["available"] is True
    assert payload["data"]["items"][0]["ticker"] == "SZSE:300308"
    assert payload["data"]["source_summary"]["candidate_count"] == 1
