"""
Tests for ticker cache router functionality.

This module tests the ticker cache router endpoints including parameter validation,
cache operations, error handling, and response formatting following TDD principles.
"""

import time
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from fullon_orm.models import Symbol, Tick

from fullon_cache_api.dependencies.cache import get_tick_cache
from fullon_cache_api.exceptions import (
    CacheNotFoundError,
    CacheServiceUnavailableError,
    CacheTimeoutError,
)
from fullon_cache_api.routers.exceptions import InvalidParameterError


class TestTickerCacheRouter:
    """Test ticker cache router endpoints."""

    @pytest.fixture
    def mock_tick_cache(self):
        """Mock TickCache for testing."""
        mock_cache = AsyncMock()
        mock_cache.ping.return_value = "pong"
        mock_cache.test.return_value = True
        return mock_cache

    @pytest.fixture
    def mock_tick_data(self):
        """Mock tick data for testing."""
        return Tick(
            symbol="BTC/USDT",
            exchange="binance",
            price=50000.0,
            volume=100.0,
            time=time.time(),
            bid=49999.0,
            ask=50001.0,
            last=50000.0,
        )

    @pytest.fixture
    def mock_symbol(self):
        """Mock Symbol object for testing."""
        return Symbol(symbol="BTC/USDT", cat_ex_id=1, base="BTC", quote="USDT")

    def test_get_ticker_success(
        self, client, override_cache_dependency, mock_tick_data
    ):
        """Test successful ticker retrieval from cache."""
        response = client.get("/api/v1/cache/tickers/binance/BTC%2FUSDT")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["exchange"] == "binance"
        assert data["symbol"] == "BTC/USDT"
        assert data["ticker_data"]["price"] == 50000.0
        assert data["cache_hit"] is True

    def test_get_ticker_not_found(self, client, app, mock_tick_cache):
        """Test 404 response for ticker not in cache."""
        from fullon_cache_api.dependencies.cache import get_tick_cache

        # Override to return None (not found)
        mock_tick_cache.get_ticker.return_value = None

        async def mock_get_tick_cache():
            yield mock_tick_cache

        app.dependency_overrides[get_tick_cache] = mock_get_tick_cache

        response = client.get("/api/v1/cache/tickers/binance/BTC%2FUSDT")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"].lower()

        # Clean up
        app.dependency_overrides = {}

    async def test_get_all_tickers_exchange(self, client, mock_tick_cache):
        """Test retrieving all tickers for specific exchange."""
        mock_tickers = [
            {"symbol": "BTC/USDT", "price": 50000.0},
            {"symbol": "ETH/USDT", "price": 3000.0},
        ]
        mock_tick_cache.get_all_tickers.return_value = mock_tickers

        with patch("fullon_cache_api.routers.tickers.get_tick_cache") as mock_get_cache:

            async def mock_cache_gen():
                yield mock_tick_cache

            mock_get_cache.return_value = mock_cache_gen()

            response = client.get("/api/v1/cache/tickers/binance")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["exchange"] == "binance"
            assert data["count"] == 2
            assert len(data["tickers"]) == 2

    async def test_get_active_tickers(self, client, mock_tick_cache):
        """Test active tickers list endpoint."""
        mock_active_symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT"]
        mock_tick_cache.get_active_symbols.return_value = mock_active_symbols

        with patch("fullon_cache_api.routers.tickers.get_tick_cache") as mock_get_cache:

            async def mock_cache_gen():
                yield mock_tick_cache

            mock_get_cache.return_value = mock_cache_gen()

            response = client.get("/api/v1/cache/tickers/binance/active")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 3
            assert "BTC/USDT" in data

    async def test_ticker_cache_health(self, client, mock_tick_cache):
        """Test ticker cache health check endpoint."""
        mock_tick_cache.ping.return_value = "pong"
        mock_tick_cache.test.return_value = True

        with patch("fullon_cache_api.routers.tickers.get_tick_cache") as mock_get_cache:

            async def mock_cache_gen():
                yield mock_tick_cache

            mock_get_cache.return_value = mock_cache_gen()

            response = client.get("/api/v1/cache/tickers/health")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["status"] == "healthy"
            assert data["redis_connected"] is True

    async def test_invalid_exchange_symbol(self, client):
        """Test validation error responses."""
        # Test empty exchange
        response = client.get("/api/v1/cache/tickers//BTC%2FUSDT")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test invalid symbol format
        response = client.get("/api/v1/cache/tickers/binance/BTCUSDT")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test empty symbol base
        response = client.get("/api/v1/cache/tickers/binance/%2FUSDT")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_cache_connection_failure(self, client):
        """Test 503 error on Redis connection failure."""
        with patch("fullon_cache_api.routers.tickers.get_tick_cache") as mock_get_cache:

            async def failing_cache_gen():
                raise ConnectionError("Redis connection failed")

            mock_get_cache.return_value = failing_cache_gen()

            response = client.get("/api/v1/cache/tickers/binance/BTC%2FUSDT")

            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            data = response.json()
            assert data["success"] is False
            assert "unavailable" in data["error"].lower()

    async def test_ticker_performance_metrics(self, client, mock_tick_cache):
        """Test ticker cache performance endpoint."""
        mock_metrics = {
            "cache_hits": 1250,
            "cache_misses": 48,
            "hit_ratio": 0.963,
            "avg_latency_ms": 12.5,
            "total_requests": 1298,
        }
        mock_tick_cache.get_performance_metrics.return_value = mock_metrics

        with patch("fullon_cache_api.routers.tickers.get_tick_cache") as mock_get_cache:

            async def mock_cache_gen():
                yield mock_tick_cache

            mock_get_cache.return_value = mock_cache_gen()

            response = client.get("/api/v1/cache/tickers/performance")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["cache_hits"] == 1250
            assert data["hit_ratio"] == 0.963

    async def test_parameter_validation_edge_cases(self, client):
        """Test edge cases in parameter validation."""
        # Test whitespace-only exchange
        response = client.get("/api/v1/cache/tickers/%20%20/BTC%2FUSDT")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test symbol with multiple separators
        response = client.get("/api/v1/cache/tickers/binance/BTC%2F%2FUSDT")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test symbol with whitespace-only parts
        response = client.get("/api/v1/cache/tickers/binance/%20%2F%20")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_cache_timeout_handling(self, client, mock_tick_cache):
        """Test cache timeout error handling."""
        mock_tick_cache.get_ticker.side_effect = TimeoutError("Operation timeout")

        with patch("fullon_cache_api.routers.tickers.get_tick_cache") as mock_get_cache:

            async def mock_cache_gen():
                yield mock_tick_cache

            mock_get_cache.return_value = mock_cache_gen()

            response = client.get("/api/v1/cache/tickers/binance/BTC%2FUSDT")

            assert response.status_code == status.HTTP_408_REQUEST_TIMEOUT
            data = response.json()
            assert data["success"] is False
            assert "timeout" in data["error"].lower()

    async def test_concurrent_ticker_requests(
        self, client, mock_tick_cache, mock_tick_data
    ):
        """Test handling multiple concurrent ticker requests."""
        mock_tick_cache.get_ticker.return_value = mock_tick_data

        with patch("fullon_cache_api.routers.tickers.get_tick_cache") as mock_get_cache:

            async def mock_cache_gen():
                yield mock_tick_cache

            mock_get_cache.return_value = mock_cache_gen()

            # Simulate concurrent requests
            import asyncio
            import httpx

            async def make_request():
                async with httpx.AsyncClient(
                    app=client.app, base_url="http://test"
                ) as ac:
                    response = await ac.get("/api/v1/cache/tickers/binance/BTC%2FUSDT")
                    return response.status_code

            # Run multiple concurrent requests
            tasks = [make_request() for _ in range(10)]
            results = await asyncio.gather(*tasks)

            # All requests should succeed
            assert all(status_code == status.HTTP_200_OK for status_code in results)

    async def test_response_format_consistency(
        self, client, mock_tick_cache, mock_tick_data
    ):
        """Test consistent response format across endpoints."""
        mock_tick_cache.get_ticker.return_value = mock_tick_data

        with patch("fullon_cache_api.routers.tickers.get_tick_cache") as mock_get_cache:

            async def mock_cache_gen():
                yield mock_tick_cache

            mock_get_cache.return_value = mock_cache_gen()

            response = client.get("/api/v1/cache/tickers/binance/BTC%2FUSDT")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Check standard response fields
            assert "success" in data
            assert "timestamp" in data
            assert isinstance(data["timestamp"], str)
            assert "exchange" in data
            assert "symbol" in data
            assert "ticker_data" in data
            assert "cache_hit" in data
            assert "cached_at" in data

    async def test_logging_integration(self, client, mock_tick_cache, mock_tick_data):
        """Test fullon_log integration with ticker operations."""
        mock_tick_cache.get_ticker.return_value = mock_tick_data

        with patch("fullon_cache_api.routers.tickers.logger") as mock_logger:
            with patch(
                "fullon_cache_api.routers.tickers.get_tick_cache"
            ) as mock_get_cache:

                async def mock_cache_gen():
                    yield mock_tick_cache

                mock_get_cache.return_value = mock_cache_gen()

                response = client.get("/api/v1/cache/tickers/binance/BTC%2FUSDT")

                assert response.status_code == status.HTTP_200_OK

                # Verify logging calls
                assert mock_logger.info.called
                log_calls = mock_logger.info.call_args_list

                # Should have start and success logs
                assert len(log_calls) >= 2
                assert any("started" in str(call) for call in log_calls)
                assert any("completed" in str(call) for call in log_calls)


