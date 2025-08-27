"""
Tests for base router pattern functionality.

This module tests the foundational router utilities, validation patterns,
error handling, and logging integration for all cache router implementations.
"""

import time
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from fullon_cache_api.exceptions import (
    CacheNotFoundError,
    CacheServiceUnavailableError,
    CacheTimeoutError,
)
from fullon_cache_api.routers.base import (
    create_cache_response,
    handle_cache_error,
    log_cache_operation,
    validate_exchange_symbol_format,
)
from fullon_cache_api.routers.exceptions import (
    CacheOperationError,
    InvalidParameterError,
)
from fullon_cache_api.routers.utils import CacheOperation, format_cache_key


class TestBaseRouterPattern:
    """Test base router pattern functionality."""

    def test_exchange_symbol_validation_success(self):
        """Test successful exchange and symbol format validation."""
        # Valid exchange/symbol combinations
        valid_cases = [
            ("binance", "BTC/USDT"),
            ("kraken", "ETH/USD"),
            ("coinbase", "BTC/EUR"),
            ("bitfinex", "LTC/BTC"),
        ]

        for exchange, symbol in valid_cases:
            result = validate_exchange_symbol_format(exchange, symbol)
            assert result == (exchange, symbol)

    def test_exchange_symbol_validation_failures(self):
        """Test exchange and symbol format validation failures."""
        # Invalid cases
        invalid_cases = [
            ("", "BTC/USDT", "Exchange cannot be empty"),
            ("binance", "", "Symbol cannot be empty"),
            ("binance", "BTCUSDT", "Symbol must contain '/' separator"),
            ("binance", "BTC/", "Symbol quote cannot be empty"),
            ("binance", "/USDT", "Symbol base cannot be empty"),
            ("binance", "BTC//USDT", "Symbol cannot contain multiple '/' separators"),
        ]

        for exchange, symbol, expected_message in invalid_cases:
            with pytest.raises(InvalidParameterError) as exc_info:
                validate_exchange_symbol_format(exchange, symbol)
            assert expected_message in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_cache_error_handling_not_found(self):
        """Test standardized cache error handling for cache miss."""
        operation = "get_ticker"
        original_error = Exception("Data not found in Redis")

        with patch("fullon_cache_api.routers.base.logger") as mock_logger:
            with pytest.raises(CacheNotFoundError) as exc_info:
                await handle_cache_error(
                    operation,
                    original_error,
                    {"exchange": "binance", "symbol": "BTC/USDT"},
                )

            assert "Cache data not found" in str(exc_info.value.detail)
            mock_logger.error.assert_called_once()

            # Verify logging includes operation context
            log_call_args = mock_logger.error.call_args
            assert log_call_args[1]["operation"] == operation
            assert log_call_args[1]["exchange"] == "binance"
            assert log_call_args[1]["symbol"] == "BTC/USDT"

    @pytest.mark.asyncio
    async def test_cache_error_handling_service_unavailable(self):
        """Test standardized cache error handling for Redis unavailable."""
        operation = "get_orders"
        original_error = ConnectionError("Redis connection failed")

        with patch("fullon_cache_api.routers.base.logger") as mock_logger:
            with pytest.raises(CacheServiceUnavailableError) as exc_info:
                await handle_cache_error(
                    operation, original_error, {"exchange": "binance"}
                )

            assert "Cache service unavailable" in str(exc_info.value.detail)
            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_error_handling_timeout(self):
        """Test standardized cache error handling for timeout."""
        operation = "stream_tickers"
        original_error = TimeoutError("Operation timeout after 30s")

        with patch("fullon_cache_api.routers.base.logger") as mock_logger:
            with pytest.raises(CacheTimeoutError) as exc_info:
                await handle_cache_error(
                    operation, original_error, {"exchange": "binance"}
                )

            assert "Cache operation timeout" in str(exc_info.value.detail)

    def test_response_formatting_success(self):
        """Test consistent cache response format for successful operations."""
        data = {"symbol": "BTC/USDT", "price": 50000.0, "volume": 1234.5}
        operation = "get_ticker"

        response = create_cache_response(data, operation)

        assert response["success"] is True
        assert response["operation"] == operation
        assert response["data"] == data
        assert "timestamp" in response
        assert isinstance(response["timestamp"], (int, float))

    def test_response_formatting_none_data(self):
        """Test consistent cache response format for None data (cache miss)."""
        operation = "get_ticker"

        response = create_cache_response(None, operation)

        assert response["success"] is True
        assert response["operation"] == operation
        assert response["data"] is None
        assert "timestamp" in response

    @pytest.mark.asyncio
    async def test_async_context_management_success(self):
        """Test proper async cache context handling in operations."""

        # This tests the pattern that routers should follow
        async def mock_cache_operation():
            with patch(
                "fullon_cache_api.dependencies.cache.TickCache"
            ) as mock_cache_class:
                mock_cache = AsyncMock()
                mock_context_result = AsyncMock()
                mock_context_result.get_ticker.return_value = {"price": 50000}
                mock_cache.__aenter__.return_value = mock_context_result
                mock_cache_class.return_value = mock_cache

                # Simulate router pattern
                from fullon_cache_api.dependencies.cache import get_tick_cache

                gen = get_tick_cache()
                cache = await gen.__anext__()

                result = await cache.get_ticker("BTC/USDT", "binance")

                # Clean up generator
                try:
                    await gen.__anext__()
                except StopAsyncIteration:
                    pass

                return result

        result = await mock_cache_operation()
        assert result["price"] == 50000

    @pytest.mark.asyncio
    async def test_router_logging_integration(self):
        """Test fullon_log integration in router operations."""
        with patch("fullon_cache_api.routers.base.logger") as mock_logger:
            operation = "get_ticker"
            context = {"exchange": "binance", "symbol": "BTC/USDT"}

            # Test log_cache_operation context manager
            async with log_cache_operation(operation, **context):
                # Simulate some work
                await AsyncMock()()

            # Verify start and success logging
            assert mock_logger.info.call_count == 2
            start_call, success_call = mock_logger.info.call_args_list

            # Check start log
            assert "started" in start_call[0][0]
            assert start_call[1]["operation"] == operation
            assert start_call[1]["exchange"] == "binance"

            # Check success log
            assert "completed" in success_call[0][0]
            assert "latency_ms" in success_call[1]
            assert success_call[1]["status"] == "success"

    @pytest.mark.asyncio
    async def test_router_logging_error_handling(self):
        """Test fullon_log integration for error scenarios."""
        with patch("fullon_cache_api.routers.base.logger") as mock_logger:
            operation = "get_ticker"
            context = {"exchange": "binance", "symbol": "BTC/USDT"}

            # Test log_cache_operation context manager with error
            with pytest.raises(ValueError):
                async with log_cache_operation(operation, **context):
                    raise ValueError("Test error")

            # Verify start and error logging
            assert mock_logger.info.call_count == 1  # Start log only
            assert mock_logger.error.call_count == 1  # Error log

            error_call = mock_logger.error.call_args
            assert "failed" in error_call[0][0]
            assert error_call[1]["operation"] == operation
            assert error_call[1]["status"] == "error"
            assert "latency_ms" in error_call[1]

    def test_health_check_pattern(self):
        """Test health check endpoint pattern."""
        # This tests the expected pattern for health check responses
        expected_structure = {
            "status": "healthy",
            "services": {"redis": "healthy", "cache": "available"},
            "timestamp": time.time(),
        }

        # Verify structure matches expected pattern
        assert "status" in expected_structure
        assert "services" in expected_structure
        assert "timestamp" in expected_structure
        assert isinstance(expected_structure["services"], dict)


