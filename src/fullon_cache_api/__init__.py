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

__version__ = "0.1.0"

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
