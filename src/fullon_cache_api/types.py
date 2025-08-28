"""
Custom types and type hints for FastAPI WebSocket cache operations.

This module provides type definitions used throughout the FastAPI WebSocket cache API
for better type safety and code documentation.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


# FastAPI WebSocket Message Types
class FastAPIWebSocketMessage(BaseModel):
    """Base model for FastAPI WebSocket messages."""

    request_id: str | None = None
    operation: str
    params: dict[str, Any] | None = None


class FastAPIWebSocketRequest(FastAPIWebSocketMessage):
    """Model for incoming FastAPI WebSocket requests."""

    pass


class FastAPIWebSocketResponse(BaseModel):
    """Model for outgoing FastAPI WebSocket responses."""

    request_id: str | None = None
    success: bool
    result: Any | None = None
    error: str | None = None
    error_code: str | None = None


class FastAPIStreamMessage(BaseModel):
    """Model for FastAPI WebSocket streaming messages."""

    type: str
    data: dict[str, Any]
    timestamp: float | None = None


class FastAPIWebSocketAPIResponse(BaseModel):
    """Model for structured FastAPI WebSocket API responses."""

    success: bool
    result: Any | None = None
    error: str | None = None
    error_code: str | None = None
    latency_ms: float | None = None
    cache_hit: bool | None = None


# Cache response types
CacheData = dict[str, Any]
"""Type for cache data - generic dictionary containing cache information."""

CacheKey = str
"""Type for cache keys - string identifiers for cached data."""

CacheResult = CacheData | None
"""Type for cache operation results - may be None if data not found."""

# Health status types
HealthStatus = dict[str, str | bool | int | float | None]
"""Type for health status responses containing status information."""

# Timestamp type for consistent time handling
Timestamp = datetime | float | int | None
"""Type for timestamps - can be datetime object, unix timestamp, or None."""
