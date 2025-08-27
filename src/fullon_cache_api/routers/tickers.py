"""
Ticker cache router for READ-ONLY ticker data operations.

This module provides FastAPI endpoints for retrieving ticker data from Redis cache
with comprehensive error handling, validation, and performance monitoring.
"""

import time
from datetime import UTC, datetime
from typing import Any
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, status
from fullon_cache import TickCache
from fullon_log import get_component_logger
from fullon_orm.models import Symbol

from ..dependencies.cache import get_tick_cache
from ..models.responses import (
    AllTickersResponse,
    HealthResponse,
    TickerResponse,
)
from .base import (
    handle_cache_error,
    log_cache_operation,
    validate_exchange_symbol_format,
)

logger = get_component_logger("fullon.api.cache.tickers")
router = APIRouter(prefix="/tickers", tags=["Ticker Cache"])


def _create_symbol_object(symbol_str: str) -> Symbol:
    """Create Symbol object from symbol string."""
    parts = symbol_str.split("/")
    return Symbol(symbol=symbol_str, cat_ex_id=1, base=parts[0], quote=parts[1])


def _format_tick_data(tick: Any) -> dict[str, Any] | None:
    """Format tick data for API response."""
    if not tick:
        return None

    return {
        "bid": float(tick.bid) if tick.bid else None,
        "ask": float(tick.ask) if tick.ask else None,
        "last": float(tick.last) if tick.last else None,
        "price": float(tick.price),
        "volume": float(tick.volume),
        "high": None,  # Not available in current Tick model
        "low": None,  # Not available in current Tick model
        "change": None,  # Calculate if needed
        "change_percent": None,  # Calculate if needed
        "timestamp": datetime.fromtimestamp(tick.time, tz=UTC).isoformat(),
    }


def _is_stale_data(tick: Any, stale_threshold_seconds: int = 300) -> bool:
    """Check if tick data is stale (older than threshold)."""
    if not tick or not hasattr(tick, "time"):
        return True

    current_time = time.time()
    return (current_time - tick.time) > stale_threshold_seconds


@router.get("/{exchange}/{symbol}", response_model=TickerResponse)
async def get_ticker(exchange: str, symbol: str) -> TickerResponse:
    """
    Get ticker data from cache for specific exchange/symbol pair.

    Args:
        exchange: Exchange name (e.g., 'binance')
        symbol: Trading pair symbol (e.g., 'BTC/USDT') - URL encoded

    Returns:
        TickerResponse with ticker data and metadata

    Raises:
        HTTPException: 404 if ticker not found, 422 for invalid parameters
    """
    # URL decode symbol
    symbol = unquote(symbol)

    # Validate parameters FIRST before any cache operations
    try:
        validated_exchange, validated_symbol = validate_exchange_symbol_format(
            exchange, symbol
        )
    except Exception as e:
        logger.warning(
            "Invalid ticker request parameters",
            exchange=exchange,
            symbol=symbol,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid parameters: {str(e)}",
        ) from e

    # Now get cache after validation
    try:
        cache_gen = get_tick_cache()
        cache = await cache_gen.__anext__()
    except Exception as e:
        logger.error(
            "Failed to get cache connection",
            exchange=validated_exchange,
            symbol=validated_symbol,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache service unavailable",
        ) from e

    # Perform cache operation with logging
    async with log_cache_operation(
        "get_ticker", exchange=validated_exchange, symbol=validated_symbol
    ):
        try:
            # Clean up the generator
            try:
                await cache_gen.__anext__()
            except StopAsyncIteration:
                pass  # Expected when generator is exhausted

            symbol_obj = _create_symbol_object(validated_symbol)
            tick = await cache.get_ticker(symbol_obj, validated_exchange)

            if not tick:
                logger.info(
                    "Ticker not found in cache",
                    exchange=validated_exchange,
                    symbol=validated_symbol,
                    cache_hit=False,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Ticker {validated_symbol} not found in {validated_exchange} cache",
                )

            # Format response data
            ticker_data = _format_tick_data(tick)
            if not ticker_data:
                # This should not happen since we already checked tick exists, but for safety
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Ticker {validated_symbol} data invalid in {validated_exchange} cache",
                )

            is_stale = _is_stale_data(tick)
            cached_at = datetime.fromtimestamp(tick.time, tz=UTC)

            logger.info(
                "Ticker retrieved successfully",
                exchange=validated_exchange,
                symbol=validated_symbol,
                cache_hit=True,
                stale=is_stale,
            )

            return TickerResponse(
                success=True,
                timestamp=datetime.utcnow(),
                exchange=validated_exchange,
                symbol=validated_symbol,
                ticker_data=ticker_data,
                cached_at=cached_at,
                cache_hit=True,
                stale=is_stale,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to get ticker from cache",
                exchange=validated_exchange,
                symbol=validated_symbol,
                error=str(e),
                error_type=type(e).__name__,
            )
            await handle_cache_error(
                "get_ticker",
                e,
                {"exchange": validated_exchange, "symbol": validated_symbol},
            )
            # This should never be reached due to handle_cache_error raising
            raise  # pragma: no cover


