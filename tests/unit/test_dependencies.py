"""Tests for dependency providers in src.fullon_cache_api.dependencies.

Covers error paths when caches are unavailable and minimal happy-path using
fake async context managers (no external dependencies required).
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import pytest

import sys
import types


def _install_fake_fullon_log() -> None:
    if "fullon_log" in sys.modules:
        return
    m = types.ModuleType("fullon_log")

    class _Dummy:
        def __getattr__(self, name):
            def _noop(*args, **kwargs):
                return None

            return _noop

    def get_component_logger(name: str) -> _Dummy:  # type: ignore
        return _Dummy()

    m.get_component_logger = get_component_logger  # type: ignore[attr-defined]
    sys.modules["fullon_log"] = m


@pytest.mark.asyncio
async def test_dependencies_raise_when_cache_missing() -> None:
    _install_fake_fullon_log()
    import src.fullon_cache_api.dependencies as deps
    from src.fullon_cache_api.exceptions import CacheServiceUnavailableError

    # Backup and patch the internal cache map
    original = deps._caches.copy()
    try:
        deps._caches["TickCache"] = None
        deps._caches["OrdersCache"] = None
        deps._caches["BotCache"] = None
        deps._caches["TradesCache"] = None
        deps._caches["AccountCache"] = None
        deps._caches["OHLCVCache"] = None

        with pytest.raises(CacheServiceUnavailableError):
            async for _ in deps.get_tick_cache():
                pass
        with pytest.raises(CacheServiceUnavailableError):
            async for _ in deps.get_orders_cache():
                pass
        with pytest.raises(CacheServiceUnavailableError):
            async for _ in deps.get_bot_cache():
                pass
        with pytest.raises(CacheServiceUnavailableError):
            async for _ in deps.get_trades_cache():
                pass
        with pytest.raises(CacheServiceUnavailableError):
            async for _ in deps.get_account_cache():
                pass
        with pytest.raises(CacheServiceUnavailableError):
            async for _ in deps.get_ohlcv_cache():
                pass
    finally:
        deps._caches = original


class _FakeCache:
    def __init__(self) -> None:
        self.closed = False

    async def __aenter__(self) -> "_FakeCache":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        self.closed = True


@pytest.mark.asyncio
async def test_dependencies_yield_cache_instances() -> None:
    _install_fake_fullon_log()
    import src.fullon_cache_api.dependencies as deps
    original = deps._caches.copy()
    try:
        deps._caches.update(
            {
                "TickCache": _FakeCache,
                "OrdersCache": _FakeCache,
                "BotCache": _FakeCache,
                "TradesCache": _FakeCache,
                "AccountCache": _FakeCache,
                "OHLCVCache": _FakeCache,
            }
        )

        async for c in deps.get_tick_cache():
            assert isinstance(c, _FakeCache)
        async for c in deps.get_orders_cache():
            assert isinstance(c, _FakeCache)
        async for c in deps.get_bot_cache():
            assert isinstance(c, _FakeCache)
        async for c in deps.get_trades_cache():
            assert isinstance(c, _FakeCache)
        async for c in deps.get_account_cache():
            assert isinstance(c, _FakeCache)
        async for c in deps.get_ohlcv_cache():
            assert isinstance(c, _FakeCache)
    finally:
        deps._caches = original
