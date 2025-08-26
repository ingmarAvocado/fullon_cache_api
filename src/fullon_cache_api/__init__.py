"""
fullon_cache_api - FastAPI Gateway for fullon_cache operations.

LRRS-compliant (Little, Responsible, Reusable, Separate) library providing
read-only REST API gateway for Redis cache operations.
"""

# Import version
__version__ = "0.1.0"

# Core exports (will be implemented in later issues)
# from .gateway import FullonCacheGateway
# from .routers import get_all_routers

# Base infrastructure
from .base import BaseCacheOperation, CacheHealthChecker
from .exceptions import (
    CacheAPIException,
    CacheNotFoundError,
    CacheServiceUnavailableError,
    CacheTimeoutError,
)
from .types import (
    APIResponse,
    CacheData,
    CacheKey,
    CacheResult,
    HealthStatus,
    Timestamp,
)

__all__ = [
    "__version__",
    # Core functionality (placeholders for future issues)
    # "FullonCacheGateway",
    # "get_all_routers",
    # Infrastructure
    "BaseCacheOperation",
    "CacheHealthChecker",
    "CacheData",
    "CacheResult",
    "APIResponse",
    "HealthStatus",
    "CacheKey",
    "Timestamp",
    "CacheAPIException",
    "CacheNotFoundError",
    "CacheServiceUnavailableError",
    "CacheTimeoutError",
]
