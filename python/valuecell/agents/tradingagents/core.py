import datetime
import json
from typing import Any, AsyncGenerator, Dict, Optional

from loguru import logger

from valuecell.core.agent.responses import streaming
from valuecell.core.types import BaseAgent, ComponentType, ReportComponentData, StreamResponse
from valuecell.server.api.schemas.tradingagents import TradingAgentsRunRequest
from valuecell.server.services.tradingagents_service import TradingAgentsService


class TradingAgents(BaseAgent):
    def __init__(self, **kwargs: Any):
        super().__init__()
        self.service = TradingAgentsService()

    async def stream(
        self,
        query: str,
        conversation_id: str,
        task_id: str,
        dependencies: Optional[Dict] = None,
    ) -> AsyncGenerator[StreamResponse, None]:
        try:
            request = TradingAgentsRunRequest.model_validate_json(query)
        except Exception as exc:
            logger.warning("TradingAgents request parsing failed: {}", str(exc))
            yield streaming.failed(str(exc))
            return

        try:
            result = await self.service.run_sync_analysis(request)
        except Exception as exc:
            logger.warning("TradingAgents analysis failed: {}", str(exc))
            yield streaming.failed(str(exc))
            return

        create_time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        for report in result.reports:
            payload = ReportComponentData(
                title=report.title,
                data=report.content,
                create_time=create_time,
            )
            yield streaming.component_generator(
                payload.model_dump_json(),
                ComponentType.REPORT.value,
                component_id=f"tradingagents:{report.key}",
            )

        yield streaming.message_chunk(
            json.dumps(
                {
                    "run_id": result.run_id,
                    "decision_signal": result.decision_signal,
                    "summary": result.summary.model_dump() if result.summary else {},
                },
                ensure_ascii=False,
            )
        )
        yield streaming.done()
