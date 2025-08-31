"""
Comprehensive test suite for Pydantic message models.

Tests all FastAPI WebSocket message models, data models, and validation
with fullon_log integration testing.
"""

from decimal import Decimal
from unittest.mock import patch

import pytest
from fullon_cache_api.models.data import (
    BalanceData,
    BotData,
    HealthData,
    OHLCVData,
    OrderData,
    PositionData,
    ProcessData,
    TickerData,
    TradeData,
)
from fullon_cache_api.models.messages import (
    ALLOWED_OPERATIONS,
    CacheRequest,
    CacheResponse,
    ErrorCodes,
    ErrorMessage,
    StreamMessage,
    create_error_response,
    create_success_response,
)
from pydantic import ValidationError


class TestCacheRequest:
    """Test FastAPI WebSocket request message model."""

    def test_cache_request_creation_with_defaults(self):
        """Test CacheRequest creation with default values."""
        request = CacheRequest(operation="get_ticker")

        assert request.operation == "get_ticker"
        assert isinstance(request.request_id, str)
        assert isinstance(request.params, dict)
        assert isinstance(request.timestamp, float)
        assert len(request.params) == 0

    def test_cache_request_creation_with_params(self):
        """Test CacheRequest creation with custom parameters."""
        params = {"exchange": "binance", "symbol": "BTC/USDT"}
        request = CacheRequest(
            operation="get_ticker", params=params, request_id="custom-id"
        )

        assert request.operation == "get_ticker"
        assert request.request_id == "custom-id"
        assert request.params == params

    def test_cache_request_invalid_operation(self):
        """Test CacheRequest with invalid operation."""
        with pytest.raises(ValidationError) as exc_info:
            CacheRequest(operation="invalid_operation")

        assert "Invalid FastAPI WebSocket operation" in str(exc_info.value)

    @pytest.mark.parametrize(
        "operation",
        [
            "ping",
            "health_check",
            "get_ticker",
            "get_all_tickers",
            "stream_tickers",
            "get_user_positions",
            "is_blocked",
        ],
    )
    def test_cache_request_valid_operations(self, operation):
        """Test CacheRequest with all valid operations."""
        request = CacheRequest(operation=operation)
        assert request.operation == operation

    def test_cache_request_logging(self):
        """Test CacheRequest logging integration."""
        with patch("fullon_cache_api.models.messages.logger") as mock_logger:
            CacheRequest(operation="ping")
            mock_logger.debug.assert_called()


class TestCacheResponse:
    """Test FastAPI WebSocket response message model."""

    def test_cache_response_success(self):
        """Test successful CacheResponse creation."""
        result = {"symbol": "BTC/USDT", "price": 45000.0}
        response = CacheResponse(
            request_id="test-id", success=True, result=result, latency_ms=15.2
        )

        assert response.request_id == "test-id"
        assert response.success is True
        assert response.result == result
        assert response.latency_ms == 15.2
        assert response.error is None
        assert response.error_code is None

    def test_cache_response_error(self):
        """Test error CacheResponse creation."""
        response = CacheResponse(
            request_id="test-id",
            success=False,
            error="Cache unavailable",
            error_code="CACHE_UNAVAILABLE",
        )

        assert response.request_id == "test-id"
        assert response.success is False
        assert response.error == "Cache unavailable"
        assert response.error_code == "CACHE_UNAVAILABLE"
        assert response.result is None

    def test_cache_response_logging(self):
        """Test CacheResponse logging integration."""
        with patch("fullon_cache_api.models.messages.logger") as mock_logger:
            CacheResponse(request_id="test", success=True)
            mock_logger.debug.assert_called()


class TestStreamMessage:
    """Test FastAPI WebSocket streaming message model."""

    def test_stream_message_creation(self):
        """Test StreamMessage creation."""
        data = {"symbol": "BTC/USDT", "price": 45000.0}
        message = StreamMessage(
            type="ticker_update", data=data, stream_id="tickers_binance", sequence=12345
        )

        assert message.type == "ticker_update"
        assert message.data == data
        assert message.stream_id == "tickers_binance"
        assert message.sequence == 12345
        assert isinstance(message.timestamp, float)

    def test_stream_message_logging(self):
        """Test StreamMessage logging integration."""
        with patch("fullon_cache_api.models.messages.logger") as mock_logger:
            StreamMessage(type="test", data={})
            mock_logger.debug.assert_called()


