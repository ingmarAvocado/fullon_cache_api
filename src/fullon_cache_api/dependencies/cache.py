from collections.abc import AsyncGenerator

from fullon_cache import (
    AccountCache,
    BotCache,
    OHLCVCache,
    OrdersCache,
    ProcessCache,
    TickCache,
    TradesCache,
)
from fullon_log import get_component_logger

from ..exceptions import CacheServiceUnavailableError

logger = get_component_logger("fullon.api.cache.dependencies")


# Cache session providers
async def get_tick_cache() -> AsyncGenerator[TickCache, None]:
    """Provide TickCache session for ticker operations."""
    logger.debug("Creating TickCache session")
    try:
        async with TickCache() as cache:
            yield cache
    except Exception as e:
        logger.error(
            "Failed to create TickCache session",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise CacheServiceUnavailableError(
            f"Ticker cache service unavailable: {str(e)}"
        ) from e


async def get_orders_cache() -> AsyncGenerator[OrdersCache, None]:
    """Provide OrdersCache session for order operations."""
    logger.debug("Creating OrdersCache session")
    try:
        async with OrdersCache() as cache:
            yield cache
    except Exception as e:
        logger.error(
            "Failed to create OrdersCache session",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise CacheServiceUnavailableError(
            f"Orders cache service unavailable: {str(e)}"
        ) from e


async def get_bot_cache() -> AsyncGenerator[BotCache, None]:
    """Provide BotCache session for bot operations."""
    logger.debug("Creating BotCache session")
    try:
        async with BotCache() as cache:
            yield cache
    except Exception as e:
        logger.error(
            "Failed to create BotCache session",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise CacheServiceUnavailableError(
            f"Bot cache service unavailable: {str(e)}"
        ) from e


async def get_account_cache() -> AsyncGenerator[AccountCache, None]:
    """Provide AccountCache session for account operations."""
    logger.debug("Creating AccountCache session")
    try:
        async with AccountCache() as cache:
            yield cache
    except Exception as e:
        logger.error(
            "Failed to create AccountCache session",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise CacheServiceUnavailableError(
            f"Account cache service unavailable: {str(e)}"
        ) from e


async def get_trades_cache() -> AsyncGenerator[TradesCache, None]:
    """Provide TradesCache session for trade operations."""
    logger.debug("Creating TradesCache session")
    try:
        async with TradesCache() as cache:
            yield cache
    except Exception as e:
        logger.error(
            "Failed to create TradesCache session",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise CacheServiceUnavailableError(
            f"Trades cache service unavailable: {str(e)}"
        ) from e


async def get_ohlcv_cache() -> AsyncGenerator[OHLCVCache, None]:
    """Provide OHLCVCache session for OHLCV operations."""
    logger.debug("Creating OHLCVCache session")
    try:
        async with OHLCVCache() as cache:
            yield cache
    except Exception as e:
        logger.error(
            "Failed to create OHLCVCache session",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise CacheServiceUnavailableError(
            f"OHLCV cache service unavailable: {str(e)}"
        ) from e


async def get_process_cache() -> AsyncGenerator[ProcessCache, None]:
    """Provide ProcessCache session for process monitoring."""
    logger.debug("Creating ProcessCache session")
    try:
        async with ProcessCache() as cache:
            yield cache
    except Exception as e:
        logger.error(
            "Failed to create ProcessCache session",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise CacheServiceUnavailableError(
            f"Process cache service unavailable: {str(e)}"
        ) from e
