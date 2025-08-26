"""
Custom exceptions for cache API operations.

This module provides a hierarchy of exceptions specific to cache operations,
all based on FastAPI's HTTPException for proper HTTP status code handling.
"""

from fastapi import HTTPException


class CacheAPIException(HTTPException):
    """Base exception for cache API operations."""

    pass


class CacheNotFoundError(CacheAPIException):
    """Raised when cache data is not found."""

    def __init__(self, detail: str = "Data not found in cache") -> None:
        """Initialize exception with 404 status code.

        Args:
            detail: Custom error message describing what was not found
        """
        super().__init__(status_code=404, detail=detail)


class CacheServiceUnavailableError(CacheAPIException):
    """Raised when cache service is unavailable."""

    def __init__(self, detail: str = "Cache service unavailable") -> None:
        """Initialize exception with 503 status code.

        Args:
            detail: Custom error message describing the service issue
        """
        super().__init__(status_code=503, detail=detail)


class CacheTimeoutError(CacheAPIException):
    """Raised when cache operation times out."""

    def __init__(self, detail: str = "Cache operation timeout") -> None:
        """Initialize exception with 408 status code.

        Args:
            detail: Custom error message describing the timeout
        """
        super().__init__(status_code=408, detail=detail)
