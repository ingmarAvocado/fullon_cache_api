"""Integration tests for OHLCV WebSocket with REAL Redis (no mocks)."""

from __future__ import annotations

import asyncio
import json
import time
import uuid

import pytest
from fullon_cache_api.main import create_app
from starlette.testclient import TestClient

pytestmark = [pytest.mark.integration, pytest.mark.redis]


def _flush_db() -> None:
    try:
        from fullon_cache import BaseCache  # type: ignore

        async def _do() -> None:
            cache = BaseCache()
            async with cache._redis_context() as redis:
                await redis.flushdb()
            await cache.close()

        asyncio.get_event_loop().run_until_complete(_do())
    except Exception:
        # Best effort cleanup; tests still run if flush not possible
        pass


def _make_bars(
    start_ts: int, count: int = 10, base_price: float = 100.0
) -> list[list[float]]:
    bars: list[list[float]] = []
    ts = start_ts
    price = base_price
    for i in range(count):
        o = price
        h = o * 1.01
        l = o * 0.99
        c = o * 1.002
        v = 100 + i
        bars.append([float(ts), float(o), float(h), float(l), float(c), float(v)])
        ts += 60
        price = c
    return bars


def test_get_latest_ohlcv_bars_real_redis() -> None:
    try:
        try:
            from fullon_cache import OHLCVCache  # type: ignore
        except Exception:
            from fullon_cache.ohlcv_cache import OHLCVCache  # type: ignore
    except Exception:
        pytest.skip("fullon_cache not available in environment")

    app = create_app()
    client = TestClient(app)
    _flush_db()

    symbol = f"BTC/{uuid.uuid4().hex[:4]}USDT"
    timeframe = "1m"

    async def _seed() -> None:
        cache = OHLCVCache()
        try:
            start = int(time.time()) - 60 * 50
            bars = _make_bars(start, count=50, base_price=47000.0)
            await cache.update_ohlcv_bars(symbol, timeframe, bars)
        finally:
            await cache._cache.close()

    asyncio.get_event_loop().run_until_complete(_seed())

    with client.websocket_connect("/ws/ohlcv/integration") as ws:
        request = {
            "action": "get_latest_ohlcv_bars",
            "request_id": "req1",
            "params": {"symbol": symbol, "timeframe": timeframe, "count": 20},
        }
        ws.send_text(json.dumps(request))
        response = json.loads(ws.receive_text())

        assert response["success"] is True
        assert response["action"] == "get_latest_ohlcv_bars"
        assert response["result"]["symbol"] == symbol
        assert response["result"]["timeframe"] == timeframe
        assert isinstance(response["result"]["bars"], list)
        assert len(response["result"]["bars"]) == 20


def test_stream_ohlcv_real_redis() -> None:
    try:
        try:
            from fullon_cache import OHLCVCache  # type: ignore
        except Exception:
            from fullon_cache.ohlcv_cache import OHLCVCache  # type: ignore
    except Exception:
        pytest.skip("fullon_cache not available in environment")

    app = create_app()
    client = TestClient(app)
    _flush_db()

    symbol = f"ETH/{uuid.uuid4().hex[:4]}USDT"
    timeframe = "1m"

    async def _seed() -> None:
        cache = OHLCVCache()
        try:
            start = int(time.time()) - 60 * 5
            bars = _make_bars(start, count=5, base_price=3000.0)
            await cache.update_ohlcv_bars(symbol, timeframe, bars)
        finally:
            await cache._cache.close()

    asyncio.get_event_loop().run_until_complete(_seed())

    with client.websocket_connect("/ws/ohlcv/stream_integration") as ws:
        # Start stream
        request = {
            "action": "stream_ohlcv",
            "request_id": "s1",
            "params": {"symbol": symbol, "timeframe": timeframe},
        }
        ws.send_text(json.dumps(request))

        # Expect confirmation
        conf = json.loads(ws.receive_text())
        assert conf["success"] is True
        assert conf["action"] == "stream_ohlcv"

        # Keep this integration test light: only validate stream setup (like trades stream test)
        # Full update assertion is covered in the unit-ish test.
