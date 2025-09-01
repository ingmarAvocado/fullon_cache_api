"""
fullon_cache_api - FastAPI WebSocket Gateway for fullon_cache operations.

LRRS-compliant (Little, Responsible, Reusable, Separate) library providing
read-only FastAPI WebSocket API gateway for Redis cache operations with real-time streaming.

ARCHITECTURE: FastAPI + WebSocket Endpoints Only
- FastAPI framework with WebSocket endpoints
- fullon_log for consistent logging across fullon ecosystem
- No REST/HTTP endpoints - only WebSocket endpoints
- Real-time bidirectional communication
- FastAPI dependency injection system
- Pydantic validation for WebSocket messages
- Clean context manager interface

LOGGING: fullon_log Integration
- Component loggers: get_component_logger("fullon.api.cache.*")
- Structured logging with key-value pairs
- Environment-based configuration via .env
- Production-ready with 10,000+ logs/second performance
"""

# Load environment configuration early so downstream libs (fullon_cache, fullon_log)
# see CACHE_* variables from .env without tests wiring them explicitly.
try:  # pragma: no cover - environment dependent
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    # If python-dotenv is unavailable or .env missing, continue silently.
    pass

# Map CACHE_* variables to REDIS_* for compatibility with fullon_cache
try:  # pragma: no cover - environment dependent
    import os

    mappings = {
        "REDIS_HOST": ("CACHE_HOST", "localhost"),
        "REDIS_PORT": ("CACHE_PORT", "6379"),
        "REDIS_DB": ("CACHE_DB", "0"),
        "REDIS_USER": ("CACHE_USER", None),
        "REDIS_PASSWORD": ("CACHE_PASSWORD", None),
        "REDIS_TIMEOUT": ("CACHE_TIMEOUT", "30"),
    }
    for target, (source, default) in mappings.items():
        if os.environ.get(target):
            continue
        val = os.environ.get(source, default)
        # Treat textual 'None'/'null' as unset to avoid bad auth
        if isinstance(val, str) and val.strip().lower() in {"none", "null", ""}:
            continue
        if val is not None:
            os.environ[target] = str(val)
except Exception:
    pass

__version__ = "0.1.0"

# Pydantic models for FastAPI WebSocket operations
# FastAPI WebSocket infrastructure (will be implemented in Issue #4)
# from .app import create_fastapi_app
# from .websocket import CacheWebSocketRouter
# from .client import fullon_cache_api
# Base infrastructure
from .base import (
    BaseFastAPIWebSocketHandler,
    BaseFastAPIWebSocketStream,
    CacheHealthChecker,
)
from .exceptions import (
    CacheFastAPIWebSocketException,
    CacheNotFoundError,
    CacheServiceUnavailableError,
    CacheTimeoutError,
    FastAPIWebSocketConnectionError,
)
from .models import (
    ALLOWED_OPERATIONS,
    BalanceData,
    BotData,
    CacheRequest,
    CacheResponse,
    ErrorCodes,
    ErrorMessage,
    HealthData,
    OHLCVData,
    OrderData,
    PositionData,
    ProcessData,
    StreamMessage,
    TickerData,
    TradeData,
    create_error_response,
    create_success_response,
)
from .types import (
    CacheData,
    CacheKey,
    CacheResult,
    FastAPIStreamMessage,
    FastAPIWebSocketAPIResponse,
    FastAPIWebSocketMessage,
    FastAPIWebSocketRequest,
    FastAPIWebSocketResponse,
    HealthStatus,
    Timestamp,
)

__all__ = [
    "__version__",
    # FastAPI WebSocket API (implemented in later issues)
    # "create_fastapi_app",
    # "fullon_cache_api",
    # "CacheWebSocketRouter",
    # Pydantic Models
    "CacheRequest",
    "CacheResponse",
    "StreamMessage",
    "ErrorMessage",
    "ErrorCodes",
    "ALLOWED_OPERATIONS",
    "create_error_response",
    "create_success_response",
    "TickerData",
    "PositionData",
    "BalanceData",
    "OrderData",
    "TradeData",
    "OHLCVData",
    "ProcessData",
    "BotData",
    "HealthData",
    # Infrastructure Foundation
    "BaseFastAPIWebSocketHandler",
    "BaseFastAPIWebSocketStream",
    "CacheHealthChecker",
    # FastAPI WebSocket Types
    "FastAPIWebSocketMessage",
    "FastAPIWebSocketRequest",
    "FastAPIWebSocketResponse",
    "FastAPIStreamMessage",
    "FastAPIWebSocketAPIResponse",
    "CacheData",
    "CacheResult",
    "CacheKey",
    "HealthStatus",
    "Timestamp",
    # FastAPI WebSocket Exceptions
    "CacheFastAPIWebSocketException",
    "CacheNotFoundError",
    "CacheServiceUnavailableError",
    "CacheTimeoutError",
    "FastAPIWebSocketConnectionError",
]