@router.get("/{exchange}", response_model=AllTickersResponse)
async def get_all_tickers(
    exchange: str, cache: TickCache = Depends(get_tick_cache)
) -> AllTickersResponse:
    """
    Get all ticker data for specific exchange.

    Args:
        exchange: Exchange name (e.g., 'binance')
        cache: TickCache dependency injection

    Returns:
        AllTickersResponse with list of all tickers
    """
    if not exchange or not exchange.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Exchange cannot be empty",
        )

    exchange = exchange.strip()

    async with log_cache_operation("get_all_tickers", exchange=exchange):
        try:
            # Note: This method might not exist in current TickCache
            # Using a placeholder for TDD - will need to implement or use alternative approach
            tickers_data: list[dict[str, Any]] = []
            cached_at = datetime.utcnow()

            # Mock implementation - in real implementation, might iterate through known symbols
            # or use a different cache method
            logger.warning(
                "get_all_tickers not yet fully implemented", exchange=exchange
            )

            return AllTickersResponse(
                success=True,
                timestamp=datetime.utcnow(),
                exchange=exchange,
                tickers=tickers_data,
                count=len(tickers_data),
                cached_at=cached_at,
            )

        except Exception as e:
            await handle_cache_error("get_all_tickers", e, {"exchange": exchange})
            # This line should never be reached due to handle_cache_error raising
            raise  # pragma: no cover


@router.get("/{exchange}/active", response_model=list[str])
async def get_active_tickers(
    exchange: str, cache: TickCache = Depends(get_tick_cache)
) -> list[str]:
    """
    Get list of active ticker symbols for exchange.

    Args:
        exchange: Exchange name (e.g., 'binance')
        cache: TickCache dependency injection

    Returns:
        List of active ticker symbol strings
    """
    if not exchange or not exchange.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Exchange cannot be empty",
        )

    exchange = exchange.strip()

    async with log_cache_operation("get_active_tickers", exchange=exchange):
        try:
            # Note: This method might not exist in current TickCache
            # Using placeholder for TDD
            active_symbols: list[str] = []

            logger.warning(
                "get_active_tickers not yet fully implemented", exchange=exchange
            )

            return active_symbols

        except Exception as e:
            await handle_cache_error("get_active_tickers", e, {"exchange": exchange})
            # This line should never be reached due to handle_cache_error raising
            raise  # pragma: no cover


@router.get("/health", response_model=HealthResponse)
async def ticker_cache_health(
    cache: TickCache = Depends(get_tick_cache),
) -> HealthResponse:
    """
    Check ticker cache health and connection status.

    Returns:
        HealthResponse with health status information
    """
    async with log_cache_operation("ticker_health_check"):
        try:
            # Test cache connection
            ping_result = await cache.ping()
            # Note: test() method should be available but might not be in current implementation
            connection_test = ping_result == "pong"

            status_value = "healthy" if connection_test else "unhealthy"

            logger.info(
                "Ticker cache health check completed",
                status=status_value,
                redis_connected=connection_test,
            )

            return HealthResponse(
                success=True,
                timestamp=datetime.utcnow(),
                service="fullon_cache_api_tickers",
                status=status_value,
                version="0.1.0",
                cache_status={
                    "redis": "connected" if connection_test else "disconnected",
                    "ticker_cache": status_value,
                },
            )

        except Exception as e:
            logger.error(
                "Ticker cache health check failed",
                error=str(e),
                error_type=type(e).__name__,
            )

            return HealthResponse(
                success=True,
                timestamp=datetime.utcnow(),
                service="fullon_cache_api_tickers",
                status="unhealthy",
                version="0.1.0",
                cache_status={
                    "redis": "disconnected",
                    "ticker_cache": "unhealthy",
                    "error": str(e),
                },
            )


@router.get("/performance", response_model=dict[str, Any])
async def ticker_performance_metrics(
    cache: TickCache = Depends(get_tick_cache),
) -> dict[str, Any]:
    """
    Get ticker cache performance metrics.

    Returns:
        Dictionary with performance statistics
    """
    async with log_cache_operation("get_ticker_performance"):
        try:
            # Note: This method might not exist in current TickCache
            # Using placeholder metrics for TDD
            metrics = {
                "success": True,
                "timestamp": datetime.utcnow().isoformat(),
                "cache_hits": 0,
                "cache_misses": 0,
                "hit_ratio": 0.0,
                "avg_latency_ms": 0.0,
                "total_requests": 0,
                "last_updated": datetime.utcnow().isoformat(),
            }

            logger.warning("Ticker performance metrics not yet fully implemented")

            return metrics

        except Exception as e:
            logger.error(
                "Failed to get ticker performance metrics",
                error=str(e),
                error_type=type(e).__name__,
            )

            return {
                "success": False,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }
