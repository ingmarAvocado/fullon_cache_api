"""
FastAPI WebSocket message models for fullon_cache_api.

This module defines the complete Pydantic model system for FastAPI WebSocket
communication, including request/response validation, streaming messages,
and error handling with fullon_log integration.

All models are optimized for FastAPI WebSocket JSON serialization and
real-time messaging patterns.
"""

import time
import uuid
from typing import Any

from fullon_log import get_component_logger  # type: ignore
from pydantic import BaseModel, ConfigDict, Field, field_validator

# Initialize component logger for message models
logger = get_component_logger("fullon.api.cache.models.messages")

# Define allowed operations for FastAPI WebSocket validation
ALLOWED_OPERATIONS: set[str] = {
    # Core operations
    "ping",
    "health_check",
    # Ticker FastAPI WebSocket operations
    "get_ticker",
    "get_all_tickers",
    "stream_tickers",
    # Account FastAPI WebSocket operations
    "get_user_positions",
    "get_user_balances",
    "get_account_status",
    "stream_user_positions",
    "stream_user_balances",
    # Order FastAPI WebSocket operations
    "get_order_status",
    "get_queue_length",
    "stream_order_queue",
    # Bot FastAPI WebSocket operations
    "is_blocked",
    "get_bots",
    "stream_bot_status",
    # Trade FastAPI WebSocket operations
    "get_trades",
    "get_trade_status",
    "stream_trade_updates",
    # OHLCV FastAPI WebSocket operations
    "get_latest_ohlcv_bars",
    "stream_ohlcv_updates",
    # Process FastAPI WebSocket operations
    "get_active_processes",
    "get_system_health",
    "stream_process_health",
}


class CacheRequest(BaseModel):
    """FastAPI WebSocket request message for cache operations."""

    request_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique request identifier",
    )
    operation: str = Field(..., description="Cache operation to perform")
    params: dict[str, Any] = Field(
        default_factory=dict, description="Operation parameters"
    )
    timestamp: float = Field(default_factory=time.time, description="Request timestamp")

    @field_validator("operation")
    @classmethod
    def validate_operation(cls, v: str) -> str:
        """Validate FastAPI WebSocket operation names."""
        if v not in ALLOWED_OPERATIONS:
            logger.error(
                "Invalid FastAPI WebSocket operation attempted",
                operation=v,
                allowed_operations=list(ALLOWED_OPERATIONS),
            )
            raise ValueError(f"Invalid FastAPI WebSocket operation: {v}")

        logger.debug("FastAPI WebSocket operation validated", operation=v)
        return v

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        logger.debug(
            "FastAPI WebSocket request created",
            request_id=self.request_id,
            operation=self.operation,
            params_count=len(self.params),
        )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "request_id": "123e4567-e89b-12d3-a456-426614174000",
                "operation": "get_ticker",
                "params": {"exchange": "binance", "symbol": "BTC/USDT"},
                "timestamp": 1627846261.75,
            }
        }
    )


class CacheResponse(BaseModel):
    """FastAPI WebSocket response message for cache operations."""

    request_id: str = Field(..., description="Matching request ID")
    success: bool = Field(..., description="Operation success status")
    result: Any | None = Field(None, description="Operation result data")
    error: str | None = Field(None, description="Error message if failed")
    error_code: str | None = Field(None, description="FastAPI WebSocket error code")
    timestamp: float = Field(
        default_factory=time.time, description="Response timestamp"
    )
    latency_ms: float | None = Field(
        None, description="Operation latency in milliseconds"
    )

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        logger.debug(
            "FastAPI WebSocket response created",
            request_id=self.request_id,
            success=self.success,
            has_result=self.result is not None,
            has_error=self.error is not None,
        )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "request_id": "123e4567-e89b-12d3-a456-426614174000",
                "success": True,
                "result": {
                    "symbol": "BTC/USDT",
                    "exchange": "binance",
                    "price": 45000.0,
                    "volume": 1234.56,
                },
                "timestamp": 1627846261.85,
                "latency_ms": 15.2,
            }
        }
    )


class StreamMessage(BaseModel):
    """FastAPI WebSocket streaming message for real-time updates."""

    type: str = Field(..., description="Stream message type")
    data: dict[str, Any] = Field(..., description="Stream data payload")
    timestamp: float = Field(
        default_factory=time.time, description="Stream message timestamp"
    )
    stream_id: str | None = Field(None, description="Stream identifier")
    sequence: int | None = Field(None, description="Message sequence number")

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        logger.debug(
            "FastAPI WebSocket stream message created",
            type=self.type,
            stream_id=self.stream_id,
            sequence=self.sequence,
        )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "ticker_update",
                "data": {
                    "symbol": "BTC/USDT",
                    "exchange": "binance",
                    "price": 45100.0,
                    "volume": 1245.67,
                    "change_24h": 2.5,
                },
                "timestamp": 1627846261.95,
                "stream_id": "tickers_binance",
                "sequence": 12345,
            }
        }
    )


class ErrorMessage(BaseModel):
    """FastAPI WebSocket error message for connection/protocol errors."""

    request_id: str | None = Field(None, description="Related request ID")
    error: str = Field(..., description="Error description")
    error_code: str = Field(..., description="FastAPI WebSocket error code")
    timestamp: float = Field(default_factory=time.time, description="Error timestamp")
    details: dict[str, Any] | None = Field(None, description="Additional error details")

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        logger.warning(
            "FastAPI WebSocket error message created",
            error_code=self.error_code,
            request_id=self.request_id,
            error=self.error,
        )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "request_id": "123e4567-e89b-12d3-a456-426614174000",
                "error": "Cache operation failed",
                "error_code": "CACHE_UNAVAILABLE",
                "timestamp": 1627846261.75,
                "details": {"service": "redis", "timeout": "5s"},
            }
        }
    )


# Error code constants for FastAPI WebSocket operations
class ErrorCodes:
    """Standard error codes for FastAPI WebSocket cache operations."""

    # Connection errors
    CONNECTION_FAILED = "CONNECTION_FAILED"
    CONNECTION_TIMEOUT = "CONNECTION_TIMEOUT"
    CONNECTION_LOST = "CONNECTION_LOST"

    # Cache errors
    CACHE_MISS = "CACHE_MISS"
    CACHE_UNAVAILABLE = "CACHE_UNAVAILABLE"
    CACHE_TIMEOUT = "CACHE_TIMEOUT"

    # Validation errors
    INVALID_PARAMS = "INVALID_PARAMS"
    INVALID_OPERATION = "INVALID_OPERATION"
    MALFORMED_MESSAGE = "MALFORMED_MESSAGE"

    # System errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"


def create_error_response(
    request_id: str | None,
    error_code: str,
    error_message: str,
    details: dict[str, Any] | None = None,
) -> ErrorMessage:
    """Factory function to create standardized FastAPI WebSocket error responses."""
    logger.info(
        "Creating standardized FastAPI WebSocket error response",
        request_id=request_id,
        error_code=error_code,
        error_message=error_message,
    )

    return ErrorMessage(
        request_id=request_id,
        error=error_message,
        error_code=error_code,
        details=details,
    )


def create_success_response(
    request_id: str, result: Any, latency_ms: float | None = None
) -> CacheResponse:
    """Factory function to create standardized FastAPI WebSocket success responses."""
    logger.info(
        "Creating standardized FastAPI WebSocket success response",
        request_id=request_id,
        has_result=result is not None,
        latency_ms=latency_ms,
    )

    return CacheResponse(
        request_id=request_id, success=True, result=result, latency_ms=latency_ms
    )
