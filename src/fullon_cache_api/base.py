"""
Base classes and utilities for fullon_cache_api.

This module provides the foundational classes that all cache operations
build upon, following LRRS principles.
"""

from abc import ABC, abstractmethod
from typing import Any

from fullon_log import get_component_logger  # type: ignore


class BaseCacheOperation(ABC):
    """Base class for all cache operations with logging and error handling."""

    def __init__(self) -> None:
        """Initialize cache operation with logging."""
        self.logger = get_component_logger("fullon.api.cache")

    @abstractmethod
    async def execute(self) -> Any:
        """Execute the cache operation.

        Returns:
            Any: Result of the cache operation

        Raises:
            CacheAPIException: When cache operation fails
        """
        pass


class CacheHealthChecker:
    """Health checking utilities for cache operations."""

    def __init__(self) -> None:
        """Initialize health checker with logging."""
        self.logger = get_component_logger("fullon.api.cache.health")

    async def check_cache_connectivity(self) -> dict[str, Any]:
        """Check if cache services are available.

        Returns:
            Dict[str, Any]: Health status information

        Raises:
            CacheServiceUnavailableError: When cache is unavailable
        """
        # Implementation will be added when cache operations are implemented
        # For now, return a placeholder to satisfy the interface
        return {"status": "healthy", "timestamp": None, "services": {}}
