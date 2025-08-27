"""
Test configuration and fixtures for fullon_cache_api.

This module provides shared test fixtures, configurations, and utilities
for all test modules in the fullon_cache_api test suite.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def app():
    """Create a FastAPI application for testing."""
    from fullon_cache_api.routers.tickers import router as ticker_router

    app = FastAPI(
        title="fullon_cache_api Test",
        description="Test application for fullon_cache_api",
        version="0.1.0",
    )

    # Include ticker router for testing
    app.include_router(ticker_router, prefix="/api/v1/cache")

    return app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def override_cache_dependency(app, mock_tick_cache, mock_tick_data):
    """Override the cache dependency for testing."""
    from fullon_cache_api.dependencies.cache import get_tick_cache

    # Set up default mock behavior
    mock_tick_cache.get_ticker.return_value = mock_tick_data

    async def mock_get_tick_cache():
        yield mock_tick_cache

    app.dependency_overrides[get_tick_cache] = mock_get_tick_cache
    yield
    app.dependency_overrides = {}


@pytest.fixture
def mock_tick_cache():
    """Mock TickCache for testing."""
    mock_cache = AsyncMock()
    mock_cache.ping.return_value = "pong"
    mock_cache.test.return_value = True
    return mock_cache


@pytest.fixture
def mock_symbol():
    """Mock Symbol object for testing."""
    from fullon_orm.models import Symbol

    return Symbol(symbol="BTC/USDT", cat_ex_id=1, base="BTC", quote="USDT")


@pytest.fixture
def mock_tick_data():
    """Mock Tick data for testing."""
    import time
    from fullon_orm.models import Tick

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