class TestErrorMessage:
    """Test FastAPI WebSocket error message model."""

    def test_error_message_creation(self):
        """Test ErrorMessage creation."""
        details = {"service": "redis", "timeout": "5s"}
        error = ErrorMessage(
            request_id="test-id",
            error="Cache operation failed",
            error_code="CACHE_UNAVAILABLE",
            details=details,
        )

        assert error.request_id == "test-id"
        assert error.error == "Cache operation failed"
        assert error.error_code == "CACHE_UNAVAILABLE"
        assert error.details == details
        assert isinstance(error.timestamp, float)

    def test_error_message_logging(self):
        """Test ErrorMessage logging integration."""
        with patch("fullon_cache_api.models.messages.logger") as mock_logger:
            ErrorMessage(error="test error", error_code="TEST_ERROR")
            mock_logger.warning.assert_called()


class TestFactoryFunctions:
    """Test message factory functions."""

    def test_create_error_response(self):
        """Test error response factory function."""
        with patch("fullon_cache_api.models.messages.logger") as mock_logger:
            error = create_error_response(
                request_id="test-id",
                error_code="TEST_ERROR",
                error_message="Test error message",
                details={"key": "value"},
            )

            assert isinstance(error, ErrorMessage)
            assert error.request_id == "test-id"
            assert error.error_code == "TEST_ERROR"
            assert error.error == "Test error message"
            assert error.details == {"key": "value"}
            mock_logger.info.assert_called()

    def test_create_success_response(self):
        """Test success response factory function."""
        with patch("fullon_cache_api.models.messages.logger") as mock_logger:
            result = {"data": "test"}
            response = create_success_response(
                request_id="test-id", result=result, latency_ms=25.5
            )

            assert isinstance(response, CacheResponse)
            assert response.request_id == "test-id"
            assert response.success is True
            assert response.result == result
            assert response.latency_ms == 25.5
            mock_logger.info.assert_called()


class TestTickerData:
    """Test ticker data model."""

    def test_ticker_data_creation(self):
        """Test TickerData creation with required fields."""
        ticker = TickerData(
            symbol="BTC/USDT",
            exchange="binance",
            price=Decimal("45000.0"),
            volume=Decimal("1234.56"),
        )

        assert ticker.symbol == "BTC/USDT"
        assert ticker.exchange == "binance"
        assert ticker.price == Decimal("45000.0")
        assert ticker.volume == Decimal("1234.56")
        assert isinstance(ticker.timestamp, float)

    def test_ticker_data_json_encoding(self):
        """Test TickerData JSON encoding for FastAPI."""
        ticker = TickerData(
            symbol="BTC/USDT", exchange="binance", price=Decimal("45000.0")
        )

        # Test that the model can be created with Decimal values
        assert ticker.price == Decimal("45000.0")

        # Test JSON serialization using the json() method which applies encoders
        json_str = ticker.json()
        import json

        json_data = json.loads(json_str)
        # Decimal should be converted to float for JSON
        assert isinstance(json_data["price"], float)

    def test_ticker_data_logging(self):
        """Test TickerData logging integration."""
        with patch("fullon_cache_api.models.data.logger") as mock_logger:
            TickerData(symbol="BTC/USDT", exchange="binance")
            mock_logger.debug.assert_called()