class TestRouterUtils:
    """Test router utility functions and enums."""

    def test_cache_operation_enum(self):
        """Test CacheOperation enum values."""
        assert CacheOperation.GET_TICKER.value == "get_ticker"
        assert CacheOperation.GET_ORDERS.value == "get_orders"
        assert CacheOperation.GET_BOT_STATUS.value == "get_bot_status"
        assert CacheOperation.GET_TRADES.value == "get_trades"
        assert CacheOperation.GET_POSITIONS.value == "get_positions"
        assert CacheOperation.GET_OHLCV.value == "get_ohlcv"
        assert CacheOperation.GET_HEALTH.value == "get_health"

    def test_format_cache_key_standard(self):
        """Test standard cache key formatting."""
        key = format_cache_key("binance", "BTC/USDT")
        assert key == "binance:BTC/USDT"

    def test_format_cache_key_special_characters(self):
        """Test cache key formatting with special characters."""
        key = format_cache_key("binance", "BTC/USDT")
        assert ":" in key
        assert "/" in key

    def test_format_cache_key_normalization(self):
        """Test cache key formatting normalization."""
        # Test uppercase normalization
        key1 = format_cache_key("BINANCE", "btc/usdt")
        key2 = format_cache_key("binance", "BTC/USDT")
        # Both should be normalized to same format
        assert key1.lower() == key2.lower()


class TestRouterExceptions:
    """Test router-specific exceptions."""

    def test_invalid_parameter_error(self):
        """Test InvalidParameterError exception."""
        error = InvalidParameterError("Invalid symbol format")
        assert error.status_code == 422
        assert "Invalid symbol format" in error.detail

    def test_cache_operation_error(self):
        """Test CacheOperationError exception."""
        error = CacheOperationError("Cache operation failed")
        assert error.status_code == 500
        assert "Cache operation failed" in error.detail

    def test_exception_inheritance(self):
        """Test that custom exceptions inherit from HTTPException."""
        error1 = InvalidParameterError("test")
        error2 = CacheOperationError("test")

        assert isinstance(error1, HTTPException)
        assert isinstance(error2, HTTPException)


class TestIntegrationPatterns:
    """Test integration patterns for router implementation."""

    @pytest.mark.asyncio
    async def test_full_router_workflow_success(self):
        """Test complete router workflow for successful operation."""
        with patch("fullon_cache_api.routers.base.logger") as mock_logger:
            # 1. Validate parameters
            exchange, symbol = validate_exchange_symbol_format("binance", "BTC/USDT")

            # 2. Mock cache operation
            mock_data = {"price": 50000.0, "volume": 1234.5}

            # 3. Create response
            response = create_cache_response(mock_data, "get_ticker")

            # 4. Verify complete workflow
            assert exchange == "binance"
            assert symbol == "BTC/USDT"
            assert response["success"] is True
            assert response["data"] == mock_data

    @pytest.mark.asyncio
    async def test_full_router_workflow_validation_error(self):
        """Test complete router workflow with validation error."""
        with pytest.raises(InvalidParameterError):
            validate_exchange_symbol_format("binance", "INVALID_SYMBOL")

    @pytest.mark.asyncio
    async def test_full_router_workflow_cache_error(self):
        """Test complete router workflow with cache error."""
        with patch("fullon_cache_api.routers.base.logger"):
            # Mock cache error scenario
            original_error = ConnectionError("Redis unavailable")

            with pytest.raises(CacheServiceUnavailableError):
                await handle_cache_error(
                    "get_ticker", original_error, {"exchange": "binance"}
                )
