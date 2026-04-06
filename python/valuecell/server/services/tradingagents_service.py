import asyncio
import copy
import os
import re
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Literal

from loguru import logger

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph
from valuecell.config.loader import get_config_loader
from valuecell.server.api.schemas.tradingagents import (
    TradingAgentsReportData,
    TradingAgentsRunData,
    TradingAgentsRunListData,
    TradingAgentsRunRequest,
    TradingAgentsStepLogData,
    TradingAgentsSummaryData,
)
from valuecell.server.db.connection import get_database_manager
from valuecell.server.db.models import TradingAgentsRun

TRADING_AGENTS_LOCK = asyncio.Lock()
BACKGROUND_RUN_TASKS: dict[str, asyncio.Task[None]] = {}
SUPPORTED_PROVIDER_MAP = {
    "openai": "openai",
    "google": "google",
    "openrouter": "openrouter",
    "ollama": "ollama",
    "openai-compatible": "openai_compatible",
    "siliconflow": "openai_compatible",
    "deepseek": "openai_compatible",
    "dashscope": "openai_compatible",
}
RUNTIME_API_KEY_ENV = {
    "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "openai_compatible": "OPENAI_COMPATIBLE_API_KEY",
}
REPORT_SPECS = (
    ("market_report", "Market Analysis"),
    ("sentiment_report", "Sentiment Analysis"),
    ("news_report", "News Analysis"),
    ("fundamentals_report", "Fundamentals Analysis"),
    ("investment_plan", "Research Team Decision"),
    ("trader_investment_plan", "Trading Team Plan"),
    ("final_trade_decision", "Final Trade Decision"),
)
STREAM_STAGE_SPECS = (
    ("market_report", "market_report_ready", "Technical view completed", 38),
    ("sentiment_report", "sentiment_report_ready", "Sentiment view completed", 48),
    ("news_report", "news_report_ready", "News view completed", 58),
    ("fundamentals_report", "fundamentals_report_ready", "Fundamentals view completed", 68),
    ("investment_plan", "research_plan_ready", "Research debate completed", 80),
    ("trader_investment_plan", "trader_plan_ready", "Trading plan completed", 90),
    ("final_trade_decision", "final_decision_ready", "Final decision completed", 96),
)
RUNNING_STATUSES = {"queued", "running"}


@dataclass(frozen=True)
class ResolvedProviderConfig:
    source_provider: str
    runtime_provider: str
    base_url: str | None
    api_key: str | None


@dataclass(frozen=True)
class SyncRunResult:
    decision_signal: str
    summary: TradingAgentsSummaryData
    reports: list[TradingAgentsReportData]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _normalize_provider(provider: str) -> str:
    return provider.strip().lower()


def _get_results_dir() -> str:
    return str(Path(__file__).resolve().parents[3] / "runtime" / "tradingagents")


def _normalize_runtime_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if normalized.endswith(".SH"):
        return f"{normalized[:-3]}.SS"
    return normalized


def _resolve_provider_config(provider: str) -> ResolvedProviderConfig:
    normalized_provider = _normalize_provider(provider)
    runtime_provider = SUPPORTED_PROVIDER_MAP.get(normalized_provider)

    if runtime_provider is None:
        raise ValueError(f"Provider '{provider}' is not supported by TradingAgents")

    loader = get_config_loader()
    try:
        provider_config = loader.load_provider_config(normalized_provider)
    except FileNotFoundError as exc:
        raise ValueError(
            f"Provider '{provider}' is not configured in ValueCell",
        ) from exc
    connection = provider_config.get("connection", {})
    api_key_env = connection.get("api_key_env")
    api_key = os.getenv(api_key_env) if api_key_env else None
    base_url = connection.get("base_url")

    if runtime_provider != "ollama" and not api_key:
        raise ValueError(f"Provider '{provider}' is not configured with an API key")

    if runtime_provider == "openai_compatible" and not base_url:
        raise ValueError(f"Provider '{provider}' is missing a base URL")

    return ResolvedProviderConfig(
        source_provider=normalized_provider,
        runtime_provider=runtime_provider,
        base_url=base_url,
        api_key=api_key,
    )


@contextmanager
def _temporary_runtime_env(config: ResolvedProviderConfig) -> Iterator[None]:
    previous: dict[str, str | None] = {}
    runtime_env_name = RUNTIME_API_KEY_ENV.get(config.runtime_provider)

    if runtime_env_name and config.api_key:
        previous[runtime_env_name] = os.environ.get(runtime_env_name)
        os.environ[runtime_env_name] = config.api_key

    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _build_runtime_config(
    request: TradingAgentsRunRequest,
    provider_config: ResolvedProviderConfig,
) -> dict[str, Any]:
    runtime_config = copy.deepcopy(DEFAULT_CONFIG)
    runtime_config["results_dir"] = _get_results_dir()
    runtime_config["llm_provider"] = provider_config.runtime_provider
    runtime_config["deep_think_llm"] = request.deep_model
    runtime_config["quick_think_llm"] = request.quick_model
    runtime_config["output_language"] = request.output_language
    if provider_config.base_url:
        runtime_config["backend_url"] = provider_config.base_url
    return runtime_config


def _sanitize_markdown(markdown: str) -> str:
    text = re.sub(r"`{1,3}", "", markdown)
    text = re.sub(r"[*_>#-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _summarize_report(markdown: str | None) -> str:
    if not markdown:
        return ""
    lines = [line.strip() for line in markdown.splitlines() if line.strip()]
    for line in lines:
        if not line.startswith("#"):
            summary = _sanitize_markdown(line)
            if summary:
                return summary[:240]
    return _sanitize_markdown(markdown)[:240]


def _build_reports(final_state: dict[str, Any]) -> list[TradingAgentsReportData]:
    reports: list[TradingAgentsReportData] = []
    for key, title in REPORT_SPECS:
        content = final_state.get(key)
        if isinstance(content, str) and content.strip():
            reports.append(
                TradingAgentsReportData(
                    key=key,
                    title=title,
                    content=content,
                )
            )
    return reports


def _build_summary(final_state: dict[str, Any]) -> TradingAgentsSummaryData:
    return TradingAgentsSummaryData(
        technical=_summarize_report(final_state.get("market_report")),
        fundamentals=_summarize_report(final_state.get("fundamentals_report")),
        sentiment=_summarize_report(final_state.get("sentiment_report")),
        capital_flow=_summarize_report(final_state.get("trader_investment_plan")),
        final_decision=_summarize_report(final_state.get("final_trade_decision")),
    )


def _build_step_log(
    stage: str,
    title: str,
    message: str,
    level: Literal["info", "running", "completed", "warning", "error"],
    progress_percent: int | None,
) -> TradingAgentsStepLogData:
    return TradingAgentsStepLogData(
        stage=stage,
        title=title,
        message=message,
        level=level,
        progress_percent=progress_percent,
        created_at=_utcnow(),
    )


def _get_stage_title(stage: str | None) -> str:
    if not stage:
        return "queued"
    return stage.replace("_", " ")


def _extract_stream_logs(
    state: dict[str, Any],
    delivered_keys: set[str],
) -> list[TradingAgentsStepLogData]:
    logs: list[TradingAgentsStepLogData] = []
    for key, stage, title, progress_percent in STREAM_STAGE_SPECS:
        if key in delivered_keys:
            continue
        content = state.get(key)
        if isinstance(content, str) and content.strip():
            delivered_keys.add(key)
            logs.append(
                _build_step_log(
                    stage=stage,
                    title=title,
                    message=_summarize_report(content) or title,
                    level="completed",
                    progress_percent=progress_percent,
                )
            )
    return logs


def _normalize_step_logs_for_status(
    step_logs: list[TradingAgentsStepLogData],
    status: str,
) -> list[TradingAgentsStepLogData]:
    if status != "succeeded":
        return step_logs

    normalized_logs: list[TradingAgentsStepLogData] = []
    for log in step_logs:
        if log.level == "running":
            normalized_logs.append(log.model_copy(update={"level": "completed"}))
            continue
        normalized_logs.append(log)
    return normalized_logs


def _run_tradingagents_streaming_sync(
    request: TradingAgentsRunRequest,
    provider_config: ResolvedProviderConfig,
    progress_callback: Callable[[TradingAgentsStepLogData], None] | None = None,
) -> SyncRunResult:
    runtime_config = _build_runtime_config(request, provider_config)
    runtime_symbol = _normalize_runtime_symbol(request.symbol)
    graph = TradingAgentsGraph(
        selected_analysts=request.analysts,
        debug=True,
        config=runtime_config,
    )
    graph.ticker = runtime_symbol

    if progress_callback is not None:
        progress_callback(
            _build_step_log(
                stage="initializing_graph",
                title="Initializing TradingAgents graph",
                message=f"Preparing models and data tools for {request.symbol}",
                level="running",
                progress_percent=12,
            )
        )

    init_agent_state = graph.propagator.create_initial_state(
        runtime_symbol,
        request.trade_date.isoformat(),
    )
    args = graph.propagator.get_graph_args()
    delivered_keys: set[str] = set()
    final_state: dict[str, Any] | None = None

    if progress_callback is not None:
        progress_callback(
            _build_step_log(
                stage="analyst_team_running",
                title="Analyst team is working",
                message=f"Enabled analysts: {', '.join(request.analysts)}",
                level="running",
                progress_percent=22,
            )
        )

    for chunk in graph.graph.stream(init_agent_state, **args):
        if not isinstance(chunk, dict):
            continue
        final_state = chunk
        if progress_callback is None:
            continue
        for log in _extract_stream_logs(chunk, delivered_keys):
            progress_callback(log)

    if final_state is None:
        raise ValueError("TradingAgents returned no final state")

    graph.curr_state = final_state
    try:
        graph._log_state(request.trade_date.isoformat(), final_state)
    except Exception as exc:
        logger.warning("TradingAgents state logging failed: {}", str(exc))

    return SyncRunResult(
        decision_signal=str(graph.process_signal(final_state["final_trade_decision"])),
        summary=_build_summary(final_state),
        reports=_build_reports(final_state),
    )


class TradingAgentsService:
    def __init__(self) -> None:
        self.db_manager = get_database_manager()

    def _create_run_record(self, request: TradingAgentsRunRequest) -> TradingAgentsRun:
        run_id = f"tradingagents_{uuid.uuid4().hex}"
        now = _utcnow()
        initial_log = _build_step_log(
            stage="queued",
            title="Run created",
            message="The analysis task has been queued and is waiting to start.",
            level="info",
            progress_percent=0,
        )

        session = self.db_manager.get_session()
        try:
            record = TradingAgentsRun(
                run_id=run_id,
                status="queued",
                symbol=request.symbol,
                trade_date=request.trade_date,
                provider=request.provider,
                deep_model=request.deep_model,
                quick_model=request.quick_model,
                output_language=request.output_language,
                analysts=list(request.analysts),
                debug=request.debug,
                progress_stage="queued",
                progress_message=initial_log.message,
                progress_percent=0,
                reports=[],
                step_logs=[initial_log.model_dump(mode="json")],
                created_at=now,
                updated_at=now,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
        finally:
            session.close()

    def _get_record(self, run_id: str) -> TradingAgentsRun | None:
        session = self.db_manager.get_session()
        try:
            return (
                session.query(TradingAgentsRun)
                .filter(TradingAgentsRun.run_id == run_id)
                .first()
            )
        finally:
            session.close()

    def _append_step_log(
        self,
        run_id: str,
        log: TradingAgentsStepLogData,
        *,
        status: str | None = None,
        progress_stage: str | None = None,
        progress_message: str | None = None,
        progress_percent: int | None = None,
    ) -> None:
        session = self.db_manager.get_session()
        try:
            record = (
                session.query(TradingAgentsRun)
                .filter(TradingAgentsRun.run_id == run_id)
                .first()
            )
            if record is None:
                return
            current_logs = list(record.step_logs or [])
            current_logs.append(log.model_dump(mode="json"))
            record.step_logs = current_logs
            if status is not None:
                record.status = status
            record.progress_stage = progress_stage or log.stage
            record.progress_message = progress_message or log.message
            record.progress_percent = (
                progress_percent if progress_percent is not None else log.progress_percent
            )
            record.updated_at = _utcnow()
            session.add(record)
            session.commit()
        finally:
            session.close()

    def _update_run_record(
        self,
        run_id: str,
        *,
        status: str | None = None,
        progress_stage: str | None = None,
        progress_message: str | None = None,
        progress_percent: int | None = None,
        reports: list[TradingAgentsReportData] | None = None,
        summary: TradingAgentsSummaryData | None = None,
        decision_signal: str | None = None,
        error_message: str | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> None:
        session = self.db_manager.get_session()
        try:
            record = (
                session.query(TradingAgentsRun)
                .filter(TradingAgentsRun.run_id == run_id)
                .first()
            )
            if record is None:
                return
            if status is not None:
                record.status = status
            if progress_stage is not None:
                record.progress_stage = progress_stage
            if progress_message is not None:
                record.progress_message = progress_message
            if progress_percent is not None:
                record.progress_percent = progress_percent
            if reports is not None:
                record.reports = [item.model_dump(mode="json") for item in reports]
            if summary is not None:
                record.summary = summary.model_dump(mode="json")
            if decision_signal is not None:
                record.decision_signal = decision_signal
            if error_message is not None:
                record.error_message = error_message
            if started_at is not None:
                record.started_at = started_at
            if completed_at is not None:
                record.completed_at = completed_at
            record.updated_at = _utcnow()
            session.add(record)
            session.commit()
        finally:
            session.close()

    def _to_run_data(self, record: TradingAgentsRun) -> TradingAgentsRunData:
        summary = (
            TradingAgentsSummaryData.model_validate(record.summary)
            if record.summary
            else None
        )
        reports = [
            TradingAgentsReportData.model_validate(item)
            for item in (record.reports or [])
        ]
        step_logs = [
            TradingAgentsStepLogData.model_validate(item)
            for item in (record.step_logs or [])
        ]
        step_logs = _normalize_step_logs_for_status(step_logs, record.status)
        return TradingAgentsRunData(
            run_id=record.run_id,
            status=record.status,
            symbol=record.symbol,
            trade_date=record.trade_date,
            provider=record.provider,
            deep_model=record.deep_model,
            quick_model=record.quick_model,
            output_language=record.output_language,
            analysts=list(record.analysts or []),
            debug=record.debug,
            progress_stage=record.progress_stage,
            progress_message=record.progress_message,
            progress_percent=record.progress_percent,
            decision_signal=record.decision_signal,
            summary=summary,
            reports=reports,
            step_logs=step_logs,
            error_message=record.error_message,
            started_at=record.started_at,
            completed_at=record.completed_at,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    async def run_sync_analysis(
        self,
        request: TradingAgentsRunRequest,
    ) -> TradingAgentsRunData:
        provider_config = _resolve_provider_config(request.provider)
        created_at = _utcnow()

        logger.info(
            "Running TradingAgents synchronously for {symbol} on {trade_date} with provider {provider}",
            symbol=request.symbol,
            trade_date=request.trade_date.isoformat(),
            provider=request.provider,
        )

        async with TRADING_AGENTS_LOCK:
            with _temporary_runtime_env(provider_config):
                result = await asyncio.to_thread(
                    _run_tradingagents_streaming_sync,
                    request,
                    provider_config,
                    None,
                )

        return TradingAgentsRunData(
            run_id=f"tradingagents_{uuid.uuid4().hex}",
            status="succeeded",
            symbol=request.symbol,
            trade_date=request.trade_date,
            provider=request.provider,
            deep_model=request.deep_model,
            quick_model=request.quick_model,
            output_language=request.output_language,
            analysts=list(request.analysts),
            debug=request.debug,
            progress_stage="completed",
            progress_message="TradingAgents analysis completed successfully.",
            progress_percent=100,
            decision_signal=result.decision_signal,
            summary=result.summary,
            reports=result.reports,
            step_logs=[],
            error_message=None,
            started_at=created_at,
            completed_at=_utcnow(),
            created_at=created_at,
            updated_at=_utcnow(),
        )

    async def create_run(self, request: TradingAgentsRunRequest) -> TradingAgentsRunData:
        provider_config = _resolve_provider_config(request.provider)
        record = self._create_run_record(request)
        task = asyncio.create_task(
            self._run_in_background(record.run_id, request, provider_config)
        )
        BACKGROUND_RUN_TASKS[record.run_id] = task
        task.add_done_callback(lambda _: BACKGROUND_RUN_TASKS.pop(record.run_id, None))
        refreshed = self._get_record(record.run_id)
        if refreshed is None:
            raise ValueError("TradingAgents run record was not created")
        return self._to_run_data(refreshed)

    async def get_run(self, run_id: str) -> TradingAgentsRunData | None:
        record = self._get_record(run_id)
        if record is None:
            return None
        return self._to_run_data(record)

    async def list_runs(self, limit: int = 20) -> TradingAgentsRunListData:
        session = self.db_manager.get_session()
        try:
            query = session.query(TradingAgentsRun).order_by(TradingAgentsRun.created_at.desc())
            rows = query.limit(limit).all()
            total = query.count()
            running_count = (
                session.query(TradingAgentsRun)
                .filter(TradingAgentsRun.status.in_(list(RUNNING_STATUSES)))
                .count()
            )
            return TradingAgentsRunListData(
                runs=[self._to_run_data(item) for item in rows],
                total=total,
                running_count=running_count,
            )
        finally:
            session.close()

    async def _run_in_background(
        self,
        run_id: str,
        request: TradingAgentsRunRequest,
        provider_config: ResolvedProviderConfig,
    ) -> None:
        started_at = _utcnow()
        heartbeat_task: asyncio.Task[None] | None = None
        start_log = _build_step_log(
            stage="waiting_for_execution_slot",
            title="Waiting for execution slot",
            message="The run is waiting for an available TradingAgents worker.",
            level="running",
            progress_percent=3,
        )
        self._append_step_log(run_id, start_log, status="queued")

        try:
            async with TRADING_AGENTS_LOCK:
                running_log = _build_step_log(
                    stage="running",
                    title="TradingAgents is running",
                    message="The multi-agent stock analysis has started.",
                    level="running",
                    progress_percent=8,
                )
                self._append_step_log(
                    run_id,
                    running_log,
                    status="running",
                    progress_stage="running",
                    progress_message=running_log.message,
                    progress_percent=8,
                )
                self._update_run_record(run_id, started_at=started_at, status="running")
                heartbeat_task = asyncio.create_task(self._heartbeat(run_id))

                with _temporary_runtime_env(provider_config):
                    result = await asyncio.to_thread(
                        _run_tradingagents_streaming_sync,
                        request,
                        provider_config,
                        lambda log: self._append_step_log(run_id, log, status="running"),
                    )

                completed_log = _build_step_log(
                    stage="completed",
                    title="TradingAgents completed",
                    message="The final report and decision are ready.",
                    level="completed",
                    progress_percent=100,
                )
                self._append_step_log(
                    run_id,
                    completed_log,
                    status="succeeded",
                    progress_stage="completed",
                    progress_message=completed_log.message,
                    progress_percent=100,
                )
                self._update_run_record(
                    run_id,
                    status="succeeded",
                    progress_stage="completed",
                    progress_message=completed_log.message,
                    progress_percent=100,
                    reports=result.reports,
                    summary=result.summary,
                    decision_signal=result.decision_signal,
                    completed_at=_utcnow(),
                )
        except Exception as exc:
            logger.exception("TradingAgents background run failed")
            failed_log = _build_step_log(
                stage="failed",
                title="TradingAgents failed",
                message=str(exc),
                level="error",
                progress_percent=None,
            )
            self._append_step_log(
                run_id,
                failed_log,
                status="failed",
                progress_stage="failed",
                progress_message=str(exc),
            )
            self._update_run_record(
                run_id,
                status="failed",
                progress_stage="failed",
                progress_message=str(exc),
                error_message=str(exc),
                completed_at=_utcnow(),
            )
        finally:
            if heartbeat_task is not None:
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass

    async def _heartbeat(self, run_id: str) -> None:
        while True:
            await asyncio.sleep(8)
            record = self._get_record(run_id)
            if record is None or record.status != "running":
                return
            if record.started_at is None:
                continue
            elapsed_seconds = int(
                (_utcnow() - _ensure_utc(record.started_at)).total_seconds()
            )
            message = (
                f"Still running: {_get_stage_title(record.progress_stage)} "
                f"({elapsed_seconds}s elapsed)"
            )
            self._update_run_record(
                run_id,
                progress_message=message,
                progress_stage=record.progress_stage or "running",
                progress_percent=record.progress_percent,
            )
