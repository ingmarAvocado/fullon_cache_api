"""Unit-ish tests for OHLCV handler over WebSocket (real Redis)."""

import asyncio
import json
import time
import uuid

import pytest
from fullon_cache_api.main import create_app
from starlette.testclient import TestClient

pytestmark = [pytest.mark.redis]


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
        ts += 60  # 1-minute spacing
        price = c
    return bars


def test_get_latest_ohlcv_bars_unit_real_redis() -> None:
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
            start = int(time.time()) - 60 * 100
            bars = _make_bars(start, count=50, base_price=47000.0)
            await cache.update_ohlcv_bars(symbol, timeframe, bars)
        finally:
            await cache._cache.close()

    asyncio.get_event_loop().run_until_complete(_seed())

    with client.websocket_connect("/ws/ohlcv/unit") as ws:
        request = {
            "action": "get_latest_ohlcv_bars",
            "request_id": "ohlcv1",
            "params": {"symbol": symbol, "timeframe": timeframe, "count": 10},
        }
        ws.send_text(json.dumps(request))
        response = json.loads(ws.receive_text())

        assert response["success"] is True
        assert response["action"] == "get_latest_ohlcv_bars"
        result = response["result"]
        assert result["symbol"] == symbol
        assert result["timeframe"] == timeframe
        assert isinstance(result["bars"], list)
        assert len(result["bars"]) == 10
        assert all(isinstance(b, list) and len(b) == 6 for b in result["bars"])


def test_get_latest_ohlcv_bars_not_found_unit_real_redis() -> None:
    try:
        try:
            from fullon_cache import OHLCVCache  # type: ignore  # noqa: F401
        except Exception:
            from fullon_cache.ohlcv_cache import (
                OHLCVCache,  # type: ignore  # noqa: F401
            )
    except Exception:
        pytest.skip("fullon_cache not available in environment")

    app = create_app()
    client = TestClient(app)
    _flush_db()

    with client.websocket_connect("/ws/ohlcv/not_found") as ws:
        request = {
            "action": "get_latest_ohlcv_bars",
            "request_id": "nf1",
            "params": {"symbol": "BTC/USDT", "timeframe": "1m", "count": 5},
        }
        ws.send_text(json.dumps(request))
        response = json.loads(ws.receive_text())

        assert response["success"] is False
        assert response["error_code"] in ("OHLCV_NOT_FOUND", "CACHE_MISS")


def test_stream_ohlcv_unit_real_redis() -> None:
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

    async def _seed_initial() -> None:
        cache = OHLCVCache()
        try:
            start = int(time.time()) - 60 * 5
            bars = _make_bars(start, count=5, base_price=3000.0)
            await cache.update_ohlcv_bars(symbol, timeframe, bars)
        finally:
            await cache._cache.close()

    asyncio.get_event_loop().run_until_complete(_seed_initial())

    with client.websocket_connect("/ws/ohlcv/stream_unit") as ws:
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

        # Mutate data to trigger an update
        async def _mutate() -> None:
            cache = OHLCVCache()
            try:
                await asyncio.sleep(0.6)
                # Append one new bar
                start = int(time.time())
                new_bars = _make_bars(start, count=1, base_price=3010.0)
                await cache.update_ohlcv_bars(symbol, timeframe, new_bars)
            finally:
                await cache._cache.close()

        loop = asyncio.get_event_loop()
        task = loop.create_task(_mutate())

        updates: list[dict] = []
        for _ in range(6):
            msg = json.loads(ws.receive_text())
            if msg.get("action") == "ohlcv_update":
                updates.append(msg)
                break

        assert len(updates) >= 1
        # Ensure background mutation task is finalized to avoid warnings
        try:
            loop.run_until_complete(task)
        except Exception:
            pass
        upd = updates[0]["result"]
        assert upd["symbol"] == symbol
        assert upd["timeframe"] == timeframe
        assert isinstance(upd["bar"], list) and len(upd["bar"]) == 6
