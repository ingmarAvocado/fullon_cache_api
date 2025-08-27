"""
Comprehensive tests for fullon_cache_api Pydantic models.

Tests cover model creation, validation, error handling, and serialization
for all request and response models with edge cases and validation scenarios.
"""

from datetime import datetime, timedelta

import pytest
from fullon_cache_api.models import (
    AccountBalanceResponse,
    AccountRequest,
    AllTickersRequest,
    AllTickersResponse,
    BalanceRequest,
    # Request models
    BaseRequest,
    # Response models
    BaseResponse,
    BlockedStatusRequest,
    BotRequest,
    CacheQueryRequest,
    ErrorResponse,
    FilterRequest,
    HealthResponse,
    OHLCVRequest,
    OrderRequest,
    OrderStatusResponse,
    PaginationRequest,
    QueueLengthRequest,
    SortRequest,
    TickerRequest,
    TickerResponse,
    TimeRangeRequest,
    TradesRequest,
)
from pydantic import ValidationError


class TestResponseModels:
    """Tests for response models."""

    def test_base_response_creation(self):
        """Test BaseResponse model creation and validation."""
        response = BaseResponse(success=True)
        assert response.success is True
        assert isinstance(response.timestamp, datetime)

    def test_health_response_creation(self):
        """Test HealthResponse model creation."""
        response = HealthResponse(
            success=True,
            service="fullon_cache_api",
            status="healthy",
            version="0.1.0",
            cache_status={"redis": "connected"},
        )
        assert response.success is True
        assert response.service == "fullon_cache_api"
        assert response.status == "healthy"
        assert response.version == "0.1.0"
        assert response.cache_status["redis"] == "connected"

    def test_error_response_defaults(self):
        """Test ErrorResponse model with defaults."""
        response = ErrorResponse(error="Test error", error_code="TEST_ERROR")
        assert response.success is False  # Default for errors
        assert response.error == "Test error"
        assert response.error_code == "TEST_ERROR"
        assert response.details is None

    def test_error_response_with_details(self):
        """Test ErrorResponse with additional details."""
        details = {"field": "symbol", "value": "invalid"}
        response = ErrorResponse(
            error="Validation error", error_code="VALIDATION_ERROR", details=details
        )
        assert response.details == details

    def test_ticker_response_creation(self):
        """Test TickerResponse model creation and validation."""
        cached_time = datetime.utcnow()
        ticker_data = {"bid": 45000.0, "ask": 45050.0, "volume": 123.45}

        response = TickerResponse(
            success=True,
            exchange="binance",
            symbol="BTC/USDT",
            ticker_data=ticker_data,
            cached_at=cached_time,
            cache_hit=True,
        )

        assert response.success is True
        assert response.exchange == "binance"
        assert response.symbol == "BTC/USDT"
        assert response.ticker_data == ticker_data
        assert response.cached_at == cached_time
        assert response.cache_hit is True

    def test_all_tickers_response_creation(self):
        """Test AllTickersResponse model creation."""
        tickers = [
            {"symbol": "BTC/USDT", "price": 45000.0},
            {"symbol": "ETH/USDT", "price": 3000.0},
        ]
        cached_time = datetime.utcnow()

        response = AllTickersResponse(
            success=True,
            exchange="binance",
            tickers=tickers,
            count=2,
            cached_at=cached_time,
        )

        assert response.exchange == "binance"
        assert response.tickers == tickers
        assert response.count == 2
        assert response.cached_at == cached_time

    def test_account_balance_response_creation(self):
        """Test AccountBalanceResponse model creation."""
        balances = {"BTC": 1.5, "USDT": 10000.0}
        cached_time = datetime.utcnow()

        response = AccountBalanceResponse(
            success=True,
            user_id=123,
            exchange="binance",
            balances=balances,
            cached_at=cached_time,
        )

        assert response.user_id == 123
        assert response.exchange == "binance"
        assert response.balances == balances
        assert response.cached_at == cached_time

    def test_order_status_response_creation(self):
        """Test OrderStatusResponse model creation."""
        cached_time = datetime.utcnow()

        response = OrderStatusResponse(
            success=True,
            order_id="order123",
            status="filled",
            symbol="BTC/USDT",
            side="buy",
            amount=0.1,
            price=45000.0,
            cached_at=cached_time,
        )

        assert response.order_id == "order123"
        assert response.status == "filled"
        assert response.symbol == "BTC/USDT"
        assert response.side == "buy"
        assert response.amount == 0.1
        assert response.price == 45000.0
        assert response.cached_at == cached_time


