"""FastAPI routers for cache endpoints.

This module provides the base router patterns and utilities for implementing
consistent cache endpoint routers across all cache operation types.
"""

from .base import (
    create_cache_response,
    handle_cache_error,
    log_cache_operation,
    validate_exchange_symbol_format,
)
from .exceptions import CacheOperationError, InvalidParameterError
from .utils import CacheOperation, format_cache_key, normalize_exchange_name

__all__ = [
    "create_cache_response",
    "handle_cache_error",
    "log_cache_operation",
    "validate_exchange_symbol_format",
    "CacheOperationError",
    "InvalidParameterError",
    "CacheOperation",
    "format_cache_key",
    "normalize_exchange_name",
]
