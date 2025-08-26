"""
Custom types and type hints for fullon_cache_api.

This module provides type definitions used throughout the cache API
for better type safety and code documentation.
"""

from datetime import datetime
from typing import Any

# Cache response types
CacheData = dict[str, Any]
"""Type for cache data - generic dictionary containing cache information."""

CacheKey = str
"""Type for cache keys - string identifiers for cached data."""

CacheResult = CacheData | None
"""Type for cache operation results - may be None if data not found."""

# API response types
APIResponse = dict[str, Any]
"""Type for API responses - generic dictionary for REST responses."""

HealthStatus = dict[str, str | bool | int | float | None]
"""Type for health status responses containing status information."""

# Timestamp type for consistent time handling
Timestamp = datetime | float | int | None
"""Type for timestamps - can be datetime object, unix timestamp, or None."""
