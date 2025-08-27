from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fullon_cache_api.dependencies import (
    check_all_cache_services,
    get_account_cache,
    get_bot_cache,
    get_ohlcv_cache,
    get_orders_cache,
    get_process_cache,
    get_tick_cache,
    get_trades_cache,
    require_healthy_cache,
    validate_exchange_symbol,
    validate_user_exists,
)
from fullon_cache_api.exceptions import CacheNotFoundError, CacheServiceUnavailableError


class TestCacheDependencies:
    @pytest.mark.asyncio
    async def test_get_tick_cache_success(self):
        """Test successful TickCache dependency injection."""
        with patch("fullon_cache_api.dependencies.cache.TickCache") as mock_cache_class:
            mock_cache = AsyncMock()
            mock_context_result = AsyncMock()
            mock_cache.__aenter__.return_value = mock_context_result
            mock_cache_class.return_value = mock_cache

            # Use async generator properly
            gen = get_tick_cache()
            cache = await gen.__anext__()
            assert cache is mock_context_result

            # Verify context manager was used
            mock_cache.__aenter__.assert_called_once()

            # Clean up generator
            try:
                await gen.__anext__()
            except StopAsyncIteration:
                pass

    @pytest.mark.asyncio
    async def test_get_tick_cache_failure(self):
        """Test TickCache dependency failure handling."""
        with patch("fullon_cache_api.dependencies.cache.TickCache") as mock_cache_class:
            mock_cache_class.side_effect = Exception("Redis connection failed")

            with pytest.raises(CacheServiceUnavailableError) as exc_info:
                gen = get_tick_cache()
                await gen.__anext__()

            assert "Ticker cache service unavailable" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_all_cache_dependencies_exist(self):
        """Test all cache dependencies can be imported and called."""
        dependencies = [
            get_tick_cache,
            get_orders_cache,
            get_bot_cache,
            get_account_cache,
            get_trades_cache,
            get_ohlcv_cache,
            get_process_cache,
        ]

        for dep in dependencies:
            assert callable(dep)
            # Test that they're async generators
            import inspect

            assert inspect.isasyncgenfunction(dep)


class TestValidationDependencies:
    @pytest.mark.asyncio
    async def test_validate_exchange_symbol_success(self):
        """Test successful exchange/symbol validation."""
        with patch(
            "fullon_cache_api.dependencies.validation.get_async_session"
        ) as mock_session, patch(
            "fullon_cache_api.dependencies.validation.SymbolRepository"
        ) as mock_repo_class:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            # Mock symbol exists
            mock_symbol = MagicMock()
            mock_symbol.id = 123
            mock_repo.get_by_symbol.return_value = mock_symbol

            result = await validate_exchange_symbol("binance", "BTC/USDT")
            assert result == ("binance", "BTC/USDT")

            mock_repo.get_by_symbol.assert_called_once_with("BTC/USDT", "binance")

    @pytest.mark.asyncio
    async def test_validate_exchange_symbol_not_found(self):
        """Test exchange/symbol validation when symbol not found."""
        with patch(
            "fullon_cache_api.dependencies.validation.get_async_session"
        ) as mock_session, patch(
            "fullon_cache_api.dependencies.validation.SymbolRepository"
        ) as mock_repo_class:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            # Mock symbol doesn't exist
            mock_repo.get_by_symbol.return_value = None

            with pytest.raises(CacheNotFoundError) as exc_info:
                await validate_exchange_symbol("binance", "INVALID/PAIR")

            assert "Symbol INVALID/PAIR not found on exchange binance" in str(
                exc_info.value.detail
            )

    @pytest.mark.asyncio
    async def test_validate_user_exists_success(self):
        """Test successful user validation."""
        with patch(
            "fullon_cache_api.dependencies.validation.get_async_session"
        ) as mock_session, patch(
            "fullon_cache_api.dependencies.validation.UserRepository"
        ) as mock_repo_class:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            # Mock active user exists
            mock_user = MagicMock()
            mock_user.active = True
            mock_user.name = "test_user"
            mock_repo.get_by_id.return_value = mock_user

            result = await validate_user_exists(123)
            assert result == 123

    @pytest.mark.asyncio
    async def test_validate_user_inactive(self):
        """Test user validation with inactive user."""
        with patch(
            "fullon_cache_api.dependencies.validation.get_async_session"
        ) as mock_session, patch(
            "fullon_cache_api.dependencies.validation.UserRepository"
        ) as mock_repo_class:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            # Mock inactive user
            mock_user = MagicMock()
            mock_user.active = False
            mock_repo.get_by_id.return_value = mock_user

            with pytest.raises(HTTPException) as exc_info:
                await validate_user_exists(123)

            assert exc_info.value.status_code == 403
            assert "User account is inactive" in str(exc_info.value.detail)