class TestPositionData:
    """Test position data model."""

    def test_position_data_creation(self):
        """Test PositionData creation."""
        position = PositionData(
            user_id=1,
            exchange="binance",
            symbol="BTC/USDT",
            side="long",
            size=Decimal("0.1"),
            entry_price=Decimal("44000.0"),
        )

        assert position.user_id == 1
        assert position.exchange == "binance"
        assert position.symbol == "BTC/USDT"
        assert position.side == "long"
        assert position.size == Decimal("0.1")

    def test_position_data_side_validation(self):
        """Test position side validation."""
        # Valid sides
        for side in ["long", "short", "LONG", "SHORT"]:
            position = PositionData(
                user_id=1,
                exchange="binance",
                symbol="BTC/USDT",
                side=side,
                size=Decimal("0.1"),
            )
            assert position.side.lower() in ["long", "short"]

        # Invalid side
        with pytest.raises(ValidationError):
            PositionData(
                user_id=1,
                exchange="binance",
                symbol="BTC/USDT",
                side="invalid",
                size=Decimal("0.1"),
            )


class TestBalanceData:
    """Test balance data model."""

    def test_balance_data_total_calculation(self):
        """Test automatic total calculation."""
        balance = BalanceData(
            user_id=1,
            exchange="binance",
            asset="USDT",
            available=Decimal("1000.0"),
            locked=Decimal("100.0"),
        )

        assert balance.total == Decimal("1100.0")

    def test_balance_data_explicit_total(self):
        """Test explicit total value."""
        balance = BalanceData(
            user_id=1,
            exchange="binance",
            asset="USDT",
            available=Decimal("1000.0"),
            locked=Decimal("100.0"),
            total=Decimal("1200.0"),  # Explicit total
        )

        assert balance.total == Decimal("1200.0")


class TestOrderData:
    """Test order data model."""

    def test_order_data_creation(self):
        """Test OrderData creation."""
        order = OrderData(
            order_id="order_123",
            user_id=1,
            exchange="binance",
            symbol="BTC/USDT",
            side="buy",
            type="limit",
            status="filled",
            quantity=Decimal("0.1"),
            price=Decimal("44000.0"),
        )

        assert order.order_id == "order_123"
        assert order.side == "buy"
        assert order.type == "limit"
        assert order.status == "filled"

    def test_order_data_validation(self):
        """Test order data validation."""
        # Valid side and type
        order = OrderData(
            order_id="test",
            user_id=1,
            exchange="binance",
            symbol="BTC/USDT",
            side="BUY",
            type="LIMIT",
            status="open",
            quantity=Decimal("0.1"),
        )
        assert order.side == "buy"
        assert order.type == "limit"

        # Invalid side
        with pytest.raises(ValidationError):
            OrderData(
                order_id="test",
                user_id=1,
                exchange="binance",
                symbol="BTC/USDT",
                side="invalid",
                type="limit",
                status="open",
                quantity=Decimal("0.1"),
            )


class TestTradeData:
    """Test trade data model."""

    def test_trade_data_creation(self):
        """Test TradeData creation."""
        trade = TradeData(
            trade_id="trade_123",
            exchange="binance",
            symbol="BTC/USDT",
            side="buy",
            quantity=Decimal("0.1"),
            price=Decimal("45000.0"),
            fee=Decimal("4.5"),
            fee_asset="USDT",
        )

        assert trade.trade_id == "trade_123"
        assert trade.exchange == "binance"
        assert trade.side == "buy"
        assert trade.fee == Decimal("4.5")
        assert trade.fee_asset == "USDT"


class TestOHLCVData:
    """Test OHLCV data model."""

    def test_ohlcv_data_creation(self):
        """Test OHLCVData creation."""
        ohlcv = OHLCVData(
            symbol="BTC/USDT",
            exchange="binance",
            timeframe="1h",
            timestamp=1627846200.0,
            open=Decimal("44000.0"),
            high=Decimal("45000.0"),
            low=Decimal("43500.0"),
            close=Decimal("44800.0"),
            volume=Decimal("123.45"),
        )

        assert ohlcv.symbol == "BTC/USDT"
        assert ohlcv.timeframe == "1h"
        assert ohlcv.open == Decimal("44000.0")
        assert ohlcv.high == Decimal("45000.0")


