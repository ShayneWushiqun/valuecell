from typing import Any, Dict

from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from .base import Base


class TradingAgentsRun(Base):
    __tablename__ = "tradingagents_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(String(100), nullable=True, index=True)
    status = Column(String(50), nullable=False, default="queued", index=True)
    symbol = Column(String(50), nullable=False, index=True)
    trade_date = Column(Date, nullable=False)
    provider = Column(String(100), nullable=False)
    deep_model = Column(String(200), nullable=False)
    quick_model = Column(String(200), nullable=False)
    output_language = Column(String(50), nullable=False, default="Chinese")
    analysts = Column(JSON, nullable=False, comment="Enabled analyst modules")
    debug = Column(Boolean, nullable=False, default=False)
    progress_stage = Column(String(100), nullable=True)
    progress_message = Column(Text, nullable=True)
    progress_percent = Column(Integer, nullable=True)
    decision_signal = Column(String(50), nullable=True)
    summary = Column(JSON, nullable=True)
    reports = Column(JSON, nullable=True)
    step_logs = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    runtime_metadata = Column(JSON, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "symbol": self.symbol,
            "trade_date": self.trade_date.isoformat() if self.trade_date else None,
            "provider": self.provider,
            "deep_model": self.deep_model,
            "quick_model": self.quick_model,
            "output_language": self.output_language,
            "analysts": self.analysts or [],
            "debug": self.debug,
            "progress_stage": self.progress_stage,
            "progress_message": self.progress_message,
            "progress_percent": self.progress_percent,
            "decision_signal": self.decision_signal,
            "summary": self.summary,
            "reports": self.reports or [],
            "step_logs": self.step_logs or [],
            "error_message": self.error_message,
            "runtime_metadata": self.runtime_metadata or {},
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
