"""
Router-specific exceptions for cache API operations.

This module provides specialized exceptions for router-level operations,
extending the base CacheAPIException hierarchy with router-specific error types.
"""

from ..exceptions import CacheAPIException


class InvalidParameterError(CacheAPIException):
    """Raised when router parameters are invalid or malformed."""

    def __init__(self, detail: str = "Invalid parameter format") -> None:
        """Initialize exception with 422 status code.

        Args:
            detail: Custom error message describing the parameter issue
        """
        super().__init__(status_code=422, detail=detail)


class CacheOperationError(CacheAPIException):
    """Raised when cache operation fails at router level."""

    def __init__(self, detail: str = "Cache operation failed") -> None:
        """Initialize exception with 500 status code.

        Args:
            detail: Custom error message describing the operation failure
        """
        super().__init__(status_code=500, detail=detail)
