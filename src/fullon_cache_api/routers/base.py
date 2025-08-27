"""
Base router utilities and patterns for consistent FastAPI router implementation.

This module provides foundational utilities for all cache router implementations,
ensuring consistent validation, error handling, logging, and response formatting.
"""

import time
from contextlib import asynccontextmanager
from typing import Any, Optional

from fullon_log import get_component_logger

from ..exceptions import (
    CacheNotFoundError,
    CacheServiceUnavailableError,
    CacheTimeoutError,
)
from .exceptions import InvalidParameterError

logger = get_component_logger("fullon.api.cache.router")


def validate_user_id(user_id: str) -> str:
    """
    Validate user ID parameter format and sanitization.

    Args:
        user_id: User identifier string

    Returns:
        Sanitized user ID if valid

    Raises:
        InvalidParameterError: If user ID is invalid
    """
    if not user_id or not user_id.strip():
        raise InvalidParameterError("User ID cannot be empty")

    # Sanitize whitespace
    user_id = user_id.strip()

    # Check for minimum/maximum length
    if len(user_id) < 1 or len(user_id) > 100:
        raise InvalidParameterError("User ID must be between 1 and 100 characters")

    # Check for malicious patterns
    dangerous_patterns = [
        ";",
        "--",
        "/*",
        "*/",
        "drop",
        "delete",
        "insert",
        "update",
        "select",
        "<script",
        "</script",
        "javascript:",
        "data:",
        "vbscript:",
        "onload=",
        "onerror=",
        "\x00",
        "\r",
        "\n",
        "../",
        "./",
        "\\",
        "'",
        '"',
    ]

    user_id_lower = user_id.lower()
    for pattern in dangerous_patterns:
        if pattern in user_id_lower:
            raise InvalidParameterError(
                f"User ID contains invalid characters or patterns"
            )

    # Alphanumeric plus some safe characters only
    allowed_chars = set(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-@."
    )
    if not all(c in allowed_chars for c in user_id):
        raise InvalidParameterError("User ID contains invalid characters")

    return user_id


def validate_exchange_symbol_format(exchange: str, symbol: str) -> tuple[str, str]:
    """
    Validate exchange and symbol parameter format.

    Args:
        exchange: Exchange name (e.g., 'binance')
        symbol: Trading pair symbol (e.g., 'BTC/USDT')

    Returns:
        Tuple of (exchange, symbol) if valid

    Raises:
        InvalidParameterError: If parameters are invalid
    """
    if not exchange or not exchange.strip():
        raise InvalidParameterError("Exchange cannot be empty")

    if not symbol or not symbol.strip():
        raise InvalidParameterError("Symbol cannot be empty")

    # Symbol must contain exactly one '/' separator
    if "/" not in symbol:
        raise InvalidParameterError("Symbol must contain '/' separator")

    parts = symbol.split("/")
    if len(parts) != 2:
        raise InvalidParameterError("Symbol cannot contain multiple '/' separators")

    base, quote = parts
    if not base or not base.strip():
        raise InvalidParameterError("Symbol base cannot be empty")

    if not quote or not quote.strip():
        raise InvalidParameterError("Symbol quote cannot be empty")

    return exchange.strip(), symbol.strip()


async def handle_cache_error(
    operation: str, error: Exception, context: Optional[dict[str, Any]] = None
) -> None:
    """
    Standardized cache error handling and logging.

    Args:
        operation: Cache operation name (e.g., 'get_ticker')
        error: Original exception that occurred
        context: Additional context for logging (exchange, symbol, etc.)

    Raises:
        Appropriate CacheAPIException based on error type
    """
    context = context or {}
    error_message = str(error)

    # Log the error with full context
    logger.error(
        f"Cache {operation} failed",
        operation=operation,
        error=error_message,
        error_type=type(error).__name__,
        **context,
    )

    # Map common error types to appropriate HTTP exceptions
    if (
        "not found" in error_message.lower()
        or "does not exist" in error_message.lower()
    ):
        raise CacheNotFoundError(f"Cache data not found for {operation}")

    elif isinstance(error, TimeoutError) or "timeout" in error_message.lower():
        raise CacheTimeoutError(f"Cache operation timeout for {operation}")

    elif (
        isinstance(error, (ConnectionError, OSError))
        or "connection" in error_message.lower()
    ):
        raise CacheServiceUnavailableError(f"Cache service unavailable for {operation}")

    else:
        # Generic service unavailable for unhandled errors
        raise CacheServiceUnavailableError(f"Cache service error for {operation}")


def create_cache_response(
    data: Optional[dict[str, Any]], operation: str
) -> dict[str, Any]:
    """
    Create consistent cache response format.

    Args:
        data: Cache operation result data (None for cache miss)
        operation: Cache operation name

    Returns:
        Standardized response dictionary
    """
    return {
        "success": True,
        "operation": operation,
        "data": data,
        "timestamp": time.time(),
    }


@asynccontextmanager
async def log_cache_operation(operation: str, **context: Any) -> Any:
    """
    Context manager for consistent cache operation logging with performance metrics.

    Args:
        operation: Cache operation name
        **context: Additional logging context (exchange, symbol, etc.)
    """
    start_time = time.time()
    logger.info(f"Cache {operation} started", operation=operation, **context)

    try:
        yield
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Cache {operation} completed",
            operation=operation,
            latency_ms=duration_ms,
            status="success",
            **context,
        )
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            f"Cache {operation} failed",
            operation=operation,
            error=str(e),
            error_type=type(e).__name__,
            latency_ms=duration_ms,
            status="error",
            **context,
        )
        raise