class TestRequestModels:
    """Tests for request models."""

    def test_base_request_creation(self):
        """Test BaseRequest model creation."""
        request = BaseRequest()
        assert isinstance(request, BaseRequest)

    def test_cache_query_request_defaults(self):
        """Test CacheQueryRequest with default timeout."""
        request = CacheQueryRequest()
        assert request.timeout == 5  # default value

    def test_cache_query_request_custom_timeout(self):
        """Test CacheQueryRequest with custom timeout."""
        request = CacheQueryRequest(timeout=30)
        assert request.timeout == 30

    def test_cache_query_request_timeout_validation(self):
        """Test CacheQueryRequest timeout validation."""
        # Valid timeout
        request = CacheQueryRequest(timeout=10)
        assert request.timeout == 10

        # Invalid timeout - too low
        with pytest.raises(ValidationError):
            CacheQueryRequest(timeout=0)

        # Invalid timeout - too high
        with pytest.raises(ValidationError):
            CacheQueryRequest(timeout=100)

    def test_ticker_request_validation(self):
        """Test TickerRequest validation and normalization."""
        # Valid request
        request = TickerRequest(exchange="binance", symbol="BTC/USDT")
        assert request.exchange == "binance"
        assert request.symbol == "BTC/USDT"
        assert request.timeout == 5  # default

        # Test exchange normalization (uppercase to lowercase)
        request2 = TickerRequest(exchange="BINANCE", symbol="eth/usdt")
        assert request2.exchange == "binance"  # lowercased
        assert request2.symbol == "ETH/USDT"  # uppercased

        # Test with hyphens and underscores in exchange
        request3 = TickerRequest(exchange="kraken_pro", symbol="BTC-USD")
        assert request3.exchange == "kraken_pro"
        assert request3.symbol == "BTC-USD"

    def test_ticker_request_invalid_exchange(self):
        """Test TickerRequest with invalid exchange name."""
        with pytest.raises(ValidationError) as exc_info:
            TickerRequest(exchange="invalid@exchange", symbol="BTC/USDT")

        error_messages = str(exc_info.value)
        assert "Exchange name must be alphanumeric" in error_messages

    def test_ticker_request_invalid_symbol(self):
        """Test TickerRequest with invalid symbol format."""
        with pytest.raises(ValidationError) as exc_info:
            TickerRequest(exchange="binance", symbol="BTCUSDT")  # no separator

        error_messages = str(exc_info.value)
        assert "Symbol must contain" in error_messages

    def test_ticker_request_field_length_validation(self):
        """Test TickerRequest field length validation."""
        # Exchange too short
        with pytest.raises(ValidationError):
            TickerRequest(exchange="a", symbol="BTC/USDT")

        # Exchange too long
        with pytest.raises(ValidationError):
            TickerRequest(exchange="a" * 51, symbol="BTC/USDT")

        # Symbol too short - update to be actually too short (less than 3 characters)
        with pytest.raises(ValidationError):
            TickerRequest(exchange="binance", symbol="B/")  # Only 2 characters

        # Symbol too long
        with pytest.raises(ValidationError):
            TickerRequest(
                exchange="binance", symbol="A" * 15 + "/" + "B" * 10
            )  # Over 20 chars

    def test_all_tickers_request_validation(self):
        """Test AllTickersRequest validation."""
        request = AllTickersRequest(exchange="binance")
        assert request.exchange == "binance"

        # Test exchange normalization
        request2 = AllTickersRequest(exchange="KRAKEN")
        assert request2.exchange == "kraken"

    def test_account_request_validation(self):
        """Test AccountRequest validation."""
        request = AccountRequest(user_id=123)
        assert request.user_id == 123
        assert request.exchange is None

        # Test with exchange filter
        request2 = AccountRequest(user_id=456, exchange="kraken")
        assert request2.user_id == 456
        assert request2.exchange == "kraken"

        # Test exchange normalization
        request3 = AccountRequest(user_id=789, exchange="BINANCE")
        assert request3.exchange == "binance"

    def test_account_request_invalid_user_id(self):
        """Test AccountRequest with invalid user_id."""
        with pytest.raises(ValidationError) as exc_info:
            AccountRequest(user_id=0)  # must be > 0

        error_messages = str(exc_info.value)
        assert "greater than 0" in error_messages

        with pytest.raises(ValidationError):
            AccountRequest(user_id=-1)  # negative not allowed

    def test_balance_request_validation(self):
        """Test BalanceRequest validation."""
        request = BalanceRequest(user_id=123, exchange="binance")
        assert request.user_id == 123
        assert request.exchange == "binance"

        # Test exchange normalization
        request2 = BalanceRequest(user_id=456, exchange="KRAKEN")
        assert request2.exchange == "kraken"

    def test_order_request_validation(self):
        """Test OrderRequest validation."""
        request = OrderRequest(order_id="order123")
        assert request.order_id == "order123"

        # Test length limits
        request2 = OrderRequest(order_id="a" * 100)  # max length
        assert len(request2.order_id) == 100

        # Empty order_id should fail
        with pytest.raises(ValidationError):
            OrderRequest(order_id="")

        # Too long order_id should fail
        with pytest.raises(ValidationError):
            OrderRequest(order_id="a" * 101)

    def test_queue_length_request_validation(self):
        """Test QueueLengthRequest validation."""
        request = QueueLengthRequest(exchange="binance")
        assert request.exchange == "binance"

        # Test exchange normalization
        request2 = QueueLengthRequest(exchange="KRAKEN_PRO")
        assert request2.exchange == "kraken_pro"

    def test_bot_request_validation(self):
        """Test BotRequest validation."""
        request = BotRequest(bot_id=42)
        assert request.bot_id == 42

        # Invalid bot_id
        with pytest.raises(ValidationError):
            BotRequest(bot_id=0)

        with pytest.raises(ValidationError):
            BotRequest(bot_id=-1)

    def test_blocked_status_request_validation(self):
        """Test BlockedStatusRequest validation."""
        request = BlockedStatusRequest(exchange="binance", symbol="BTC/USDT")
        assert request.exchange == "binance"
        assert request.symbol == "BTC/USDT"

        # Test normalization
        request2 = BlockedStatusRequest(exchange="KRAKEN", symbol="eth/usd")
        assert request2.exchange == "kraken"
        assert request2.symbol == "ETH/USD"

    def test_trades_request_validation(self):
        """Test TradesRequest validation."""
        request = TradesRequest(symbol="BTC/USDT", exchange="binance")
        assert request.symbol == "BTC/USDT"
        assert request.exchange == "binance"
        assert request.limit == 100  # default

        # Test with custom limit
        request2 = TradesRequest(symbol="ETH/USDT", exchange="kraken", limit=50)
        assert request2.limit == 50

        # Test limit bounds
        with pytest.raises(ValidationError):
            TradesRequest(symbol="BTC/USDT", exchange="binance", limit=0)

        with pytest.raises(ValidationError):
            TradesRequest(symbol="BTC/USDT", exchange="binance", limit=1001)

    def test_ohlcv_request_validation(self):
        """Test OHLCVRequest validation."""
        request = OHLCVRequest(symbol="BTC/USDT", timeframe="1h", exchange="binance")
        assert request.symbol == "BTC/USDT"
        assert request.timeframe == "1h"
        assert request.exchange == "binance"
        assert request.limit == 100  # default

        # Test with custom limit
        request2 = OHLCVRequest(
            symbol="ETH/USDT", timeframe="5m", exchange="kraken", limit=500
        )
        assert request2.limit == 500

        # Test valid timeframes
        valid_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"]
        for tf in valid_timeframes:
            request = OHLCVRequest(symbol="BTC/USDT", timeframe=tf, exchange="binance")
            assert request.timeframe == tf

    def test_ohlcv_request_invalid_timeframe(self):
        """Test OHLCVRequest with invalid timeframe."""
        with pytest.raises(ValidationError) as exc_info:
            OHLCVRequest(symbol="BTC/USDT", timeframe="invalid", exchange="binance")

        error_messages = str(exc_info.value)
        assert (
            "string does not match expected pattern" in error_messages
            or "String should match pattern" in error_messages
        )

    def test_time_range_request_validation(self):
        """Test TimeRangeRequest validation."""
        now = datetime.utcnow()
        start = now - timedelta(hours=1)
        end = now

        request = TimeRangeRequest(start_time=start, end_time=end)
        assert request.start_time == start
        assert request.end_time == end

        # Test with only start_time
        request2 = TimeRangeRequest(start_time=start)
        assert request2.start_time == start
        assert request2.end_time is None

        # Test with no times
        request3 = TimeRangeRequest()
        assert request3.start_time is None
        assert request3.end_time is None

    def test_time_range_request_invalid_range(self):
        """Test TimeRangeRequest with invalid time range."""
        now = datetime.utcnow()
        start = now
        end = now - timedelta(hours=1)  # end before start

        with pytest.raises(ValidationError) as exc_info:
            TimeRangeRequest(start_time=start, end_time=end)

        error_messages = str(exc_info.value)
        assert "end_time must be after start_time" in error_messages

    def test_pagination_request_validation(self):
        """Test PaginationRequest validation and offset calculation."""
        request = PaginationRequest()
        assert request.page == 1  # default
        assert request.limit == 100  # default
        assert request.offset == 0  # (1-1) * 100

        # Test custom pagination
        request2 = PaginationRequest(page=3, limit=50)
        assert request2.page == 3
        assert request2.limit == 50
        assert request2.offset == 100  # (3-1) * 50

        # Test validation bounds
        with pytest.raises(ValidationError):
            PaginationRequest(page=0)  # must be >= 1

        with pytest.raises(ValidationError):
            PaginationRequest(limit=0)  # must be >= 1

        with pytest.raises(ValidationError):
            PaginationRequest(limit=1001)  # must be <= 1000

    def test_sort_request_validation(self):
        """Test SortRequest validation."""
        request = SortRequest(sort_by="timestamp")
        assert request.sort_by == "timestamp"
        assert request.sort_order == "asc"  # default

        # Test with custom sort order
        request2 = SortRequest(sort_by="price", sort_order="desc")
        assert request2.sort_by == "price"
        assert request2.sort_order == "desc"

        # Test sort_by normalization
        request3 = SortRequest(sort_by="TIMESTAMP")
        assert request3.sort_by == "timestamp"

        # Test invalid sort_order
        with pytest.raises(ValidationError):
            SortRequest(sort_by="price", sort_order="invalid")

    def test_filter_request_validation(self):
        """Test FilterRequest validation."""
        request = FilterRequest()
        assert request.filters == {}

        # Test with valid filters
        filters = {"exchange": "binance", "symbol": "BTC/USDT"}
        request2 = FilterRequest(filters=filters)
        assert request2.filters == filters

        # Test filter key validation
        with pytest.raises(ValidationError):
            FilterRequest(filters={"invalid@key": "value"})


