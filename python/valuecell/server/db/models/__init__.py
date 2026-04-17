"""
ValueCell Server - Database Models

This package contains all database models for the ValueCell server.
All models are automatically imported to ensure they are registered with SQLAlchemy.
"""

# Import all models to ensure they are registered with SQLAlchemy
from .agent import Agent
from .ashare_daily_snapshot import AShareDailySnapshot
from .asset import Asset
from .daily_briefing import DailyBriefing
from .decision_context_window import DecisionContextWindow
from .decision_alert import DecisionAlert
from .decision_record import DecisionRecord
from .holding_diagnosis import HoldingDiagnosis

# Import base model
from .base import Base
from .strategy import Strategy
from .strategy_compose_cycle import StrategyComposeCycle
from .strategy_detail import StrategyDetail
from .strategy_holding import StrategyHolding
from .strategy_instruction import StrategyInstruction
from .strategy_portfolio import StrategyPortfolioView
from .tradingagents_run import TradingAgentsRun
from .user_holding import UserHolding
from .user_profile import ProfileCategory, UserProfile
from .watchlist import Watchlist, WatchlistItem
from .short_cycle_context_event import ShortCycleContextEvent

# Export all models
__all__ = [
    "Base",
    "Agent",
    "AShareDailySnapshot",
    "Asset",
    "Strategy",
    "Watchlist",
    "WatchlistItem",
    "UserHolding",
    "HoldingDiagnosis",
    "DailyBriefing",
    "DecisionContextWindow",
    "DecisionAlert",
    "DecisionRecord",
    "ShortCycleContextEvent",
    "UserProfile",
    "ProfileCategory",
    "StrategyHolding",
    "StrategyDetail",
    "StrategyPortfolioView",
    "StrategyComposeCycle",
    "StrategyInstruction",
    "TradingAgentsRun",
]
