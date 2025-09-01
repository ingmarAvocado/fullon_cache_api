"""Unit-ish tests for ticker handler over WebSocket (real Redis)."""

import json
import uuid

import pytest
from starlette.testclient import TestClient

from fullon_cache_api.main import create_app


pytestmark = [pytest.mark.redis]


def _flush_db():
    try:
        from fullon_cache import BaseCache  # type: ignore

        async def _do():
            cache = BaseCache()
            async with cache._redis_context() as redis:
                await redis.flushdb()
            await cache.close()

        import asyncio

        asyncio.get_event_loop().run_until_complete(_do())
    except Exception:
        pass


def test_get_all_tickers_real_redis():
    try:
        from fullon_cache import TickCache  # type: ignore
    except Exception:
        pytest.skip("fullon_cache not available in environment")

    app = create_app()
    client = TestClient(app)
    _flush_db()

    exchange = "binance"
    symbols = [f"BTC/{uuid.uuid4().hex[:4]}USDT", f"ETH/{uuid.uuid4().hex[:4]}USDT"]

    import asyncio

    async def _seed():
        cache = TickCache()
        try:
            for i, s in enumerate(symbols):
                tick = {
                    "symbol": s,
                    "exchange": exchange,
                    "price": 50000.0 - (i * 1000),
                    "volume": 1000 + (i * 10),
                    "time": 1700000000.0 + i,
                    "bid": 10.0,
                    "ask": 20.0,
                    "last": 1.0,
                    "change_24h": 2.5,
                }
                await cache.set_ticker(tick)  # type: ignore[arg-type]
        finally:
            await cache._cache.close()

    asyncio.get_event_loop().run_until_complete(_seed())

    with client.websocket_connect("/ws/tickers/test_all") as ws:
        request = {
            "action": "get_all_tickers",
            "request_id": "all_req",
            "params": {"exchange": exchange},
        }
        ws.send_text(json.dumps(request))
        response = json.loads(ws.receive_text())

        assert response["success"] is True
        assert response["result"]["exchange"] == exchange
        assert isinstance(response["result"]["tickers"], list)
        assert len(response["result"]["tickers"]) >= 2