class TestTickerRouterIntegration:
    """Integration tests for ticker cache router."""

    async def test_full_ticker_workflow(self, client):
        """Test complete ticker cache workflow."""
        # This would test with real cache in integration environment
        # For now, test the workflow structure
        pass

    async def test_ticker_cache_refresh_detection(self, client):
        """Test detection of stale ticker data."""
        # Mock stale data scenario
        mock_old_time = datetime.utcnow().timestamp() - 3600  # 1 hour old

        with patch("fullon_cache_api.routers.tickers.get_tick_cache") as mock_get_cache:
            mock_cache = AsyncMock()
            mock_tick = Tick(
                symbol="BTC/USDT",
                exchange="binance",
                price=50000.0,
                volume=100.0,
                time=mock_old_time,
                bid=49999.0,
                ask=50001.0,
                last=50000.0,
            )
            mock_cache.get_ticker.return_value = mock_tick

            async def mock_cache_gen():
                yield mock_cache

            mock_get_cache.return_value = mock_cache_gen()

            response = client.get("/api/v1/cache/tickers/binance/BTC%2FUSDT")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            # Should detect and flag stale data
            assert data.get("stale") is True


class TestTickerRouterErrorHandling:
    """Test error handling patterns in ticker router."""

    async def test_cache_service_unavailable(self, client):
        """Test service unavailable error handling."""
        with patch("fullon_cache_api.dependencies.cache.TickCache") as mock_cache_class:
            mock_cache_class.side_effect = ConnectionError("Redis unavailable")

            response = client.get("/api/v1/cache/tickers/binance/BTC%2FUSDT")

            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            data = response.json()
            assert data["success"] is False
            assert "unavailable" in data["error"].lower()

    async def test_error_response_format(self, client):
        """Test consistent error response format."""
        response = client.get("/api/v1/cache/tickers//BTC%2FUSDT")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()

        # Check error response structure
        assert "success" in data
        assert data["success"] is False
        assert "error" in data
        assert "error_code" in data
        assert "timestamp" in data