class TestProcessData:
    """Test process data model."""

    def test_process_data_creation(self):
        """Test ProcessData creation."""
        process = ProcessData(
            process_id="fullon_bot_1",
            name="Trading Bot",
            status="running",
            pid=12345,
            cpu_percent=5.2,
            memory_percent=2.1,
        )

        assert process.process_id == "fullon_bot_1"
        assert process.name == "Trading Bot"
        assert process.status == "running"
        assert process.pid == 12345


class TestBotData:
    """Test bot data model."""

    def test_bot_data_creation(self):
        """Test BotData creation."""
        bot = BotData(
            bot_id="bot_123",
            user_id=1,
            exchange="binance",
            symbol="BTC/USDT",
            status="active",
            is_blocked=False,
        )

        assert bot.bot_id == "bot_123"
        assert bot.user_id == 1
        assert bot.exchange == "binance"
        assert bot.is_blocked is False


class TestHealthData:
    """Test health data model."""

    def test_health_data_creation(self):
        """Test HealthData creation."""
        services = {"redis": "healthy", "database": "healthy", "cache": "healthy"}

        health = HealthData(
            status="healthy", services=services, uptime=86400.0, version="1.0.0"
        )

        assert health.status == "healthy"
        assert health.services == services
        assert health.uptime == 86400.0
        assert health.version == "1.0.0"


class TestAllowedOperations:
    """Test allowed operations validation."""

    def test_allowed_operations_contains_core_ops(self):
        """Test that ALLOWED_OPERATIONS contains core operations."""
        assert "ping" in ALLOWED_OPERATIONS
        assert "health_check" in ALLOWED_OPERATIONS

    def test_allowed_operations_contains_ticker_ops(self):
        """Test that ALLOWED_OPERATIONS contains ticker operations."""
        assert "get_ticker" in ALLOWED_OPERATIONS
        assert "get_all_tickers" in ALLOWED_OPERATIONS
        assert "stream_tickers" in ALLOWED_OPERATIONS

    def test_allowed_operations_contains_all_categories(self):
        """Test that ALLOWED_OPERATIONS contains operations from all categories."""
        categories = [
            "get_user_positions",
            "get_order_status",
            "is_blocked",
            "get_trades",
            "get_latest_ohlcv_bars",
            "get_active_processes",
        ]

        for operation in categories:
            assert operation in ALLOWED_OPERATIONS


class TestErrorCodes:
    """Test error codes constants."""

    def test_error_codes_constants(self):
        """Test ErrorCodes constants are defined."""
        assert hasattr(ErrorCodes, "CONNECTION_FAILED")
        assert hasattr(ErrorCodes, "CACHE_MISS")
        assert hasattr(ErrorCodes, "INVALID_PARAMS")
        assert hasattr(ErrorCodes, "INTERNAL_ERROR")

        # Test actual values
        assert ErrorCodes.CONNECTION_FAILED == "CONNECTION_FAILED"
        assert ErrorCodes.CACHE_MISS == "CACHE_MISS"
        assert ErrorCodes.INVALID_PARAMS == "INVALID_PARAMS"


class TestIntegration:
    """Integration tests for model interactions."""

    def test_request_response_workflow(self):
        """Test complete request-response workflow."""
        # Create request
        request = CacheRequest(
            operation="get_ticker", params={"exchange": "binance", "symbol": "BTC/USDT"}
        )

        # Create ticker data
        ticker_data = TickerData(
            symbol="BTC/USDT", exchange="binance", price=Decimal("45000.0")
        )

        # Create response
        response = CacheResponse(
            request_id=request.request_id,
            success=True,
            result=ticker_data.dict(),
            latency_ms=15.2,
        )

        assert response.request_id == request.request_id
        assert response.success is True
        assert response.result["symbol"] == "BTC/USDT"

    def test_error_workflow(self):
        """Test error handling workflow."""
        request = CacheRequest(operation="get_ticker")

        error = create_error_response(
            request_id=request.request_id,
            error_code=ErrorCodes.CACHE_UNAVAILABLE,
            error_message="Redis connection failed",
        )

        assert error.request_id == request.request_id
        assert error.error_code == ErrorCodes.CACHE_UNAVAILABLE
        assert "Redis connection failed" in error.error
