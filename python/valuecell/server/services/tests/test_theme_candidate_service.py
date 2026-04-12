from __future__ import annotations

from typing import Any, cast

from valuecell.server.services.assets.theme_candidate_service import ThemeCandidateService


class FakeThemeFocusService:
    def get_theme_focus_snapshot(self, top_n: int = 12) -> dict[str, Any]:
        return {
            "success": True,
            "data": {
                "trading_date": "20250410",
                "items": [
                    {
                        "theme_name": "AI算力",
                        "theme_code": "885001.TI",
                        "theme_state": "加强",
                        "summary": "AI算力趋势加强。",
                        "representative_tickers_json": ["SZSE:300308"],
                        "rank": 2,
                        "expectation_gap_level": "高",
                        "core_leaders_json": ["SZSE:300308"],
                        "metrics": {
                            "change_value": 3.5,
                            "hot_count": 4,
                        },
                    },
                    {
                        "theme_name": "ST板块",
                        "theme_code": "885999.TI",
                        "theme_state": "加强",
                        "summary": "ST方向异动。",
                        "representative_tickers_json": ["ST龙头"],
                        "rank": 1,
                        "expectation_gap_level": "低",
                        "core_leaders_json": ["ST龙头"],
                        "metrics": {
                            "change_value": 5.2,
                            "hot_count": 6,
                        },
                    },
                    {
                        "theme_name": "机器人",
                        "theme_code": "885123.TI",
                        "theme_state": "活跃",
                        "summary": "机器人方向活跃。",
                        "representative_tickers_json": ["SSE:688001"],
                        "rank": 3,
                        "expectation_gap_level": "中",
                        "core_leaders_json": ["SSE:688001"],
                        "metrics": {
                            "change_value": 2.0,
                            "hot_count": 3,
                        },
                    },
                ],
            },
        }


def test_theme_candidate_service_marks_st_as_not_recommended() -> None:
    service = ThemeCandidateService(theme_focus_service=cast(Any, FakeThemeFocusService()))

    result = service.get_theme_candidates(top_n=3)

    assert result["success"] is True
    items = result["data"]["items"]
    assert items[-1]["theme_name"] == "ST板块"
    assert items[-1]["is_suitable_for_direct_participation"] is False
    assert items[-1]["participation_hint"] == "疑似 ST 或高风险方向，默认回避，不建议参与。"


def test_theme_candidate_service_does_not_fabricate_specific_etf() -> None:
    service = ThemeCandidateService(theme_focus_service=cast(Any, FakeThemeFocusService()))

    result = service.get_theme_candidates(top_n=3)

    items = result["data"]["items"]
    ai_item = next(item for item in items if item["theme_name"] == "AI算力")
    kcb_item = next(item for item in items if item["theme_name"] == "机器人")

    assert ai_item["etf_hint"] is not None
    assert "暂无匹配具体 ETF" in ai_item["etf_hint"]["summary"]
    assert kcb_item["preferred_market"] == "科创板为主"
    assert kcb_item["is_suitable_for_direct_participation"] is False
