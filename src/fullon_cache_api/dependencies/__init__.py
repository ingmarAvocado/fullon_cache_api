"""
FastAPI dependency injection for cache sessions.

Provides lightweight, read-only cache session dependencies that integrate with
FastAPI's `Depends(...)` pattern. Each dependency opens a cache session using
fullon_cache and ensures proper async cleanup.

Design constraints:
- Read-only usage only; no mutating operations.
- Async context management for clean resource handling.
- Degrades gracefully when `fullon_cache` is unavailable.
"""

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any, Optional

from fullon_log import get_component_logger  # type: ignore

from ..exceptions import CacheServiceUnavailableError

logger = get_component_logger("fullon.api.cache.dependencies")

if TYPE_CHECKING:  # type hints without importing at runtime
    from fullon_cache import (  # pragma: no cover - type checking only
        AccountCache as _AccountCache,
    )
    from fullon_cache import (
        BotCache as _BotCache,
    )
    from fullon_cache import (
        OHLCVCache as _OHLCVCache,
    )
    from fullon_cache import (
        OrdersCache as _OrdersCache,
    )
    from fullon_cache import (
        TickCache as _TickCache,
    )
    from fullon_cache import (
        TradesCache as _TradesCache,
    )


def _import_caches() -> dict[str, Optional[type]]:
    """Attempt to import cache classes from fullon_cache.

    Returns a dict of cache class references or None when unavailable.
    """
    try:  # defer import to runtime to avoid hard dependency during import
        from fullon_cache import (  # type: ignore
            AccountCache,
            BotCache,
            OHLCVCache,
            OrdersCache,
            TickCache,
            TradesCache,
        )

        return {
            "TickCache": TickCache,
            "OrdersCache": OrdersCache,
            "BotCache": BotCache,
            "TradesCache": TradesCache,
            "AccountCache": AccountCache,
            "OHLCVCache": OHLCVCache,
        }
    except Exception as exc:  # pragma: no cover - environment dependent
        logger.warning(
            "fullon_cache import failed; dependencies will raise on use",
            error=str(exc),
        )
        return {
            "TickCache": None,
            "OrdersCache": None,
            "BotCache": None,
            "TradesCache": None,
            "AccountCache": None,
            "OHLCVCache": None,
        }


_caches = _import_caches()


async def get_tick_cache() -> AsyncGenerator["_TickCache" | Any, None]:
    tick_cls = _caches.get("TickCache")
    if tick_cls is None:
        raise CacheServiceUnavailableError(
            "TickCache unavailable: install/configure fullon_cache"
        )
    logger.info("Opening TickCache session")
    async with tick_cls() as cache:  # type: ignore[call-arg]
        try:
            yield cache
        finally:
            logger.info("Closed TickCache session")


async def get_orders_cache() -> AsyncGenerator["_OrdersCache" | Any, None]:
    orders_cls = _caches.get("OrdersCache")
    if orders_cls is None:
        raise CacheServiceUnavailableError(
            "OrdersCache unavailable: install/configure fullon_cache"
        )
    logger.info("Opening OrdersCache session")
    async with orders_cls() as cache:  # type: ignore[call-arg]
        try:
            yield cache
        finally:
            logger.info("Closed OrdersCache session")


async def get_bot_cache() -> AsyncGenerator["_BotCache" | Any, None]:
    bot_cls = _caches.get("BotCache")
    if bot_cls is None:
        raise CacheServiceUnavailableError(
            "BotCache unavailable: install/configure fullon_cache"
        )
    logger.info("Opening BotCache session")
    async with bot_cls() as cache:  # type: ignore[call-arg]
        try:
            yield cache
        finally:
            logger.info("Closed BotCache session")


async def get_trades_cache() -> AsyncGenerator["_TradesCache" | Any, None]:
    trades_cls = _caches.get("TradesCache")
    if trades_cls is None:
        raise CacheServiceUnavailableError(
            "TradesCache unavailable: install/configure fullon_cache"
        )
    logger.info("Opening TradesCache session")
    async with trades_cls() as cache:  # type: ignore[call-arg]
        try:
            yield cache
        finally:
            logger.info("Closed TradesCache session")


async def get_account_cache() -> AsyncGenerator["_AccountCache" | Any, None]:
    account_cls = _caches.get("AccountCache")
    if account_cls is None:
        raise CacheServiceUnavailableError(
            "AccountCache unavailable: install/configure fullon_cache"
        )
    logger.info("Opening AccountCache session")
    async with account_cls() as cache:  # type: ignore[call-arg]
        try:
            yield cache
        finally:
            logger.info("Closed AccountCache session")


async def get_ohlcv_cache() -> AsyncGenerator["_OHLCVCache" | Any, None]:
    ohlcv_cls = _caches.get("OHLCVCache")
    if ohlcv_cls is None:
        raise CacheServiceUnavailableError(
            "OHLCVCache unavailable: install/configure fullon_cache"
        )
    logger.info("Opening OHLCVCache session")
    async with ohlcv_cls() as cache:  # type: ignore[call-arg]
        try:
            yield cache
        finally:
            logger.info("Closed OHLCVCache session")


__all__ = [
    "get_tick_cache",
    "get_orders_cache",
    "get_bot_cache",
    "get_trades_cache",
    "get_account_cache",
    "get_ohlcv_cache",
]
