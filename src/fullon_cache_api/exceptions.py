"""
Custom exceptions for FastAPI WebSocket cache operations.

This module provides a hierarchy of exceptions specific to FastAPI WebSocket cache operations,
designed for WebSocket error handling patterns.
"""


class CacheFastAPIWebSocketException(Exception):
    """Base exception for FastAPI WebSocket cache operations."""

    def __init__(self, message: str, error_code: str = "WEBSOCKET_ERROR") -> None:
        """Initialize WebSocket exception.

        Args:
            message: Error message describing the issue
            error_code: Specific error code for WebSocket clients
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class CacheNotFoundError(CacheFastAPIWebSocketException):
    """Raised when cache data is not found in WebSocket operations."""

    def __init__(self, detail: str = "Data not found in cache") -> None:
        """Initialize cache miss exception.

        Args:
            detail: Custom error message describing what was not found
        """
        super().__init__(detail, "CACHE_MISS")


class CacheServiceUnavailableError(CacheFastAPIWebSocketException):
    """Raised when cache service is unavailable for WebSocket operations."""

    def __init__(self, detail: str = "Cache service unavailable") -> None:
        """Initialize service unavailable exception.

        Args:
            detail: Custom error message describing the service issue
        """
        super().__init__(detail, "CACHE_UNAVAILABLE")


class CacheTimeoutError(CacheFastAPIWebSocketException):
    """Raised when cache operation times out in WebSocket context."""

    def __init__(self, detail: str = "Cache operation timeout") -> None:
        """Initialize timeout exception.

        Args:
            detail: Custom error message describing the timeout
        """
        super().__init__(detail, "TIMEOUT")


class FastAPIWebSocketConnectionError(CacheFastAPIWebSocketException):
    """Raised when FastAPI WebSocket connection fails."""

    def __init__(self, detail: str = "WebSocket connection error") -> None:
        """Initialize WebSocket connection exception.

        Args:
            detail: Custom error message describing the connection issue
        """
        super().__init__(detail, "WEBSOCKET_CONNECTION_ERROR")
