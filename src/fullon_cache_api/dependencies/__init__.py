"""
FastAPI dependencies for fullon_cache_api.

Provides dependency injection for cache sessions, validation,
and health checking with proper error handling and logging.
"""

# Cache session dependencies
from .cache import (
    get_account_cache,
    get_bot_cache,
    get_ohlcv_cache,
    get_orders_cache,
    get_process_cache,
    get_tick_cache,
    get_trades_cache,
)

# Health check dependencies
from .health import (
    check_all_cache_services,
    require_healthy_cache,
)

# Validation dependencies
from .validation import (
    validate_bot_exists,
    validate_exchange_symbol,
    validate_user_exists,
)

__all__ = [
    # Cache sessions
    "get_tick_cache",
    "get_orders_cache",
    "get_bot_cache",
    "get_account_cache",
    "get_trades_cache",
    "get_ohlcv_cache",
    "get_process_cache",
    # Validation
    "validate_exchange_symbol",
    "validate_user_exists",
    "validate_bot_exists",
    # Health checking
    "check_all_cache_services",
    "require_healthy_cache",
]
