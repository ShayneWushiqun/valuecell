import pandas as pd

from tradingagents.dataflows.tushare_finance import (
    _prepare_statement_frame,
    is_tushare_ashare_ticker,
    to_tushare_ts_code,
)


def test_to_tushare_ts_code() -> None:
    assert is_tushare_ashare_ticker("000001.SZ")
    assert is_tushare_ashare_ticker("600519.SH")
    assert to_tushare_ts_code("000001.SZ") == "000001.SZ"
    assert to_tushare_ts_code("600519.SH") == "600519.SH"
    assert to_tushare_ts_code("600519.SS") == "600519.SH"


def test_prepare_statement_frame_filters_annual_rows() -> None:
    data = pd.DataFrame(
        [
            {
                "end_date": "20250331",
                "ann_date": "20250419",
                "total_assets": 10,
                "total_liab": 8,
            },
            {
                "end_date": "20241231",
                "ann_date": "20250315",
                "total_assets": 9,
                "total_liab": 7,
            },
            {
                "end_date": "20231231",
                "ann_date": "20240315",
                "total_assets": 8,
                "total_liab": 6,
            },
        ]
    )

    result = _prepare_statement_frame(
        data,
        ["end_date", "total_assets", "total_liab"],
        "annual",
        "2025-04-06",
    )

    assert result["end_date"].tolist() == ["2024-12-31", "2023-12-31"]
    assert result["total_assets"].tolist() == [9, 8]