class TestHealthDependencies:
    @pytest.mark.asyncio
    async def test_check_all_cache_services_healthy(self):
        """Test health check when all services are healthy."""
        with patch(
            "fullon_cache_api.dependencies.health.get_tick_cache"
        ) as mock_tick, patch(
            "fullon_cache_api.dependencies.health.get_orders_cache"
        ) as mock_orders, patch(
            "fullon_cache_api.dependencies.health.get_bot_cache"
        ) as mock_bot, patch(
            "fullon_cache_api.dependencies.health.get_account_cache"
        ) as mock_account, patch(
            "fullon_cache_api.dependencies.health.get_trades_cache"
        ) as mock_trades, patch(
            "fullon_cache_api.dependencies.health.get_ohlcv_cache"
        ) as mock_ohlcv, patch(
            "fullon_cache_api.dependencies.health.get_process_cache"
        ) as mock_process:
            # Mock all caches as healthy
            all_mocks = [
                mock_tick,
                mock_orders,
                mock_bot,
                mock_account,
                mock_trades,
                mock_ohlcv,
                mock_process,
            ]
            for mock_cache in all_mocks:
                mock_cache_instance = AsyncMock()
                mock_cache_instance.test = AsyncMock(return_value=True)
                mock_cache.return_value.__aenter__.return_value = mock_cache_instance

            result = await check_all_cache_services()

            assert result["overall_status"] == "healthy"
            assert len(result["services"]) == 7
            assert all(
                service["status"] == "healthy"
                for service in result["services"].values()
            )

    @pytest.mark.asyncio
    async def test_check_all_cache_services_unhealthy(self):
        """Test health check when all services are unhealthy."""
        with patch(
            "fullon_cache_api.dependencies.health.get_tick_cache"
        ) as mock_tick, patch(
            "fullon_cache_api.dependencies.health.get_orders_cache"
        ) as mock_orders, patch(
            "fullon_cache_api.dependencies.health.get_bot_cache"
        ) as mock_bot, patch(
            "fullon_cache_api.dependencies.health.get_account_cache"
        ) as mock_account, patch(
            "fullon_cache_api.dependencies.health.get_trades_cache"
        ) as mock_trades, patch(
            "fullon_cache_api.dependencies.health.get_ohlcv_cache"
        ) as mock_ohlcv, patch(
            "fullon_cache_api.dependencies.health.get_process_cache"
        ) as mock_process:
            # Mock all caches as unhealthy
            all_mocks = [
                mock_tick,
                mock_orders,
                mock_bot,
                mock_account,
                mock_trades,
                mock_ohlcv,
                mock_process,
            ]
            for mock_cache in all_mocks:
                mock_cache.side_effect = Exception("Cache unavailable")

            result = await check_all_cache_services()

            assert result["overall_status"] == "unhealthy"
            assert all(
                service["status"] == "unhealthy"
                for service in result["services"].values()
            )

    @pytest.mark.asyncio
    async def test_require_healthy_cache_success(self):
        """Test require_healthy_cache when services are healthy."""
        with patch(
            "fullon_cache_api.dependencies.health.check_all_cache_services"
        ) as mock_check:
            mock_check.return_value = {"overall_status": "healthy"}

            # Should not raise any exception
            await require_healthy_cache()

    @pytest.mark.asyncio
    async def test_require_healthy_cache_failure(self):
        """Test require_healthy_cache when services are unhealthy."""
        with patch(
            "fullon_cache_api.dependencies.health.check_all_cache_services"
        ) as mock_check:
            mock_check.return_value = {"overall_status": "unhealthy"}

            with pytest.raises(HTTPException) as exc_info:
                await require_healthy_cache()

            assert exc_info.value.status_code == 503
            assert "Cache services are currently unavailable" in str(
                exc_info.value.detail
            )
