from datetime import date, datetime, timezone

import pytest

from valuecell.server.services import tradingagents_service
from valuecell.server.api.schemas.tradingagents import TradingAgentsRunRequest


class DummyLoader:
    def load_provider_config(self, provider_name: str) -> dict:
        if provider_name == "openai":
            return {
                "connection": {
                    "api_key_env": "OPENAI_API_KEY",
                    "base_url": "https://api.openai.com/v1",
                }
            }
        if provider_name == "siliconflow":
            return {
                "connection": {
                    "api_key_env": "SILICONFLOW_API_KEY",
                    "base_url": "https://api.siliconflow.cn/v1",
                }
            }
        raise FileNotFoundError(provider_name)


def test_resolve_provider_config_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        tradingagents_service,
        "get_config_loader",
        lambda: DummyLoader(),
    )

    resolved = tradingagents_service._resolve_provider_config("openai")

    assert resolved.runtime_provider == "openai"
    assert resolved.api_key == "test-key"
    assert resolved.base_url == "https://api.openai.com/v1"


def test_resolve_provider_config_openai_compatible_mapping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SILICONFLOW_API_KEY", "sf-key")
    monkeypatch.setattr(
        tradingagents_service,
        "get_config_loader",
        lambda: DummyLoader(),
    )

    resolved = tradingagents_service._resolve_provider_config("siliconflow")

    assert resolved.runtime_provider == "openai_compatible"
    assert resolved.api_key == "sf-key"
    assert resolved.base_url == "https://api.siliconflow.cn/v1"


def test_build_reports_and_summary() -> None:
    final_state = {
        "market_report": "# Market\nMomentum remains constructive.",
        "sentiment_report": "Retail sentiment is improving.",
        "news_report": "No major risk events surfaced.",
        "fundamentals_report": "Revenue growth remains stable.",
        "investment_plan": "Research team leans cautiously bullish.",
        "trader_investment_plan": "Scale into positions gradually.",
        "final_trade_decision": "Buy on pullbacks with measured sizing.",
    }

    reports = tradingagents_service._build_reports(final_state)
    summary = tradingagents_service._build_summary(final_state)

    assert len(reports) == 7
    assert reports[0].key == "market_report"
    assert "Momentum remains constructive." in summary.technical
    assert "Revenue growth remains stable." in summary.fundamentals
    assert "Scale into positions gradually." in summary.capital_flow
    assert "Buy on pullbacks with measured sizing." in summary.final_decision


def test_normalize_runtime_symbol_for_shanghai() -> None:
    assert tradingagents_service._normalize_runtime_symbol("600519.SH") == "600519.SS"
    assert tradingagents_service._normalize_runtime_symbol("000001.SZ") == "000001.SZ"


def test_extract_stream_logs_emits_completed_steps_once() -> None:
    delivered_keys: set[str] = set()
    state = {
        "market_report": "Market report ready.",
        "sentiment_report": "",
        "news_report": "",
        "fundamentals_report": "",
        "investment_plan": "",
        "trader_investment_plan": "",
        "final_trade_decision": "",
    }

    logs = tradingagents_service._extract_stream_logs(state, delivered_keys)
    duplicated_logs = tradingagents_service._extract_stream_logs(state, delivered_keys)

    assert len(logs) == 1
    assert logs[0].stage == "market_report_ready"
    assert duplicated_logs == []


def test_normalize_step_logs_for_succeeded_run() -> None:
    running_log = tradingagents_service._build_step_log(
        stage="running",
        title="TradingAgents is running",
        message="The multi-agent stock analysis has started.",
        level="running",
        progress_percent=8,
    )
    completed_log = tradingagents_service._build_step_log(
        stage="completed",
        title="TradingAgents completed",
        message="The final report and decision are ready.",
        level="completed",
        progress_percent=100,
    )

    normalized_logs = tradingagents_service._normalize_step_logs_for_status(
        [running_log, completed_log],
        "succeeded",
    )

    assert normalized_logs[0].level == "completed"
    assert normalized_logs[1].level == "completed"


def test_run_tradingagents_streaming_sync_sets_ticker_for_log_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    final_state = {
        "company_of_interest": "000988.SZ",
        "trade_date": "2026-04-06",
        "market_report": "Technical done.",
        "sentiment_report": "Sentiment done.",
        "news_report": "News done.",
        "fundamentals_report": "Fundamentals done.",
        "investment_debate_state": {
            "bull_history": [],
            "bear_history": [],
            "history": [],
            "current_response": "",
            "judge_decision": "",
        },
        "trader_investment_plan": "Trading plan done.",
        "risk_debate_state": {
            "aggressive_history": [],
            "conservative_history": [],
            "neutral_history": [],
            "history": [],
            "judge_decision": "",
        },
        "investment_plan": "Research plan done.",
        "final_trade_decision": "Buy on weakness.",
    }
    logged = {}

    class DummyPropagator:
        def create_initial_state(self, company_name: str, trade_date: str):
            return {"company": company_name, "trade_date": trade_date}

        def get_graph_args(self):
            return {}

    class DummyGraphRunner:
        def stream(self, init_state, **kwargs):
            yield final_state

    class DummyGraph:
        def __init__(self, selected_analysts, debug, config):
            self.propagator = DummyPropagator()
            self.graph = DummyGraphRunner()
            self.config = config
            self.ticker = None
            self.curr_state = None

        def _log_state(self, trade_date: str, state):
            logged["ticker"] = self.ticker
            logged["trade_date"] = trade_date

        def process_signal(self, text: str) -> str:
            return "BUY"

    monkeypatch.setattr(tradingagents_service, "TradingAgentsGraph", DummyGraph)

    request = TradingAgentsRunRequest(
        symbol="000988.SZ",
        trade_date=date(2026, 4, 6),
        provider="openai-compatible",
        deep_model="foo",
        quick_model="bar",
        output_language="Chinese",
        analysts=["market", "social"],
        debug=False,
    )
    provider_config = tradingagents_service.ResolvedProviderConfig(
        source_provider="openai-compatible",
        runtime_provider="openai_compatible",
        base_url="https://example.com",
        api_key="test-key",
    )

    result = tradingagents_service._run_tradingagents_streaming_sync(
        request,
        provider_config,
        None,
    )

    assert logged["ticker"] == "000988.SZ"
    assert logged["trade_date"] == "2026-04-06"
    assert result.decision_signal == "BUY"


def test_ensure_utc_handles_naive_and_aware_datetime() -> None:
    naive = datetime(2026, 4, 6, 12, 0, 0)
    aware = datetime(2026, 4, 6, 12, 0, 0, tzinfo=timezone.utc)

    normalized_naive = tradingagents_service._ensure_utc(naive)
    normalized_aware = tradingagents_service._ensure_utc(aware)

    assert normalized_naive.tzinfo == timezone.utc
    assert normalized_aware.tzinfo == timezone.utc
