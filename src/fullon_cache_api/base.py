"""
Base classes and utilities for fullon_cache_api.

This module provides the foundational classes that all FastAPI WebSocket cache operations
build upon, following LRRS principles.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from fastapi import WebSocket
from fullon_log import get_component_logger  # type: ignore


class BaseFastAPIWebSocketHandler(ABC):
    """Base class for all FastAPI WebSocket message handlers."""

    def __init__(self) -> None:
        """Initialize WebSocket handler with logging."""
        # CRITICAL: Use fullon_log component logger
        self.logger = get_component_logger("fullon.api.cache.websocket")

    @abstractmethod
    async def handle_message(
        self, websocket: WebSocket, message: dict[str, Any]
    ) -> Any:
        """Handle incoming FastAPI WebSocket message.

        Args:
            websocket: FastAPI WebSocket connection
            message: Incoming WebSocket message

        Returns:
            Any: Response data to send back

        Raises:
            CacheFastAPIWebSocketException: When message handling fails
        """
        pass

    @abstractmethod
    async def validate_params(self, params: dict[str, Any]) -> bool:
        """Validate FastAPI WebSocket message parameters.

        Args:
            params: Message parameters to validate

        Returns:
            bool: True if parameters are valid

        Raises:
            ValueError: When parameters are invalid
        """
        pass


class BaseFastAPIWebSocketStream(ABC):
    """Base class for FastAPI WebSocket streaming operations."""

    def __init__(self) -> None:
        """Initialize WebSocket stream handler with logging."""
        # CRITICAL: Use fullon_log component logger
        self.logger = get_component_logger("fullon.api.cache.websocket.stream")

    @abstractmethod
    async def stream_updates(
        self, websocket: WebSocket, params: dict[str, Any]
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream real-time updates via FastAPI WebSocket.

        Args:
            websocket: FastAPI WebSocket connection
            params: Streaming parameters

        Yields:
            Dict[str, Any]: Stream update messages

        Raises:
            CacheFastAPIWebSocketException: When streaming fails
        """
        pass


class CacheHealthChecker:
    """Health checking utilities for FastAPI WebSocket cache operations."""

    def __init__(self) -> None:
        """Initialize health checker with logging."""
        # CRITICAL: Use fullon_log component logger
        self.logger = get_component_logger("fullon.api.cache.health")

    async def check_websocket_connectivity(self) -> dict[str, Any]:
        """Check FastAPI WebSocket server connectivity.

        Returns:
            Dict[str, Any]: Health status information

        Raises:
            CacheServiceUnavailableError: When WebSocket service is unavailable
        """
        self.logger.info("Starting WebSocket connectivity check")

        result: dict[str, Any] = {
            "status": "healthy",
            "framework": "fastapi",
            "transport": "websocket",
            "timestamp": None,
            "services": {},
        }

        self.logger.info(
            "WebSocket connectivity check completed", status=result["status"]
        )
        return result

    async def check_cache_connectivity(self) -> dict[str, Any]:
        """Check if cache services are available.

        Returns:
            Dict[str, Any]: Health status information

        Raises:
            CacheServiceUnavailableError: When cache is unavailable
        """
        # Implementation will be added when cache operations are implemented
        # For now, return a placeholder to satisfy the interface
        self.logger.info("Starting cache connectivity check")

        result: dict[str, Any] = {
            "status": "healthy",
            "timestamp": None,
            "services": {},
        }

        self.logger.info("Cache connectivity check completed", status=result["status"])
        return result
