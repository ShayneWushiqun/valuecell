"""ValueCell Asset Service Module.

This module provides high-level asset service functionality for financial asset management,
search, price retrieval, and watchlist operations with internationalization support.

Key Features:
- Asset search with localization
- Real-time and historical price data
- Watchlist management
- Multi-language support
- Integration with multiple data adapters

Usage Example:
    ```python
    from valuecell.services.assets import (
        get_asset_service, search_assets, add_to_watchlist
    )

    # Search for assets
    results = search_assets("AAPL", language="zh-Hans")

    # Add to watchlist
    add_to_watchlist(user_id="user123", ticker="NASDAQ:AAPL")
    ```
"""

from .asset_service import (
    AssetService,
    add_to_watchlist,
    get_asset_info,
    get_asset_price,
    get_asset_service,
    get_watchlist,
    reset_asset_service,
    search_assets,
)
from .emotion_cycle_service import (
    EmotionCycleService,
    get_emotion_cycle_service,
    reset_emotion_cycle_service,
)
from .homepage_context_service import (
    HomepageContextService,
    get_homepage_context_service,
    reset_homepage_context_service,
)
from .market_pulse_service import (
    MarketPulseService,
    get_market_pulse_service,
    reset_market_pulse_service,
)
from .theme_focus_service import (
    ThemeFocusService,
    get_theme_focus_service,
    reset_theme_focus_service,
)
from .short_cycle_data_service import (
    ShortCycleDataService,
    get_short_cycle_data_service,
    reset_short_cycle_data_service,
)

__version__ = "1.0.0"

__all__ = [
    # Service class
    "AssetService",
    "MarketPulseService",
    "EmotionCycleService",
    "HomepageContextService",
    "ThemeFocusService",
    "ShortCycleDataService",
    "get_asset_service",
    "get_market_pulse_service",
    "get_emotion_cycle_service",
    "get_homepage_context_service",
    "get_theme_focus_service",
    "get_short_cycle_data_service",
    "reset_asset_service",
    "reset_market_pulse_service",
    "reset_emotion_cycle_service",
    "reset_homepage_context_service",
    "reset_theme_focus_service",
    "reset_short_cycle_data_service",
    # Convenience functions
    "search_assets",
    "get_asset_info",
    "get_asset_price",
    "add_to_watchlist",
    "get_watchlist",
]
