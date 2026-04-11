from __future__ import annotations

from valuecell.server.services.assets.theme_focus_service import ThemeFocusService


class FakeShortCycleDataService:
    def get_theme_focus_data(self, **kwargs):
        return {
            "success": True,
            "trade_date": "20250410",
            "data": {
                "ths_index": {
                    "count": 3,
                    "columns": ["ts_code", "name"],
                    "rows": [
                        {"ts_code": "885001.TI", "name": "AI算力"},
                        {"ts_code": "885002.TI", "name": "机器人"},
                        {"ts_code": "885003.TI", "name": "新能源车"},
                    ],
                },
                "ths_daily": {
                    "count": 3,
                    "columns": ["ts_code", "pct_chg"],
                    "rows": [
                        {"ts_code": "885001.TI", "pct_chg": 4.2},
                        {"ts_code": "885002.TI", "pct_chg": 2.1},
                        {"ts_code": "885003.TI", "pct_chg": -1.8},
                    ],
                },
                "ths_member": {
                    "count": 6,
                    "columns": ["ts_code", "con_ticker"],
                    "rows": [
                        {"ts_code": "885001.TI", "con_ticker": "SZSE:300308"},
                        {"ts_code": "885001.TI", "con_ticker": "SSE:603019"},
                        {"ts_code": "885002.TI", "con_ticker": "SZSE:300024"},
                        {"ts_code": "885002.TI", "con_ticker": "SSE:688017"},
                        {"ts_code": "885003.TI", "con_ticker": "SZSE:002594"},
                        {"ts_code": "885003.TI", "con_ticker": "SZSE:300750"},
                    ],
                },
                "moneyflow_ind_ths": {
                    "count": 3,
                    "columns": ["ts_code", "net_amount"],
                    "rows": [
                        {"ts_code": "885001.TI", "net_amount": 12.5},
                        {"ts_code": "885002.TI", "net_amount": 7.0},
                        {"ts_code": "885003.TI", "net_amount": -3.2},
                    ],
                },
                "moneyflow_ind_dc": {
                    "count": 3,
                    "columns": ["ts_code", "net_amount"],
                    "rows": [
                        {"ts_code": "885001.TI", "net_amount": 11.3},
                        {"ts_code": "885002.TI", "net_amount": 4.2},
                        {"ts_code": "885003.TI", "net_amount": -2.0},
                    ],
                },
                "kpl_list": {
                    "count": 5,
                    "columns": ["reason_type", "ticker"],
                    "rows": [
                        {"reason_type": "AI算力", "ticker": "SZSE:300308"},
                        {"reason_type": "AI算力", "ticker": "SSE:603019"},
                        {"reason_type": "机器人", "ticker": "SZSE:300024"},
                        {"reason_type": "机器人", "ticker": "SSE:688017"},
                        {"reason_type": "AI算力", "ticker": "SZSE:002261"},
                    ],
                },
                "ths_hot": {
                    "count": 4,
                    "columns": ["name", "ticker"],
                    "rows": [
                        {"name": "AI算力", "ticker": "SZSE:300308"},
                        {"name": "AI算力", "ticker": "SSE:603019"},
                        {"name": "机器人", "ticker": "SZSE:300024"},
                        {"name": "新能源车", "ticker": "SZSE:002594"},
                    ],
                },
                "tdx_index": {
                    "count": 0,
                    "columns": [],
                    "rows": [],
                },
            },
        }


def test_theme_focus_service_returns_ranked_snapshots() -> None:
    service = ThemeFocusService(
        short_cycle_data_service=FakeShortCycleDataService()
    )

    result = service.get_theme_focus_snapshot(
        trade_date="2025-04-10",
        start_date="2025-04-01",
        end_date="2025-04-10",
        top_n=2,
    )

    assert result["success"] is True
    items = result["data"]["items"]
    assert len(items) == 2
    assert items[0]["theme_name"] == "AI算力"
    assert items[0]["rank"] == 1
    assert items[0]["theme_state"] in {"加强", "活跃"}
    assert items[0]["representative_tickers_json"]
    assert items[0]["core_leaders_json"]


def test_theme_focus_service_builds_expectation_gap_and_institutions() -> None:
    service = ThemeFocusService(
        short_cycle_data_service=FakeShortCycleDataService()
    )

    result = service.get_theme_focus_snapshot(top_n=3)

    assert result["success"] is True
    ai_item = result["data"]["items"][0]
    assert ai_item["expectation_gap_level"] in {"高", "中"}
    assert isinstance(ai_item["core_institutions_json"], list)
    assert ai_item["metrics"]["score"] >= 60