class TestModelIntegration:
    """Integration tests for model functionality."""

    def test_all_models_importable(self):
        """Test all models can be imported from package."""
        # If imports in the test file succeeded, this test passes
        assert True

    def test_response_model_serialization(self):
        """Test response models can be serialized to JSON."""
        response = TickerResponse(
            success=True,
            exchange="binance",
            symbol="BTC/USDT",
            ticker_data={"price": 45000},
            cached_at=datetime.utcnow(),
            cache_hit=True,
        )

        json_data = response.model_dump()
        assert isinstance(json_data, dict)
        assert json_data["success"] is True
        assert json_data["exchange"] == "binance"
        assert json_data["symbol"] == "BTC/USDT"
        assert "timestamp" in json_data
        assert "cached_at" in json_data

    def test_request_model_validation_and_serialization(self):
        """Test request models handle validation and serialization."""
        request = TickerRequest(exchange="BINANCE", symbol="btc/usdt", timeout=10)

        # Test validation/normalization occurred
        assert request.exchange == "binance"
        assert request.symbol == "BTC/USDT"
        assert request.timeout == 10

        # Test serialization
        json_data = request.model_dump()
        assert isinstance(json_data, dict)
        assert json_data["exchange"] == "binance"
        assert json_data["symbol"] == "BTC/USDT"
        assert json_data["timeout"] == 10

    def test_model_config_inheritance(self):
        """Test model configuration inheritance."""
        request = TickerRequest(exchange="  binance  ", symbol="BTC/USDT")
        # str_strip_whitespace should work
        assert request.exchange == "binance"  # whitespace stripped and lowercased

    def test_error_response_structure(self):
        """Test error response provides proper structure for API errors."""
        response = ErrorResponse(
            error="Invalid exchange name",
            error_code="INVALID_EXCHANGE",
            details={"field": "exchange", "value": "invalid@name"},
        )

        assert response.success is False
        assert response.error == "Invalid exchange name"
        assert response.error_code == "INVALID_EXCHANGE"
        assert response.details["field"] == "exchange"

        # Should serialize properly for API responses
        json_data = response.model_dump()
        assert json_data["success"] is False
        assert "timestamp" in json_data
